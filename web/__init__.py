
from .webwatch_html import Watch_HTML
from .webwatch_api import WebWatch_Tuner


class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils

        self.webwatch_html = Watch_HTML(fhdhr, plugin_utils)
        self.webwatch_api = WebWatch_Tuner(fhdhr, plugin_utils)
