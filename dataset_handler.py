import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import fasttext
from messages import Error
from kivy.clock import Clock
import pickle

class DatasetHandler:

    def read_file(self, path, sep=""):
        if path.endswith('.txt'):
            if sep == ',':
                dataset = pd.read_csv(path, sep=",")
            else:
                with open(path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                # Убираем символы новой строки из каждой строки
                lines = [line.strip() for line in lines]
                # Создаем DataFrame
                dataset = pd.DataFrame(lines)
        elif path.endswith('.xlsx'):
            dataset = pd.read_excel(path)
        else:
            Clock.schedule_once(lambda dt: Error(text="Неподдерживаемое расширение файла").open(), 1)
            return None

        return dataset

    def save_dataframe(self, dataframe, path, file_format='csv'):
        if file_format == 'csv' or file_format == 'txt':
            dataframe.to_csv(path, index=False, header=False)
        elif file_format == 'xlsx': 
            dataframe.to_excel(path, index=False, header=False)
        elif file_format == 'json':
            dataframe.to_json(path, orient='records')
        else:
            Clock.schedule_once(lambda dt: Error(text="Неподдерживаемый формат файла. Поддерживаемые форматы: 'csv', 'xlsx', 'json'").open(), 1)

    def preprocess_text(self, text, flags: dict):
        '''
        Обрабатывает текст к нужному формату
        '''
        text = str(text)
        if flags.get("lower"):
            text = text.lower()
        tokens = word_tokenize(text, language='russian')
        if flags.get("del_stop_words"):
            with open('syst/stopwords.pkl', 'rb') as file:
                stop_words = pickle.load(file)
            tokens = [token for token in tokens if token not in stop_words]
        if flags.get("del_symb"):
            tokens = [re.sub(r'[^А-Яа-яA-Za-z]', '', token) for token in tokens]
        proc_text = " ".join(tokens)
        if flags.get("vect"):
            fasttext_model = fasttext.load_model("./syst/lid.176.ftz")
            proc_text = fasttext_model.get_sentence_vector(proc_text)
        return proc_text
    
    def preprocess_dataset(self, dataset_path, flags: dict):
        result_dataset = self.read_file(dataset_path)
        if result_dataset is None:
            return None
        texts = result_dataset.iloc[:, 0].values
        for idx, text in enumerate(texts, 1):
            proc_text = self.preprocess_text(text, flags)
            result_dataset.loc[idx-1, 0] = proc_text
        return result_dataset
      
    def get_dataset_texts(self, path):
        dataset = self.read_file(path)
        if dataset is None:
            return None
        return dataset.iloc[:, 0].values