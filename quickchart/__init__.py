"""A python client for quickchart.io, a web service that generates static
charts."""

import datetime
import json
import re
try:
    from urllib import urlencode
except:
    # For Python 3
    from urllib.parse import urlencode

USER_AGENT = 'quickchart-python (2.0.0)'

FUNCTION_DELIMITER_RE = re.compile('\"__BEGINFUNCTION__(.*?)__ENDFUNCTION__\"')


class QuickChartFunction:
    def __init__(self, script):
        self.script = script

    def __repr__(self):
        return self.script


def serialize(obj):
    if isinstance(obj, QuickChartFunction):
        return '__BEGINFUNCTION__' + obj.script + '__ENDFUNCTION__'
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj.__dict__


def dump_json(obj):
    ret = json.dumps(obj, default=serialize, separators=(',', ':'))
    ret = FUNCTION_DELIMITER_RE.sub(
        lambda match: json.loads('"' + match.group(1) + '"'), ret)
    return ret


class QuickChart:
    def __init__(self):
        self.config = None
        self.width = 500
        self.height = 300
        self.background_color = '#ffffff'
        self.device_pixel_ratio = 1.0
        self.format = 'png'
        self.version = '2.9.4'
        self.key = None
        self.scheme = 'https'
        self.host = 'quickchart.io'

    def is_valid(self):
        return self.config is not None

    def get_url_base(self):
        return '%s://%s' % (self.scheme, self.host)

    def get_url(self):
        if not self.is_valid():
            raise RuntimeError(
                'You must set the `config` attribute before generating a url')
        params = {
            'c': dump_json(self.config) if type(self.config) == dict else self.config,
            'w': self.width,
            'h': self.height,
            'bkg': self.background_color,
            'devicePixelRatio': self.device_pixel_ratio,
            'f': self.format,
            'v': self.version,
        }
        if self.key:
            params['key'] = self.key
        return '%s/chart?%s' % (self.get_url_base(), urlencode(params))

    def _post(self, url):
        try:
            import requests
        except:
            raise RuntimeError('Could not find `requests` dependency')

        postdata = {
            'chart': dump_json(self.config) if type(self.config) == dict else self.config,
            'width': self.width,
            'height': self.height,
            'backgroundColor': self.background_color,
            'devicePixelRatio': self.device_pixel_ratio,
            'format': self.format,
            'version': self.version,
        }
        if self.key:
            postdata['key'] = self.key
        headers = {
            'user-agent': USER_AGENT,
        }
        resp = requests.post(url, json=postdata, headers=headers)
        if resp.status_code != 200:
            err_description = resp.headers.get('x-quickchart-error')
            raise RuntimeError(
                'Invalid response code from chart creation endpoint: %d%s'
                % (resp.status_code, '\n%s' % err_description if err_description else '')
            )
        return resp


    def get_short_url(self):
        resp = self._post('%s/chart/create' % self.get_url_base())
        parsed = json.loads(resp.text)
        if not parsed['success']:
            raise RuntimeError(
                'Chart creation endpoint failed to create chart')
        return parsed['url']

    def get_bytes(self):
        resp = self._post('%s/chart' % self.get_url_base())
        return resp.content

    def to_file(self, path):
        content = self.get_bytes()
        with open(path, 'wb') as f:
            f.write(content)
