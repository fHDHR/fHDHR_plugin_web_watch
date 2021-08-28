from flask import Response, request, redirect, abort, session
import urllib.parse

from fHDHR.exceptions import TunerError


class WebWatch_Tuner():
    endpoints = ["/api/webwatch"]
    endpoint_name = "api_webwatch"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        stream_method = "webwatch"

        base_url = request.url_root[:-1]

        tuner_number = request.args.get('tuner', default=None, type=str)

        client_address = request.remote_addr

        accessed_url = request.args.get('accessed', default=request.url, type=str)

        method = request.args.get('method', default="stream", type=str)

        redirect_url = request.args.get('redirect', default=None, type=str)

        origin_methods = self.fhdhr.origins.valid_origins
        origin = request.args.get('origin', default=None, type=str)
        if origin and origin not in origin_methods:
            return "%s Invalid channels origin" % origin

        if method == "stream":

            channel_number = request.args.get('channel', None, type=str)
            if not channel_number:
                return "Missing Channel"

            if origin:

                if str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number", origin)]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("number", channel_number, origin)
                    if not chan_obj:
                        response = Response("Not Found", status=404)
                        response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                        self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                        abort(response)
                elif str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id", origin)]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("id", channel_number, origin)
                    if not chan_obj:
                        response = Response("Not Found", status=404)
                        response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                        self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                        abort(response)
                else:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

            else:

                if str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id")]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("id", channel_number)
                    if not chan_obj:
                        response = Response("Not Found", status=404)
                        response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                        self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                        abort(response)
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

            duration = request.args.get('duration', default=0, type=int)

            transcode_quality = request.args.get('transcode', default=None, type=str)
            valid_transcode_types = [None, "heavy", "mobile", "internet720", "internet480", "internet360", "internet240"]
            if transcode_quality not in valid_transcode_types:
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = "802 - Unknown Transcode Profile"
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                abort(response)

            stream_args = {
                            "channel": channel_number,
                            "origin": origin,
                            "method": stream_method,
                            "duration": duration,
                            "origin_quality": self.fhdhr.config.dict["streaming"]["origin_quality"],
                            "transcode_quality": transcode_quality or self.fhdhr.config.dict["streaming"]["transcode_quality"],
                            "accessed": accessed_url,
                            "base_url": base_url,
                            "client": client_address,
                            "client_id": session["session_id"]
                            }

            if stream_method == "passthrough":
                try:
                    stream_args = self.fhdhr.device.tuners.get_stream_info(stream_args)
                except TunerError as e:
                    self.fhdhr.logger.info("A %s stream request for %s channel %s was rejected due to %s"
                                           % (origin, stream_args["method"], str(stream_args["channel"]), str(e)))
                    response = Response("Service Unavailable", status=503)
                    response.headers["X-fHDHR-Error"] = str(e)
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)
                self.fhdhr.logger.info("Passthrough method selected, no tuner will be used. Redirecting Client to %s" % stream_args["stream_info"]["url"])
                return redirect(stream_args["stream_info"]["url"])

            try:
                if not tuner_number:
                    tunernum = self.fhdhr.device.tuners.first_available(origin, channel_number)
                else:
                    tunernum = self.fhdhr.device.tuners.tuner_grab(tuner_number, origin, channel_number)
            except TunerError as e:
                self.fhdhr.logger.info("A %s stream request for channel %s was rejected due to %s"
                                       % (stream_args["method"], str(stream_args["channel"]), str(e)))
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str(e)
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                abort(response)

            tuner = self.fhdhr.device.tuners.tuners[origin][str(tunernum)]

            try:
                stream_args = self.fhdhr.device.tuners.get_stream_info(stream_args)
            except TunerError as e:
                self.fhdhr.logger.info("A %s stream request for %s channel %s was rejected due to %s"
                                       % (origin, stream_args["method"], str(stream_args["channel"]), str(e)))
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str(e)
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                tuner.close()
                abort(response)

            self.fhdhr.logger.info("%s Tuner #%s to be used for stream." % (origin, tunernum))
            tuner.set_status(stream_args)
            session["tuner_used"] = tunernum

            try:
                tuner.setup_stream(stream_args, tuner)
            except TunerError as e:
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str(e)
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                tuner.close()
                abort(response)

            return Response(tuner.stream.get())

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
