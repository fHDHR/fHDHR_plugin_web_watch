from flask import request, render_template_string, session, abort, Response
import pathlib
from io import StringIO


class Watch_HTML():
    endpoints = ["/webwatch"]
    endpoint_name = "page_webwatch_html"
    endpoint_access_level = 0

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr

        self.template_file = pathlib.Path(plugin_utils.path).joinpath('webwatch.html')
        self.template = StringIO()
        self.template.write(open(self.template_file).read())

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        watch_url = None

        origin_methods = self.fhdhr.origins.list_origins
        if self.fhdhr.origins.count_origins:

            channel_number = request.args.get('channel', None, type=str)
            if not channel_number:
                return "Missing Channel"

            origin = request.args.get('origin', default=origin_methods[0], type=str)

            if origin:

                if str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number", origin)]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("number", channel_number, origin)
                elif str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id", origin)]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("id", channel_number, origin)
                else:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

            else:

                if str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id")]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("id", channel_number)
                else:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

            if not chan_obj.dict["enabled"]:
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str("806 - Tune Failed")
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                abort(response)

            origin = chan_obj.origin
            channel_number = chan_obj.number
            channel_id = chan_obj.dict["id"]

            watch_url = '/api/webwatch?method=stream&channel=%s&origin=%s' % (channel_id, origin)

            whatson = self.fhdhr.device.epg.whats_on_now(chan_obj.number, origin, chan_obj=chan_obj)

            channel_list = []

            channel_list.append({
                                "epg_method": chan_obj.origin,
                                "number": chan_obj.number,
                                "name": chan_obj.dict["name"],
                                "chan_thumbnail": chan_obj.thumbnail,
                                "listing_title": whatson["listing"][0]["title"],
                                "listing_thumbnail": whatson["listing"][0]["thumbnail"],
                                "listing_description": whatson["listing"][0]["description"]
                                })

            for epg_method in self.fhdhr.device.epg.valid_epg_methods:
                epg_chan_matches = self.fhdhr.db.get_fhdhr_value("epg_channels", "list", epg_method) or {}
                epg_id = [x for x in list(epg_chan_matches.keys()) if epg_chan_matches[x]["fhdhr_id"] == chan_obj.dict["id"]]
                if len(epg_id):
                    whatson_all = self.fhdhr.device.epg.whats_on_allchans(epg_method)
                    whatson = [whatson_all[x] for x in list(whatson_all.keys()) if whatson_all[x]["id"] == epg_id[0]]
                    if len(whatson):
                        channel_list.append({
                                            "epg_method": epg_method,
                                            "number": chan_obj.number,
                                            "name": chan_obj.dict["name"],
                                            "chan_thumbnail": chan_obj.thumbnail,
                                            "listing_title": whatson[0]["listing"][0]["title"],
                                            "listing_thumbnail": whatson[0]["listing"][0]["thumbnail"],
                                            "listing_description": whatson[0]["listing"][0]["description"]
                                            })

        return render_template_string(self.template.getvalue(), request=request, session=session, fhdhr=self.fhdhr, watch_url=watch_url, channel_list=channel_list)
