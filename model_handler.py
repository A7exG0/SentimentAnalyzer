import fasttext
import os 

class Model:
    
    def __init__(self, model_path):
        self.model = self.upload_model(model_path)

    def upload_model(self, path):
        if os.path.exists(path):
            return fasttext.load_model(path)
        else:
            return None
    def get_prediction(self, text):
        return self.model.predict(text)