from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTrailingCheckbox
import os
from messages import Message

class DialogListItem(MDListItem):
    name = StringProperty()
    is_choosed = BooleanProperty(False)

class ChoosingDialog(MDDialog): 
    files_folder = StringProperty()
    file_name = StringProperty("")
    is_complete = BooleanProperty(False)
    _items_list = ListProperty()

    def __init__(self, **kwargs):
        ''' 
        В параметре files_folder необходимо указать папку с файлами для выбора.
        '''
        super().__init__(**kwargs)
        pathes = os.listdir(self.files_folder)

        for path in pathes:
            item = DialogListItem(name=os.path.basename(path))
            self._items_list.append(item)
            self.ids.container.add_widget(item)      

    def _save_file_name(self):
        for item in self._items_list:
            if item.is_choosed:
                self.file_name = item.name
                self.is_complete = True
                self.dismiss()
                return 
        Message(text="Вы не выбрали модель").open()
