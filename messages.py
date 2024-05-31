from kivymd.uix.snackbar import MDSnackbar
from kivy.properties import StringProperty

class Error(MDSnackbar):
    text = StringProperty()
    
class Message(MDSnackbar):
    text = StringProperty()
    