from dataset_handler import DatasetHandler
import matplotlib.pyplot as plt
from kivy.clock import Clock
import threading
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ObjectProperty
import pandas as pd
from kivy.metrics import dp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.scrollview import *
import os
from kivymd.uix.list import *
from kivymd.uix.screen import MDScreen
from model_handler import Model

from kivy.animation import Animation
from kivymd.uix.expansionpanel import MDExpansionPanel
from kivymd.uix.behaviors import RotateBehavior
from kivymd.uix.list import MDListItemTrailingIcon
from kivy.uix.behaviors import ButtonBehavior
import logging
from choosing_dialog import ChoosingDialog
import pyperclip 
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText, MDSnackbarSupportingText
import json 
from datetime import datetime
import shutil
from messages import Message, Error

TEST_DATASET_PATH = "syst/TEST_DATA.txt"

class ExpansionPanelItem(MDExpansionPanel, DatasetHandler):
    name = StringProperty("-")
    dataset_name = StringProperty("-")
    model_name = StringProperty("-")
    accuracy = StringProperty("-")
    is_diagram = BooleanProperty(False)
    sentiment_path_disabled = BooleanProperty(True)
    mistakes_path_disabled = BooleanProperty(True)
    fig_path = StringProperty("")
    sentiment_path = StringProperty("")
    mistakes_path = StringProperty("")
    result_dataset = ObjectProperty(None)
    fig = ObjectProperty(None)
    mistakes_dataset = ObjectProperty(None)

    def finish_panel(self): #TODO Изменить возможность сохранения в разных форматах 
        dir_path = "./results/"+self.name
        if os.path.exists(dir_path): # если такое уже есть, то заменяем последний символ
            dir_path = dir_path[:-1] + str((int(dir_path[-1]) + 1) % 10) 
        os.makedirs(dir_path)
        if self.result_dataset is not None:
            self.sentiment_path = os.path.abspath(dir_path + "/Classified dataset.xlsx")
            self.save_dataframe(self.result_dataset, self.sentiment_path, 'xlsx')
        if self.fig is not None:
            fig_path = dir_path + '/Sentiment distribution.png'
            self.fig.savefig(fig_path)
            self.fig_path = fig_path
        if self.mistakes_dataset is not None:
            self.mistakes_path = os.path.abspath(dir_path + "/Testing mistakes.xlsx")
            self.save_dataframe(self.mistakes_dataset, self.mistakes_path, 'xlsx')   
        
        saving_data = {
            "accuracy": self.accuracy,
            "dataset_name": self.dataset_name,
            "model_name": self.model_name,
            "sentiment_path_disabled": self.sentiment_path_disabled,
            "mistakes_path_disabled": self.mistakes_path_disabled,
            "sentiment_path": self.sentiment_path,
            "mistakes_path": self.mistakes_path,
            "is_diagram": self.is_diagram,
            "diagram_path": self.fig_path,
        }
        with open(dir_path + "/parameters.json", "w") as file:
            json.dump(saving_data, file)
        

    def copy_path(self, path):
        pyperclip.copy(path)
        MDSnackbar(
            MDSnackbarText(
                text="Путь скопирован:",
            ),
            MDSnackbarSupportingText(
                text=path,
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
        ).open()

    def remove_expansion_panel(self):
        self.parent.remove_widget(self)
        if os.path.exists("./results/"+self.name):
            shutil.rmtree("./results/"+self.name)
        else: 
            Error(text="Проблема с файловой системой. Перезапустите приложение.").open()

class TrailingPressedIconButton(
    ButtonBehavior, RotateBehavior, MDListItemTrailingIcon
):
    def open_chevron(self, panel: MDExpansionPanel):
        if panel._content.parent:
            panel._content.parent.remove_widget(panel._content)
        
        Animation(
            padding=[0, dp(12), 0, dp(12)] if not panel.is_open else [0, 0, 0, 0],
            d=0.2,
        ).start(panel)
        
        if not panel.is_open:
            panel.open()
        else:
            panel.close()
        
        if not panel.is_open:
            panel.set_chevron_down(self)
        else:
            panel.set_chevron_up(self)


class ProgressLine(MDDialog):
    text = StringProperty()
    progress = NumericProperty(0)
    method = ObjectProperty()
    stop_flag = BooleanProperty(False)

    def on_open(self):
        thread_one = threading.Thread(target=self.method, args=(self, ))#args=(self,)+self.args)
        thread_one.start()

        def _update(dt):  
            if self.stop_flag:
                self.dismiss()
                thread_one.join()
                Clock.unschedule(_update) 

            if self.progress == 100:
                self.dismiss()
                Clock.unschedule(_update) 

        Clock.schedule_interval(_update, 0.01)
            
    def stop(self):
        self.stop_flag = True

class Results(MDScreen, DatasetHandler):
    ''' 
    Данный класс является реализацией окна вкладки результаты. Наследует от класса  
    DatasetHandler необходимые функции для работы с датасетами. 
    '''
    dataset_path = StringProperty("")
    model_path = StringProperty("")
    progress = NumericProperty(0)
    _number_prop = NumericProperty(0)
    _index = NumericProperty(0)
    adding_panel: ExpansionPanelItem = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.load_panels, 0.1)

    def load_panels(self, dt):
        ''' 
        Загрузка сохраненных панелей с результатами из файла
        '''
        for folder, _, files in os.walk("./results"):
            if folder == "./results":
                continue
            
            if not os.path.exists(folder + "/parameters.json"): 
                shutil.rmtree(folder)
                continue

            with open(folder + "/parameters.json", "r") as file:
                panel_data = json.load(file)

            panel = ExpansionPanelItem(
                name=os.path.basename(folder),
                dataset_name=panel_data.get("dataset_name"),
                model_name=panel_data.get("model_name"),
                accuracy=panel_data.get("accuracy"),
                sentiment_path_disabled=panel_data.get("sentiment_path_disabled"),
                mistakes_path_disabled=panel_data.get("mistakes_path_disabled"),
                sentiment_path=panel_data.get("sentiment_path"),
                mistakes_path=panel_data.get("mistakes_path"),
                is_diagram=panel_data.get("is_diagram"),
                fig_path=panel_data.get("diagram_path")
            )
            panel.ids.diagram.height =dp(500) if panel.is_diagram else dp(0)
            self.ids.container.add_widget(panel, self._index)
            self._index+=1
            
    
    def _active_checbox(self, item):
        '''
        Добавление функционала в зависимости от выбранных чекбоксов
        '''
        if item.active == True:
            self._number_prop += 1
            if item == self.ids.classification_checkbox:
                self.ids.diagram.disabled = False
        else:
            self._number_prop -= 1
            if item == self.ids.classification_checkbox:
                self.ids.diagram_checkbox.active = False
                self.ids.diagram.disabled = True

        if self._number_prop == 0:
            self.ids.result_button.disabled = True
        else:
            self.ids.result_button.disabled = False

    def set_file_name(self, dialog, attribute_name, label_id):
        '''
        По завершению диалога выбора модели или датасета, сохраняет выбранное имя.
        '''
        if dialog.is_complete:
            setattr(self, attribute_name, dialog.file_name)
            card = getattr(self.ids, label_id)
            card.text = dialog.file_name
            if attribute_name == "model_name":
                self.model_path = "./models/" + dialog.file_name
                self.model = Model(self.model_path)
                if self.model is None:
                    Error(text="Необходимой модели не сущетсвует").open()
                self.ids.accuracy.disabled = False
                self.ids.saving_mistakes.disabled = False
            else:
                self.dataset_path = "./data/" + dialog.file_name
            if self.model_path != "" and self.dataset_path != "":
                self.ids.classification.disabled = False 

    def show_dialog(self, folder, attribute_name, label_id):
        '''
        Открывает диалог для выбора модели или датасета в зависимости от параметров
        '''
        dialog = ChoosingDialog(files_folder=folder)
        dialog.bind(on_pre_dismiss=lambda instance: self.set_file_name(dialog, attribute_name, label_id))
        dialog.open()

    def show_model_dialog(self):
        '''
        Открывает диалоговое окно для выбора модели
        '''
        self.show_dialog("./models", "model_name", "model_text")

    def show_dataset_dialog(self):
        '''
        Открывает диалоговое окно для выбора датасета
        '''
        self.show_dialog("./data", "dataset_name", "dataset_text")

    def get_current_time(self):
        '''
        Получает текущую дату и время. 
        Необходима для создания панели с результатами.
        '''
        current_datetime = datetime.now()
        current_datetime_str = current_datetime.strftime("%Y-%m-%d %H.%M.%S")
        return current_datetime_str

    def add_expansion_panel(self, panel):
        '''
        Добавляет панель с результатами. 
        '''
        panel.finish_panel()
        self.ids.container.add_widget(panel, self._index)
        self._index+=1

    def _generate_diagram(self, sentiment_counts):
        '''
        Создает диаграмму соотношения количества позитивных, негативных и нейтральных текстов
        '''
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.INFO)
        
        sizes = [sentiment_counts["positive"], sentiment_counts["negative"], sentiment_counts["netral"]]
        labels = ['Positive', 'Negative', 'Neutral']
        colors = ['green', 'red', 'gray']
        
        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title('Соотношение')
        
        self.adding_panel.is_diagram = True
        self.adding_panel.fig = plt

    def _count_sentiment(self, line):
        '''
        Метод, который классифицирует тексты и создает диаграмму соотношения, если были
        выбраны необходимые параметры.
        '''
        texts = self.get_dataset_texts(self.dataset_path)
        total_texts = len(texts)
        
        sentiment_counts = {"negative": 0, "netral": 0, "positive": 0}
        result_dataset = pd.DataFrame({'text': texts, 'value': [None] * total_texts})
        
        for idx, text in enumerate(texts, 1):
            if line.stop_flag:
                return
            
            line.progress = idx / total_texts * 100
            try:
                tuple_result  = self.model.get_prediction(text)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: Error(text=str(e) + f"\nСтрока:{idx-1}\nТекст:{text}").open(), 1)
                continue
                
            prediction = tuple_result[0][0].replace("__label__", "")
            result_dataset.loc[idx-1, 'value'] = prediction
            
            if self.ids.diagram_checkbox.active:
                sentiment_counts[prediction] += 1

        self.adding_panel.result_dataset = result_dataset
        self.adding_panel.sentiment_path_disabled = False
        
        if self.ids.diagram_checkbox.active:
            Clock.schedule_once(lambda dt: self._generate_diagram(sentiment_counts))

        if not self.ids.saving_mistakes_checkbox.active and not self.ids.accuracy_checkbox.active:
            Clock.schedule_once(lambda dt: self.add_expansion_panel(self.adding_panel), 0.1)


    def _estimate_model(self, line):
        '''
        Анализирует модель: вычисляет ее точность и, если были выбранны необходимые параметры, 
        сохраняет ошибки модели в тестах.
        '''
        mistakes_dataset = pd.DataFrame(columns=['text', 'value', 'predicted'])
        dataset = self.read_file(TEST_DATASET_PATH, sep=',') 
        total = len(dataset)
        correct_predictions = 0

        for i, (text, value) in enumerate(zip(dataset['text'], dataset['value']), 1):
            if line.stop_flag:
                return

            try:
                tuple_result  = self.model.get_prediction(text)
            except Exception:
                continue

            prediction = tuple_result[0][0].replace("__label__", "")

            if prediction == value:
                correct_predictions += 1
            elif self.ids.saving_mistakes_checkbox.active:
                mistake = {'text': text, 'value': value, 'predicted': prediction}
                mistakes_dataset = mistakes_dataset._append(mistake, ignore_index=True)

            line.progress = i / total * 100

        if self.ids.saving_mistakes_checkbox.active:
            self.adding_panel.mistakes_dataset = mistakes_dataset
            self.adding_panel.mistakes_path_disabled = False

        if self.ids.accuracy_checkbox.active:
            accuracy = correct_predictions / total * 100
            self.adding_panel.accuracy = str(round(accuracy, 2))
        
        Clock.schedule_once(lambda dt: self.add_expansion_panel(self.adding_panel), 0.1)


    def get_result(self):
        '''
        Вызывается при нажатии кнопки "Получить результаты" и запускает функционал, который 
        выбрал пользователь.
        '''
        self.adding_panel = ExpansionPanelItem(name = self.get_current_time())
        if self.dataset_path != "":
            if os.path.exists(self.dataset_path):
                self.adding_panel.dataset_name =os.path.basename(self.dataset_path) 
            else:
                Error(text="Выбранного датасета не существует").open()
                return
        if self.model_path != "":
            if os.path.exists(self.model_path):
                self.adding_panel.model_name = os.path.basename(self.model_path)
            else:
                Error(text="Выбранной модели не существует").open()
                return

        if self.ids.diagram_checkbox.active == True:
            self.adding_panel.ids.diagram.height = dp(500)
        else:
            self.adding_panel.ids.diagram.height = dp(0)

        if self.ids.classification_checkbox.active:
            line = ProgressLine(text="Получение результатов", method=self._count_sentiment)
            line.bind(on_dismiss = lambda instance: self.on_dismiss(line))
            line.open()
        else:
            ProgressLine(text="Оценка модели", method=self._estimate_model).open()

    def on_dismiss(self, line):
        '''
        Запускает функионал оценки модели, после классификации текстов, если пользователь выбрал необходимые параметры
        '''
        if not line.stop_flag and (self.ids.accuracy_checkbox.active or self.ids.saving_mistakes_checkbox.active):
            ProgressLine(text="Оценка модели", method=self._estimate_model).open()


