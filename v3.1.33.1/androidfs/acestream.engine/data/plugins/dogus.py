#-plugin-sig:VS0h76V+qIFbbdLhSom+eLz3WUJ9zsI91MEnFpdjN9Rz8YdGKhxxeuJ3eyS2zw5/2P0nu3wDcR/I2wfnsoY1nSU2SpwKcXhRTMzMmtcEhKgAxas3ZyPJl27MWEbj1DKgba+iYyrHfRUFOzGEvMr6wVxkjCrUEN0JIAzlWBtZFo6ZLe6iyfLGm+seQ0Yrg2keG9/XbqqSp2eP9SLhDptKK+WDUDSaqI8PsvLgI5l8aUj3B5sXsEX3RK6J6raXnFfLF27dkwLgNlmVvtnETmraQhULiEU51vV27ohoPOIcK6rkbSZB8tho0YOmPkHE5zusuKdw2LER5NO1vhoTGVI9Gw==
from __future__ import print_function

import re

from ACEStream.PluginsContainer.livestreamer.plugin import Plugin
from ACEStream.PluginsContainer.livestreamer.plugin.api import http
from ACEStream.PluginsContainer.livestreamer.plugin.api import validate
from ACEStream.PluginsContainer.livestreamer.stream import HDSStream
from ACEStream.PluginsContainer.livestreamer.stream import HLSStream


class Dogus(Plugin):
    """
    Support for live streams from Dogus sites include startv, ntv, ntvspor, and kralmuzik
    """

    url_re = re.compile(r"""https?://(?:www.)?
        (?:
            startv.com.tr/canli-yayin|
            ntv.com.tr/canli-yayin/ntv|
            ntvspor.net/canli-yayin|
            kralmuzik.com.tr/tv/kral-tv|
            kralmuzik.com.tr/tv/kral-pop-tv
        )/?""", re.VERBOSE)
    mobile_url_re = re.compile(r"""(?P<q>[\"'])(?P<url>https?://[^'"]*?/live/hls/[^'"]*?\?token=)
                                   (?P<token>[^'"]*?)(?P=q)""", re.VERBOSE)
    desktop_url_re = re.compile(r"""(?P<q>[\"'])(?P<url>https?://[^'"]*?/live/hds/[^'"]*?\?token=)
                                    (?P<token>[^'"]*?)(?P=q)""", re.VERBOSE)
    token_re = re.compile(r"""token=(?P<q>[\"'])(?P<token>[^'"]*?)(?P=q)""")

    hds_schema = validate.Schema(validate.all(
        {
            "success": True,
            "xtra": {
                "url": validate.url(),
                "use_akamai": bool
            }
        },
        validate.get("xtra")
    ))
    SWF_URL = "http://dygassets.akamaized.net/player2/plugins/flowplayer/flowplayer.httpstreaming-3.2.11.swf"

    @classmethod
    def can_handle_url(cls, url):
        return cls.url_re.match(url) is not None

    def _get_star_streams(self, desktop_url, mobile_url, token=""):
        if token:
            self.logger.debug("Opening stream with token: {}", token)

        if mobile_url:
            for _, s in HLSStream.parse_variant_playlist(self.session,
                                                         mobile_url + token,
                                                         headers={"Referer": self.url}).items():
                yield "live", s
        if desktop_url:
            # get the HDS stream URL
            res = http.get(desktop_url + token)
            stream_data = http.json(res, schema=self.hds_schema)
            for _, s in HDSStream.parse_manifest(self.session,
                                                 stream_data["url"],
                                                 pvswf=self.SWF_URL,
                                                 is_akamai=stream_data["use_akamai"],
                                                 headers={"Referer": self.url}).items():
                yield "live", s

    def _get_streams(self):
        res = http.get(self.url)
        mobile_url_m = self.mobile_url_re.search(res.text)
        desktop_url_m = self.desktop_url_re.search(res.text)


        desktop_url = desktop_url_m and desktop_url_m.group("url")
        mobile_url = mobile_url_m and mobile_url_m.group("url")

        token = (desktop_url_m and desktop_url_m.group("token")) or (mobile_url_m and mobile_url_m.group("token"))
        if not token:
            # if no token is in the url, try to find it else where in the page
            token_m = self.token_re.search(res.text)
            token = token_m and token_m.group("token")

        return self._get_star_streams(desktop_url, mobile_url, token=token)


__plugin__ = Dogus
