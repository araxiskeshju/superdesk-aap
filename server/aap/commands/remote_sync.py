# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

"""Superdesk"""

from eve.utils import config
import superdesk
from superdesk import get_resource_service, json_utils
from superdesk.metadata.packages import LINKED_IN_PACKAGES
from superdesk.metadata.item import ITEM_STATE, CONTENT_STATE
import requests
from requests.auth import HTTPBasicAuth
import json
import logging

logger = logging.getLogger(__name__)


class RemoteSyncCommand(superdesk.Command):
    """Command that will pull the published content from a remote instance of Superdesk.
    """

    option_list = [
        superdesk.Option('--remote', '-rmt', dest='remote', required=True),
        superdesk.Option('--username', '-usr', dest='username', required=True),
        superdesk.Option('--password', '-pwd', dest='password', required=True),
        superdesk.Option('--desk', '-desk', dest='desk', required=False)
    ]

    headers = {"Content-type": "application/json;charset=UTF-8", "Accept": "application/json"}

    token = None
    url = None

    def _login_to_remote(self, remote, username, password):
        """
        Log into the API of the remote instance of superdesk and save the token for future requests
        :param remote:
        :param username:
        :param password:
        :return:
        """
        try:
            post_data = {'username': username, 'password': password}
            response = requests.post('{}/{}'.format(remote, 'auth_db'), json=post_data, verify=False,
                                     headers=self.headers)
            if int(response.status_code) // 100 == 2:
                content = json_utils.loads(response.content.decode('UTF-8'))
                self.token = content.get('token')
                return True
            else:
                print('Login to remote superdesk API failed with response status code: {}'.format(response.status_code))
                return False
        except Exception as ex:
            print('Login to remote superdesk API failed with exception: {}'.format(ex))
            logger.exception('Login to remote superdesk API failed with exception.')

    def _get_remote_published_items(self, desk):
        """
        Query the remote instance of superdesk for published items and process each of them
        :return:
        """
        try:
            from_count = 0
            while True:
                # The query excludes spiked items and returns only text items that are the last published version
                query = {"query": {
                    "filtered": {
                        "filter": {"and": [{"term": {"last_published_version": True}}, {"term": {"type": "text"}}]}}},
                    "sort": [{"publish_sequence_no": "asc"}], "size": 100, "from": from_count}
                # If a desk has been passed we filter on that as well
                if desk:
                    query.get('query').get('filtered').get('filter').get('and').append({"term": {"task.desk": desk}})
                params = {'repo': 'published', 'source': json.dumps(query)}
                response = requests.get('{}/{}'.format(self.url, 'search'), auth=HTTPBasicAuth(self.token, None),
                                        params=params, verify=False)
                content = json_utils.loads(response.content.decode('UTF-8'))
                if len(content['_items']) == 0:
                    break
                for item in content['_items']:
                    try:
                        self._process_item(item['archive_item'])
                    except Exception as ex:
                        print('Exception processing {}'.format(ex))
                        logger.exception('Exception processing.')
                from_count += 100
        except Exception as ex:
            print('Exception getting remote published items: {}', ex)
            logger.exception('Exception getting remote published items.')

    def _get_remote_package(self, id):
        """
        Given the id of a package retrieve it from the remote instance of superdesk
        :param id:
        :return:
        """
        response = requests.get('{}/{}/{}'.format(self.url, 'archive', id), auth=HTTPBasicAuth(self.token, None),
                                verify=False)
        return json.loads(response.content.decode('UTF-8'))

    def _inject_item(self, item):
        """
        Inject the passed item into the local database and publish it.
        :param item:
        :return:
        """
        item.pop(LINKED_IN_PACKAGES, None)
        get_resource_service('archive').post([item])
        get_resource_service('archive_publish').patch(id=item[config.ID_FIELD],
                                                      updates={ITEM_STATE: CONTENT_STATE.PUBLISHED,
                                                               'auto_publish': True})

    def _process_item(self, item):
        """
        Process an item that has been retrieved from the remote instance of Superdesk
        :param item:
        :return:
        """
        if '_id' in item:
            print("\n\n\n\nProcessing {} headline:[{}] slugline:[{}] takekey:[{} state:{}]".format(item['_id'],
                                                                                                   item.get('headline',
                                                                                                            ''),
                                                                                                   item.get('slugline',
                                                                                                            ''),
                                                                                                   item.get(
                                                                                                       'anpa_take_key',
                                                                                                       ''),
                                                                                                   item.get('state',
                                                                                                            '')))
            if 'rewritten_by' in item:
                print('Item has been rewritten so ignoring it')
                return

            if item['state'] != 'published':
                print('State:  {}  id: {}'.format(item.get('state', ''), item.get('_id', '')))

            if (item.get('state', '')) == 'killed':
                print("Item has been killed, ignoring it")
                return

            fields_to_remove = ('unique_name', 'unique_id', 'takes', '_etag', '_type', '_current_version', '_updated')
            for field in fields_to_remove:
                item.pop(field, None)
            item['state'] = 'in_progress'
            item['_current_version'] = 1

            service = get_resource_service('archive')

            local_item = service.find_one(req=None, _id=item.get('_id'))
            if local_item is None:
                print("Injecting item {}".format(item.get('_id', '')))
                self._inject_item(item)
            else:
                print("Already Imported")
        else:
            print("No Associated archive_item {}".format(item))

    def run(self, remote, username, password, desk=None):
        self.url = remote
        if self._login_to_remote(remote, username, password):
            self._get_remote_published_items(desk)


superdesk.command('app:remote_sync', RemoteSyncCommand())
