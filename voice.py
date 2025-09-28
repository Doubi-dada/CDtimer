import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 160)  # 调整语速

def speak(text):
    engine.say(text)
    engine.runAndWait()
