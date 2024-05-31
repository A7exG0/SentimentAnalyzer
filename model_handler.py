import fasttext
from kivy.properties import StringProperty, ObjectProperty

class Model:
    
    def __init__(self, model_path):
        self.model = self.upload_model(model_path)

    def upload_model(self, path):
        return fasttext.load_model(path)

    def get_prediction(self, text):
        return self.model.predict(text)