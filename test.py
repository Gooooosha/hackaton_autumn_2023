import speech_recognition as sr
recognizer = sr.Recognizer()
audio_file_path = "audio.ogg"
with sr.AudioFile(audio_file_path) as source:
    try:
        audio_data = recognizer.record(source)
        recognized_text = recognizer.recognize_google(audio_data, language="ru-RU")
        print("Распознанный текст: " + recognized_text)
    except sr.UnknownValueError:
        print("Речь не распознана")
    except sr.RequestError as e:
        print("Ошибка запроса к Google Web Speech API; {0}".format(e))