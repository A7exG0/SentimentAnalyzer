import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import fasttext
from messages import Error
from kivy.clock import Clock

nltk.download('stopwords')
fs = fasttext.load_model("./syst/lid.176.ftz")

class DatasetHandler:
    
    def __init__(self):
        self.__fasttext_model = fs

    def read_file(self, path):
        """
        Считывает файл в зависимости от его расширения.
        Args:
            path: строка, путь к файлу.
        Returns:
            pandas DataFrame: прочитанный DataFrame.
        """
        if path.endswith('.txt'):
            dataset = pd.read_csv(path, sep=',') 
        elif path.endswith('.xlsx'):
            dataset = pd.read_excel(path)
        else:
            Clock.schedule_once(lambda dt: Error(text="Неподдерживаемое расширение файла").open(), 1)

        return dataset

    def save_dataframe(self, dataframe, path, file_format='csv'):
        """
        Сохраняет DataFrame в файл указанного формата.
        Args:
            dataframe: pandas DataFrame, который нужно сохранить.
            filename: строка, имя файла, в который нужно сохранить DataFrame.
            file_format: строка, формат файла ('csv', 'xlsx', 'json', и т.д.). По умолчанию 'csv'.
        """
        if file_format == 'csv' or file_format == 'txt':
            dataframe.to_csv(path, index=False)
        elif file_format == 'xlsx': 
            dataframe.to_excel(path, index=False)
        elif file_format == 'json':
            dataframe.to_json(path, orient='records')
        else:
            Clock.schedule_once(lambda dt: Error(text="Неподдерживаемый формат файла. Поддерживаемые форматы: 'csv', 'xlsx', 'json'").open(), 1)

    def preprocess_text(self, text, flags: dict):
        '''
        Обрабатывает текст к нужному формату
        '''
        if flags.get("lower"):
            text = text.lower()
        tokens = word_tokenize(text, language='russian')
        if flags.get("del_stop_words"):
            stop_words = set(stopwords.words('russian'))
            tokens = [token for token in tokens if token not in stop_words]
        if flags.get("del_symb"):
            tokens = [re.sub(r'[^А-Яа-яA-Za-z]', '', token) for token in tokens]
        proc_text = " ".join(tokens)
        if flags.get("vect"):
            proc_text = self.__fasttext_model.get_sentence_vector(proc_text)
        return proc_text
    
    def preprocess_dataset(self, dataset_path, flags: dict):
        result_dataset = self.read_file(dataset_path)
        texts = result_dataset.iloc[:, 0].values
        for idx, text in enumerate(texts, 1):
            proc_text = self.preprocess_text(text, flags)
            result_dataset.loc[idx-1, 'text'] = proc_text
        return result_dataset
      
    def get_dataset_texts(self, path):
        dataset = self.read_file(path)
        return dataset.iloc[:, 0].values


    # if idx %1000 == 0:
    #     print(idx)

    #! Изменить функцию под эту штуку
    # def preprocess_dataset(self, dataset_path, flags: dict):
    #     result_dataset = self.read_file(dataset_path)
    #     texts = result_dataset.iloc[:, 0].values
    #     # total_texts = len(texts)
    #     for idx, text in enumerate(texts, 1):
    #         # if line.stop_flag:
    #         #     return
    #         # line.progress = idx / total_texts * 100
    #         proc_text = self.preprocess_text(text, flags)
    #         result_dataset.loc[idx-1, 'text'] = proc_text
    #         if idx %1000 == 0:
    #             print(idx)

    #     return result_dataset

    def train_test_split(df, train_size):
        if not 0 < train_size < 1:
            raise ValueError("train_size должен быть числом в диапазоне от 0 до 1")
        
        train_size = int(df.shape[0] * train_size)
        train_df = df.iloc[:train_size]
        test_df = df.iloc[train_size:]
        return train_df, test_df

    def change_values(self, dataset):
        #TODO добавить возмножность выбора меток
        values = dataset['value']
        new_dataset = dataset.copy()
        new_dataset['value'] = new_dataset['value'].astype(str)
        for i in range(len(new_dataset)):
            value = new_dataset['value'][i]
            if value == '-2' or value == '-1':
                new_dataset.loc[i, 'value'] = "negative"
            elif value == '0':
                new_dataset.loc[i, 'value'] = "neutral"
            elif value == '1' or value == '2':
                new_dataset.loc[i, 'value'] = "positive"
            if i % 1000 == 0: 
                print(i)