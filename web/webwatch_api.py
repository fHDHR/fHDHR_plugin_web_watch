from flask import request, redirect
import urllib.parse


class WebWatch_Tuner():
    endpoints = ["/api/webwatch"]
    endpoint_name = "api_webwatch"
    endpoint_methods = ["GET", "POST"]

    """
    This is a redeirect to the fHRHR_web core api/tuners
    """

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        accessed_url = urllib.parse.quote(request.url)

        tuner_number = request.args.get('tuner', default=None, type=str)

        duration = request.args.get('duration', default=0, type=int)
        transcode_quality = request.args.get('transcode', default=None, type=str)

        origin_methods = self.fhdhr.origins.valid_origins
        origin = request.args.get('origin', default=None, type=str)
        if origin and origin not in origin_methods:
            return "%s Invalid channels origin" % origin

        channel_number = request.args.get('channel', None, type=str)
        if not channel_number:
            return "Missing Channel"

        redirect_url = self.get_tuner_api_url(channel_number, origin, duration, transcode_quality, accessed_url, tuner_number)
        return redirect(redirect_url)

    def get_tuner_api_url(self, channel_number, origin, duration, transcode_quality, accessed_url, tuner_number=None):

        redirect_url = "/api/tuners?method=stream"

        if tuner_number:
            redirect_url += "&tuner=%s" % (tuner_number)

        redirect_url += "&channel=%s" % channel_number
        redirect_url += "&origin=%s" % origin
        redirect_url += "&stream_method=webwatch"

        if duration:
            redirect_url += "&duration=%s" % duration

        if transcode_quality:
            redirect_url += "&transcode=%s" % transcode_quality

        redirect_url += "&accessed=%s" % accessed_url

        return redirect_url
