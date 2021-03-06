Feature: Mission Report
    Background: Initial Setup:
        Given the "vocabularies"
        """
        [{"_id": "categories", "items": [
            {"name": "National", "qcode": "a", "is_active": true},
            {"name": "Advisories", "qcode": "v", "is_active": true},
            {"name": "Racing (Turf)", "qcode": "r", "is_active": true},
            {"name": "FormGuide", "qcode": "h", "is_active": true}
        ]}, {"_id": "genre", "items": [
            {"name": "Article (news)", "qcode": "Article"},
            {"name": "Results (sport)", "qcode": "Results (sport)"}
        ]}]
        """
        And "desks"
        """
        [{
            "_id": "5b501a501d41c84c0bfced4a",
            "name": "Sports Desk",
            "members": [{"user": "#CONTEXT_USER_ID#"}]
        }]
        """
        And "stages"
        """
        [
            {
                "_id": "5b501a511d41c84c0bfced4b", "desk": "5b501a501d41c84c0bfced4a",
                "name": "stage1", "is_visible": true
            },
            {
                "_id": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a",
                "name": "stage2", "is_visible": true
            }
        ]
        """
        Given "published"
        """
        [
            {
                "_id": "archive1", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a511d41c84c0bfced4b", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "a"}], "state": "published"
            },
            {
                "_id": "archive2", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "published"
            }
        ]
        """

    @auth
    Scenario: Generate the Mission report
        When we get "/mission_report?params={"query": {"filtered": {}}}"
        Then we get list with 1 items
        """
        {"_items": [{
            "corrections": [],
            "kills": [],
            "takedowns": [],
            "rewrites": [],
            "new_stories": {
                "categories": {
                    "a": 1,
                    "v": 1
                },
                "count": 2
            },
            "total_stories": 2
        }]}
        """

    @auth
    Scenario: Include corrections, kills, takedowns and rewrites
        Given "published"
        """
        [
            {
                "_id": "archive1", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a511d41c84c0bfced4b", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "a"}], "state": "published"
            },
            {
                "_id": "archive2", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "published"
            },
            {
                "_id": "archive3", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "published", "rewrite_of": "archive1"
            },
            {
                "_id": "archive4", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "corrected"
            },
            {
                "_id": "archive5", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "killed"
            },
            {
                "_id": "archive6", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "recalled"
            }
        ]
        """
        When we get "/mission_report?params={"query": {"filtered": {}}}"
        Then we get list with 1 items
        """
        {"_items": [{
            "corrections": [{
                "_id": "archive4", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "corrected"
            }],
            "kills": [{
                "_id": "archive5", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "killed"
            }],
            "takedowns": [{
                "_id": "archive6", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "recalled"
            }],
            "rewrites": [{
                "_id": "archive3", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}],
                "state": "published", "rewrite_of": "archive1"
            }],
            "new_stories": {
                "categories": {
                    "a": 1,
                    "v": 1
                },
                "count": 2
            },
            "total_stories": 6
        }]}
        """

    @auth
    Scenario: Calculates count for results, fields, comment and betting
        Given "published"
        """
        [
            {
                "_id": "archive1", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a511d41c84c0bfced4b", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "a"}], "state": "published"
            },
            {
                "_id": "archive2", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "published"
            },
            {
                "_id": "archive3", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "r"}], "state": "published"
            },
            {
                "_id": "archive4", "_type": "published", "source": "AP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "r"}], "state": "published"
            },
            {
                "_id": "archive5", "_type": "published", "source": "BRA",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "r"}], "state": "published"
            },
            {
                "_id": "archive6", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "r"}], "state": "published",
                "genre": [{"qcode": "Results (sport)"}]
            }
        ]
        """
        When we get "/mission_report?params={"query": {"filtered": {}}}"
        Then we get list with 1 items
        """
        {"_items": [{
            "corrections": [],
            "kills": [],
            "takedowns": [],
            "rewrites": [],
            "new_stories": {
                "categories": {
                    "a": 1,
                    "h": 0,
                    "r": 2,
                    "results": 2,
                    "v": 1
                },
                "count": 6
            },
            "total_stories": 6
        }]}
        """

    @auth
    @wip
    Scenario: Receive results as hicharts configs
        Given "published"
        """
        [
            {
                "_id": "archive1", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a511d41c84c0bfced4b", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "a"}], "state": "published"
            },
            {
                "_id": "archive2", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "published"
            },
            {
                "_id": "archive3", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "published", "rewrite_of": "archive1"
            },
            {
                "_id": "archive4", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "corrected"
            },
            {
                "_id": "archive5", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "killed"
            },
            {
                "_id": "archive6", "_type": "published", "source": "AAP",
                "task": {"stage": "5b501a6f1d41c84c0bfced4c", "desk": "5b501a501d41c84c0bfced4a"},
                "anpa_category": [{"qcode": "v"}], "state": "recalled"
            }
        ]
        """
        When we get "/mission_report?params={"query": {"filtered": {}}}&return_type=highcharts_config"
        Then we get 6 charts
        """
        [{
            "chart": {
                "height": 300,
                "type": "line"
            },
            "series": [{"data": [6, 0, 2, 1, 1, 1, 1]}],
            "title": {"text": "Mission Report: Summary(6)"},
            "type": "line",
            "xAxis": {"categories": [
                "Total Stories",
                "Results/Fields/Comment/Betting",
                "New Stories",
                "Updates",
                "Corrections",
                "Kills",
                "Takedowns"
            ]},
            "yAxis": {"title": {"text": "STORIES TRANSMITTED"}}
        }, {
            "type": "bar",
            "title": {"text": "New Stories By Category"},
            "series": [{"data": [1, 0, 0, 0, 1]}],
            "xAxis": {
                "categories": [
                    "National (A)",
                    "FormGuide (H)",
                    "Racing (Turf) (R)",
                    "Results/Fields/Comment/Betting",
                    "Advisories (V)"
                ],
                "title": {"text": "CATEGORY"}
            },
            "yAxis": {"title": {"text": "STORIES TRANSMITTED"}}
        }, {
            "type": "table",
            "title": "There were 1 corrections issued",
            "headers": ["Sent", "Slugline", "TakeKey", "Ednote"]
        }, {
            "type": "table",
            "title": "There were 1 kills issued",
            "headers": ["Sent", "Slugline", "TakeKey", "Ednote"]
        }, {
            "type": "table",
            "title": "There were 1 takedowns issued",
            "headers": ["Sent", "Slugline", "TakeKey", "Ednote"]
        }, {
            "type": "table",
            "title": "There were 1 updates issued",
            "headers": ["Sent", "Slugline", "TakeKey", "Ednote"]
        }]
        """
