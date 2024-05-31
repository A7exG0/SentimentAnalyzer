from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.scrollview import *
import os
from kivymd.uix.list import *
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivymd.uix.navigationrail import MDNavigationRailItem

from results_screen import Results
from files_screen import Files


class CommonNavigationRailItem(MDNavigationRailItem):
    text = StringProperty()
    icon = StringProperty()

    def on_active(self, instance, is_choosed):
        if is_choosed:
            app = MDApp.get_running_app()
            app.change_workspace(app._screens[self.text])

class SentimentAnalyzer(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._screens = {}
        self.create_directory_if_not_exists("./models")
        self.create_directory_if_not_exists("./data")
    
    def create_directory_if_not_exists(self, dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    def change_workspace(self, new_workspace_name):
        self.root.remove_widget(self.root.ids.workspace)
        self.root.add_widget(new_workspace_name)
        self.root.ids.workspace = new_workspace_name

    def on_start(self):
        results = Results()
        datasets = Files(dir_name ="data", ext=['.txt', '.xlsx'])
        models = Files(dir_name ="models", ext=['.pkl', '.h5', '.joblib', '.pb', '.onnx', '.pth', '.pklz', '.gz', '.pt'])
        self._screens['Результаты'] = results
        self._screens['Датасеты'] = datasets
        self._screens['Модели'] = models
        self.change_workspace(results)

    def build(self):
        # if self.is_windows(): 
        from kivy.config import Config 
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.minimum_width = 800
        Window.minimum_height = 600
        screen = Builder.load_file('main.kv')
        return screen 

    # def is_windows(self):
    #     return platform.system() == 'Windows'

SentimentAnalyzer().run()
