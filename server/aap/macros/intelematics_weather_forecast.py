# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import logging
from superdesk.cache import cache
from flask import current_app as app
import requests
import xml.etree.ElementTree as et
from lxml import etree
from flask import render_template_string
from superdesk.utils import config
from superdesk import get_resource_service


logger = logging.getLogger(__name__)

# This is a list of the names of the forecast locations that we are interested in
met_forecast_areas = {'NSW': ['Sydney', 'Parramatta', 'Campbelltown', 'Penrith', 'Wollongong', 'Newcastle'],
                      'QLD': ['Brisbane', 'Gold Coast Seaway', 'Cairns', 'Gladstone', 'Mount Isa'],
                      'VIC': ['Melbourne', 'Phillip Island', 'Geelong', 'Ballarat', 'Wilsons Promontory'],
                      'SA': ['Adelaide', 'Whyalla', 'Coober Pedy', 'Port Augusta', 'Mount Gambier'],
                      'WA': ['Perth', 'Margaret River', 'Geraldton', 'Broome', 'Kalgoorlie']}

# This is a list of the names ov the available observation stations
met_observation_stations = {'NSW': ['Sydney - Observatory Hill', 'Sydney Olympic Park', 'Parramatta', 'Campbelltown',
                                    'Penrith', 'Albion Park', 'Newcastle University'],
                            'QLD': ['Brisbane', 'Gold Coast Seaway', 'Cairns', 'Gladstone', 'Mount Isa'],
                            'VIC': ['Melbourne', 'Rhyll', 'Geelong Racecourse', 'Ballarat', 'Wilsons Promontory'],
                            'SA': ['Adelaide', 'Whyalla', 'Coober Pedy Airport', 'Port Augusta', 'Mount Gambier'],
                            'WA': ['Perth', 'Witchcliffe', 'Geraldton Airport', 'Broome', 'Kalgoorlie-Boulder']}

NS = {'sd': 'http://www.sunatraffic.com.au'}


@cache(ttl=600)
def _get_urls():
    resp = dict()
    url = 'http://dataservices.sunatraffic.com.au/SunaDataServices'
    payload = {'key': app.config.get('INTELEMATICS_WEATHER_API_KEY', '')}
    response = requests.get(url, params=payload)
    response.raise_for_status()
    utf8_parser = etree.XMLParser(encoding='utf-8')
    xml = et.fromstring(response.content, parser=utf8_parser)
    for s in xml.findall('.//sd:toc/sd:dataSummary', namespaces=NS):
        type = s.find('sd:dataType', namespaces=NS).text
        url = s.find('sd:url', namespaces=NS).text
        resp[type] = url
    return resp


@cache(ttl=600)
def _get_forecast(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content.decode('utf-8')


def forecast_story(item, **kwargs):
    def add_value(period, dict, name, base):
        try:
            node = period.find('sd:{}'.format(name), namespaces=NS)
            if node is not None:
                dict['{}{}'.format(base, name).replace('-', '_')] = node.text
        except Exception as ex:
            pass

    # The place is used to determine the state the the requests will be limited to
    if 'place' in item and len(item.get('place')):
        state = item.get('place')[0].get('qcode').upper()
    else:
        return

    links = _get_urls()
    forecast_xml = _get_forecast(links.get('weather forecast'))

    forecast_dict = dict()
    xml = et.fromstring(forecast_xml)
    s = xml.find('.//sd:forecast/sd:state/[@name="{}"]'.format(state), namespaces=NS)
    if s is not None:
        for area in met_forecast_areas.get(state):
            location = s.find('.//sd:location[sd:name="{}"]'.format(area), namespaces=NS)
            if location is not None:
                location_name = location.find('sd:name', namespaces=NS).text
                for period in location.findall('sd:period', namespaces=NS):
                    index = period.attrib.get('index')
                    base_str = '{}_{}_'.format(location_name.replace(' ', '_'), index)

                    forecast_dict['{}start'.format(base_str)] = period.attrib.get('start')
                    forecast_dict['{}end'.format(base_str)] = period.attrib.get('end')

                    add_value(period, forecast_dict, 'precis', base_str)
                    add_value(period, forecast_dict, 'min-temperature', base_str)
                    add_value(period, forecast_dict, 'max-temperature', base_str)
                    add_value(period, forecast_dict, 'chance-of-rain', base_str)
                    add_value(period, forecast_dict, 'amount-of-rain', base_str)
                    add_value(period, forecast_dict, 'icon', base_str)

    current_xml = _get_forecast(links.get('current weather'))
    xml = et.fromstring(current_xml)
    s = xml.find('.//sd:observations/sd:state/[@name="{}"]'.format(state), namespaces=NS)
    if s is not None:
        for station in met_observation_stations.get(state):
            observation = s.find('sd:observation[sd:loc_name="{}"]'.format(station), namespaces=NS)
            if observation is not None:
                location_name = observation.find('sd:loc_name', namespaces=NS).text
                base_str = '{}_obs_'.format(location_name.replace(' ', '_'))
                add_value(observation, forecast_dict, 'time', base_str)
                add_value(observation, forecast_dict, 'temperature', base_str)
                add_value(observation, forecast_dict, 'app_temperature', base_str)
                add_value(observation, forecast_dict, 'humidity', base_str)
                add_value(observation, forecast_dict, 'wind-speed', base_str)
                add_value(observation, forecast_dict, 'wind-dir', base_str)
                add_value(observation, forecast_dict, 'visibility', base_str)

    # for i, (k, v) in enumerate(forecast_dict.items()):
    #     print('{} {} : {} ---> {{{{{}}}}}'.format(i, k, v, k))
    #     print(k)

    item['body_html'] = render_template_string(item.get('body_html', ''), **forecast_dict)

    update = {'source': 'Intelematics'}
    ingest_provider = get_resource_service('ingest_providers').find_one(req=None, source='Intelematics')
    if ingest_provider:
        update['ingest_provider'] = ingest_provider.get(config.ID_FIELD)
    update['body_html'] = item['body_html']
    get_resource_service('archive').system_update(item[config.ID_FIELD], update, item)
    item['source'] = 'Intelematics'

    return item


name = 'weather forecast'
label = 'Weather Forecast/Observations'
callback = forecast_story
access_type = 'frontend'
action_type = 'direct'
