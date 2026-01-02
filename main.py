import json
import time
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.speedtest: speedtest.Speedtest = None
        self.image_state = "idle"


    def init_speedtest(self) -> None:
        try:
            self.speedtest = speedtest.Speedtest(secure=True)
        except (speedtest.ConfigRetrievalError, speedtest.SpeedtestBestServerFailure) as e:
            log.error(e)
            self.show_error()
            self.set_bottom_label(None)
            self.image_state = "error"

    def on_ready(self):
        self.set_media(media_path=os .path.join(self.plugin_base.PATH, "assets", "speed.png"), size=0.8, valign=-1, update=True)
        self.set_bottom_label("Start")

    def on_key_down(self):
        if self.image_state in ["idle", "showing"]:
            self.image_state = "running"
            self.set_media(image=None, update=True)
            self.set_top_label(None)
            self.set_center_label("Testing...", font_size=12)
            self.set_bottom_label(None)
            try:
                self.perform_test()
            except Exception as e:
                log.error(e)
                self.show_error(1)
        elif self.image_state in ["running", "error"]:
            return

    def on_key_hold(self):
        """
        Clears the top, center, and bottom labels and restores the speed.png image.
        """
        self.set_top_label(None)
        self.set_center_label(None)
        self.set_bottom_label("Start")
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "speed.png"), size=0.8, valign=-1, update=True)


    def event_callback(self, event, data=None):
        if event == Input.Key.Events.SHORT_UP:
            self.on_key_down()
        elif event == Input.Key.Events.HOLD_START:
            self.on_key_hold()

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

        self.image_state = "showing"
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
            action_id_suffix="Speedtest",
            action_name=self.lm.get("actions.speedtest.name"),
            icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "speed.png")),
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.UNSUPPORTED
            }
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
