import json
import time
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

import sys
import os
from PIL import Image
from loguru import logger as log
import requests

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))

# Import globals
import globals as gl

# Import own modules
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page

import speedtest

class Speedtest(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.speedtest: speedtest.Speedtest = None
        self.state = "idle"


    def init_speedtest(self) -> None:
        try:
            self.speedtest = speedtest.Speedtest(secure=True)
        except (speedtest.ConfigRetrievalError, speedtest.SpeedtestBestServerFailure) as e:
            log.error(e)
            self.show_error()
            self.set_bottom_label(None)
            self.state = "error"
        
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "speed.png"), size=0.8, valign=-1, update=False)
        self.set_bottom_label("Start")

    def on_key_down(self):
        if self.state in ["idle", "showing"]:
            self.state = "running"
            self.set_media(image=None, update=True)
            self.set_top_label(None)
            self.set_center_label("Testing...", font_size=12)
            self.set_bottom_label(None)
            self.perform_test()
        elif self.state in ["running", "error"]:
            return


    def perform_test(self):
        self.init_speedtest()
        self.speedtest.get_best_server()
        download = round(self.speedtest.download()/1000000)
        upload = round(self.speedtest.upload()/1000000)
        ping = round(self.speedtest.results.ping)

        if self.page is not self.deck_controller.active_page:
            # Page has changed while test was running
            return

        self.set_top_label(f"Ping: {ping} ms", font_size=11, update=False)
        self.set_center_label(f"{download} Mbps", font_size=12, update=False)
        self.set_bottom_label(f"{upload} Mbps", font_size=12)

        self.state = "showing"
        self.speedtest = None
        self.init_speedtest()


class SpeedTestPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.init_locale_manager()

        self.lm = self.locale_manager

        ## Register actions
        self.speedtest_holder = ActionHolder(
            plugin_base=self,
            action_base=Speedtest,
            action_id="com_core447_Speedtest::Speedtest",
            action_name=self.lm.get("actions.speedtest.name"),
            icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "speed.png"))
        )
        self.add_action_holder(self.speedtest_holder)


        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/StreamController/Speedtest",
            plugin_version="1.0.0",
            app_version="1.0.0-alpha"
        )

    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

    def get_selector_icon(self) -> Gtk.Widget:
        return Gtk.Image(file=os.path.join(self.PATH, "assets", "speed.png"))
        # return Gtk.Image.new_from_filename(os.path.join(self.PATH, "assets", "speed.png"))
        return Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "speed.png"))