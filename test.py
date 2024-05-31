
from nltk.corpus import stopwords
import nltk
import pickle

# Убедитесь, что стоп-слова загружены
# nltk.download('stopwords')
nltk.download('punkt')
print("!")
# Получение списка стоп-слов
stop_words = set(stopwords.words('russian'))

# Сохранение списка в файл
with open('stopwords.pkl', 'wb') as file:
    pickle.dump(stop_words, file)

# import pickle

# # Загрузка списка из файла
# with open('stopwords.pkl', 'rb') as file:
#     stop_words = pickle.load(file)

# # Использование загруженного списка
# print(stop_words)