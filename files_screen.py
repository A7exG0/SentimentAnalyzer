from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
import os
import shutil
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.appbar import MDTopAppBar
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivymd.uix.menu import MDDropdownMenu
import sys
from dataset_handler import DatasetHandler
from messages import Message, Error
    
def get_os():
    if sys.platform.startswith('win'):
        return 'Windows'
    elif sys.platform.startswith('darwin'):
        return 'macOS'
    elif sys.platform.startswith('linux'):
        return 'Linux'
    else: 
        return 'unknown'

class CheckItem(MDBoxLayout):
    text = StringProperty()
    active = BooleanProperty(False)

    def on_active(self, checkbox, value):
        self.active = value 

class PreprocessDialog(MDDialog):
    name = StringProperty()
    dir_name = StringProperty()
    new_name = StringProperty()
    extension = StringProperty()
    is_complete = BooleanProperty(False)
    low_check = BooleanProperty()
    del_symb_check = BooleanProperty()
    del_words_check = BooleanProperty()
    vect_check = BooleanProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.new_name, self.extension = self.set_default_name()

    def set_default_name(self):
        name, extension = os.path.splitext(self.name)
        i = 1
        while True: 
            full_name = name + str(i) + extension
            if os.path.exists(f"./{self.dir_name}/{full_name}"):
                i+=1
            else:
                return name + str(i), extension

    def close_dialog(self):
        input_name = self.ids.new_name.text
        full_name = input_name + self.extension
        if os.path.exists(f"./{self.dir_name}/{full_name}"):
            Message(text="Датасет с таким именем уже существует").open()
            return 
        self.low_check = self.ids.low_check.active
        self.del_symb_check = self.ids.del_symb_check.active
        self.del_words_check = self.ids.del_words_check.active
        self.vect_check = self.ids.vect_check.active
        if self.low_check == self.del_symb_check == self.del_words_check == self.ids.vect_check.active == False:
            Message(text="Не выбран ни один параметр").open()
            return 
        self.is_complete = True 
        self.new_name = input_name
        self.dismiss()

class ModelItem(MDTopAppBar):
    name = StringProperty()
    dir_name = StringProperty()

    def _remove_file(self):
        self.parent.remove_widget(self)
        os.remove(f"./{self.dir_name}/"+ self.name)


class DatasetItem(MDTopAppBar, DatasetHandler):
    name = StringProperty()
    dir_name = StringProperty()
    _menu: MDDropdownMenu = None
    _preproc_dialog: PreprocessDialog = None

    def _remove_file(self):
        self.parent.remove_widget(self)
        os.remove(f"./{self.dir_name}/"+ self.name)

    def _open_menu(self, menu_button):
        menu_items = []
        for item, method in {
            "Открыть": lambda: self.open_file(),
            "Предобработка": lambda: self._preprocess_dialog_open(),
        }.items():
            menu_items.append(
                {
                    "text": item,
                    "on_release": method,
                }
            )
        self.menu = MDDropdownMenu(
            caller=menu_button,
            items=menu_items,
        )
        self.menu.open()

    def _preprocess_dialog_open(self):
        preproc_dialog = PreprocessDialog(name = self.name, dir_name = self.dir_name)
        preproc_dialog.bind(on_pre_dismiss=lambda instance: self._on_pre_dismiss(preproc_dialog))
        preproc_dialog.open()

    def _on_pre_dismiss(self, dialog):
        if dialog.is_complete is False:
            return
        flags = {"lower": dialog.low_check, "del_symb": dialog.del_symb_check, "del_stop_words": dialog.del_words_check, "vect": dialog.vect_check}
        
        new_dataset = self.preprocess_dataset(f"./{self.dir_name}/{self.name}", flags)
        path = f"./data/{dialog.new_name + dialog.extension}"
        self.save_dataframe(new_dataset, path, dialog.extension[1:]) # delete "."
        new_item = DatasetItem(name=os.path.basename(path), dir_name = self.dir_name)
        self.parent.add_widget(new_item)
        
    def open_file(self):
        syst = get_os()
        if syst == "Windows":
            os.system(f"start ./{self.dir_name}/{self.name}")
        elif syst == "macOS":
            os.system(f"open ./{self.dir_name}/{self.name}")
        elif syst == "Linux":
            os.system(f"xdg-open ./{self.dir_name}/{self.name}")
        else:
            Error("Операционная система не соответствует требованиям").open()


class FileManager(MDFileManager):
    ext = ListProperty()
    file_pathes_list = ListProperty()
    selected_pathes = ListProperty()
        
    def select_path(self, path: str, *args):
        if os.path.basename(path) in self.file_pathes_list:
            Message(text="Файл с таким именем уже существует").open()
            return
        if path in self.selected_pathes:
            self.selected_pathes.remove(path)
            Message(text="Файл убран:" + path).open()
        else:
            self.selected_pathes.append(path)
            Message(text="Выбран файл:" + path).open()
        
    def exit_manager(self, *args):
        self.close()
    
    def open(self):
        self.selected_pathes = [] 
        self.show(os.getcwd())

class FileDialog(MDDialog):
    is_complete = BooleanProperty(False)
    _file_manager: FileManager = None
    ext = ListProperty()
    file_pathes_list = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)        
        self._file_manager = FileManager(file_pathes_list=self.file_pathes_list, ext=self.ext)

    def get_selected_pathes(self):
        return self._file_manager.selected_pathes

    def accept_close(self):
        pathes = self._file_manager.selected_pathes
        if pathes != [] :
            self.is_complete = True
            self.dismiss()
        else:
            Message(text="Вы не выбрали ни одного файла").open()


class Files(MDScreen):
    dir_name = StringProperty()
    ext = ListProperty()
    file_pathes_list = ListProperty()
    file_dialog: FileDialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.dir_name == "models":
            self._add_builted_model() 
        self.file_pathes_list = self.load_saves(self.dir_name)
    
    def _open_choosing_dialog(self):
        self.file_dialog = FileDialog(file_pathes_list=self.file_pathes_list, ext=self.ext)
        self.file_dialog.bind(on_pre_dismiss=lambda instance: self.save_file())
        self.file_dialog.open()

    def _add_builted_model(self):
        shutil.copy("./syst/built-in model.bin", "./models")

    def add_file(self, path, folder_name):
        if folder_name == "data":
            newItem = DatasetItem(name=os.path.basename(path), dir_name = self.dir_name)
        else:
            newItem = ModelItem(name=os.path.basename(path), dir_name = self.dir_name)
            if newItem.name == "built-in model.bin":
                newItem.disabled = True
        self.ids.appbar.add_widget(newItem)
    
    def load_saves(self, folder_name):
        folder_path = f"./{folder_name}"
        pathes = os.listdir(folder_path)
        for path in pathes:
            self.add_file(os.path.join(folder_path, path), folder_name)
        return pathes 
    
    def add_file_item(self, selected_pathes):
        for path in selected_pathes:
            self.file_pathes_list.append(os.path.basename(path))
            shutil.copy(path, "./" + self.dir_name)
            self.add_file(path, self.dir_name)

    def save_file(self): 
        if self.file_dialog.is_complete:
            pathes = self.file_dialog.get_selected_pathes()
            self.add_file_item(pathes)

    def __del__(self):
        if os.path.exists("./models/built-in model.bin"):
            os.remove("./models/built-in model.bin")

