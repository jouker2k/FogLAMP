# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

"""Unit test for foglamp.plugins.south.http_south.http_south"""

import json
import pytest
import asyncio
from unittest import mock
from unittest.mock import patch
from aiohttp.test_utils import make_mocked_request
from aiohttp.streams import StreamReader
from multidict import CIMultiDict

from foglamp.plugins.south.http_south.http_south import HttpSouthIngest
from foglamp.plugins.south.coap_listen.coap_listen import Ingest


__author__ = "Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


def mock_request(data, loop):
    payload = StreamReader(loop=loop)
    payload.feed_data(data.encode())
    payload.feed_eof()

    protocol = mock.Mock()
    app = mock.Mock()
    headers = CIMultiDict([('CONTENT-TYPE', 'application/json')])
    req = make_mocked_request('POST', '/sensor-reading', headers=headers,
                              protocol=protocol, payload=payload, app=app)
    return req


@pytest.allure.feature("unit")
@pytest.allure.story("plugin", "south", "http")
class TestHttpSouthIngest(object):
    """Unit tests foglamp.plugins.south.http_south.http_south.HttpSouthIngest
    """

    @pytest.mark.asyncio
    async def test_post_sensor_reading_ok(self, event_loop):
        data = """{
            "timestamp": "2017-01-02T01:02:03.23232Z-05:00",
            "asset": "sensor1",
            "key": "80a43623-ebe5-40d6-8d80-3f892da9b3b4",
            "readings": {
                "velocity": "500",
                "temperature": {
                    "value": "32",
                    "unit": "kelvin"
                }
            }
        }"""

        async def mock_coro():
            return ""

        with patch.object(Ingest, 'add_readings', return_value=mock_coro()):
            with patch.object(Ingest, 'is_available', return_value=True):
                request = mock_request(data, event_loop)
                r = await HttpSouthIngest.render_post(request)
                retval = json.loads(r.body.decode())
                # Assert the POST request response
                assert 200 == retval['status']
                assert 'success' == retval['result']

    async def test_post_sensor_reading_missing_delimiter(self, event_loop):
        data = """{
            "timestamp": "2017-01-02T01:02:03.23232Z-05:00",
            "asset": "sensor1",
            "key": "80a43623-ebe5-40d6-8d80-3f892da9b3b4",
            "readings": {
                "velocity": "500",
                "temperature": {
                    "value": "32",
                    "unit": "kelvin"
                }
        }"""
        with patch.object(Ingest, 'is_available', return_value=True):
            request = mock_request(data, event_loop)
            r = await HttpSouthIngest.render_post(request)
            retval = json.loads(r.body.decode())
            # Assert the POST request response
            assert 400 == retval['status']
            assert retval['error'].startswith("Expecting ',' delimiter:")

    async def test_post_sensor_reading_not_dict(self, event_loop):
        data = """{
            "timestamp": "2017-01-02T01:02:03.23232Z-05:00",
            "asset": "sensor2",
            "key": "80a43623-ebe5-40d6-8d80-3f892da9b3b4",
            "readings": "500"
        }"""

        with patch.object(Ingest, 'is_available', return_value=True):
            request = mock_request(data, event_loop)
            r = await HttpSouthIngest.render_post(request)
            retval = json.loads(r.body.decode())
            # Assert the POST request response
            assert 400 == retval['status']
            assert "readings must be a dictionary" == retval['error']