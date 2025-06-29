import datetime, os, webbrowser, random, json, pickle, psutil
import pyttsx3, pyautogui, numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

with open("intents.json") as f:
    INTENTS = json.load(f)

MODEL     = load_model("chat_model.h5")
TOKENIZER = pickle.load(open("tokenizer.pkl", "rb"))
LABEL_ENC = pickle.load(open("label_encoder.pkl", "rb"))
MAX_LEN   = 20

_tts = None
def speak(txt: str):
    """Server-side TTS: only for local runs."""
    global _tts
    if _tts is None:
        _tts = pyttsx3.init("sapi5")
        for v in _tts.getProperty("voices"):
            if "female" in v.name.lower():
                _tts.setProperty("voice", v.id); break
        else:
            _tts.setProperty("voice", _tts.getProperty("voices")[1].id)
        _tts.setProperty("rate", 150)
        _tts.setProperty("volume", 1.0)
    _tts.say(txt); _tts.runAndWait()

def greet() -> str:
    now   = datetime.datetime.now()
    day   = now.strftime("%A")
    clock = now.strftime("%I:%M %p")
    if   now.hour < 12: return f"Good morning! Sir It’s {day}, {clock}."
    elif now.hour < 17: return f"Good afternoon! Sir It’s {day}, {clock}."
    return f"Good evening! Sir It’s {day}, {clock}."

def _open(url, msg):  webbrowser.open(url); return msg
def _app(path, name): os.startfile(path);   return f"Opening {name}"
def _kill(exe, name): os.system(f"taskkill /f /im {exe}"); return f"Closing {name}"

WEEK = {
    "monday": "from 9:00 am to 9:50 am you have Python class in Cr 201, from 10:00 am to 11:00 am you have machine learning class in Cr 405",
    "tuesday": "from 8:00 am to 10:00 am you have D S A class in Lt 201, from 2:00 pm to 2:50 pm you have DAA in Cr 402",
    "wednesday": "from 2:10 pm to 4:00 pm you have machine learning class in Lt 301",
    "thursday": "from 8:00 am to 9:50 am you have Python class in Cr 301, from 1:00 pm to 1:50 pm you have Deep Learning class in Cr 405",
    "friday": "from 3:00 pm to 5:00 am you have D S A class in Lt 401",
    "saturday": "from 9:00 am to 9:50 am you have Python class, from 10:00 am to 11:00 am you have machine learning class",
    "sunday": "Today is Holiday"
}

def _predict_tag(text: str) -> str:
    seq = TOKENIZER.texts_to_sequences([text])
    pad = pad_sequences(seq, maxlen=MAX_LEN, truncating="post")
    return LABEL_ENC.inverse_transform([np.argmax(MODEL.predict(pad, verbose=0))])[0]


_genai_model = None
def get_genai_model():
    global _genai_model
    if _genai_model is None:
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            _genai_model = genai.GenerativeModel("gemini-1.5-flash")
            print("Loaded Gemini 1.5 Flash model successfully")
        except Exception as e:
            print(f"Failed to load Gemini model: {e}")
            return None
    return _genai_model

def reply(user_text: str) -> str:
    """
    Decide Friday’s response text and perform any side-effects
    (opening apps, web pages, changing volume, etc.).
    """
    low = user_text.lower()

    if any(site in low for site in ("facebook","whatsapp","discord","instagram")):
        if "facebook"  in low: return _open("https://www.facebook.com", "Opening Facebook")
        if "whatsapp"  in low: return _open("https://web.whatsapp.com", "Opening WhatsApp")
        if "discord"   in low: return _open("https://discord.com",       "Opening Discord")
        if "instagram" in low: return _open("https://www.instagram.com","Opening Instagram")

    if "open calculator" in low:  return _app(r"C:\Windows\System32\calc.exe",    "Calculator")
    if "open VS code" in low: return _app(r"C:\Windows\System32\Code.exe","VS Code")
    if "open notepad"    in low:  return _app(r"C:\Windows\System32\notepad.exe", "Notepad")
    if "open paint"      in low:  return _app(r"C:\Windows\System32\mspaint.exe", "Paint")

    if "close calculator" in low: return _kill("calc.exe",    "Calculator")
    if "close notepad"    in low: return _kill("notepad.exe", "Notepad")
    if "close paint"      in low: return _kill("mspaint.exe", "Paint")

    if "volume up" in low or "increase volume" in low:
        pyautogui.press("volumeup");   return "Volume increased 🔊"
    if "volume down" in low or "decrease volume" in low:
        pyautogui.press("volumedown"); return "Volume decreased 🔉"
    if "mute" in low:
        pyautogui.press("volumemute"); return "Volume muted 🔇"

    if "schedule" in low or "time table" in low:
        today = datetime.datetime.today().strftime("%A").lower()
        return f"Sir Your schedule for today is: {WEEK[today]}"

    if "system condition" in low or "condition of the system" in low:
        cpu  = psutil.cpu_percent()
        batt = psutil.sensors_battery().percent
        return f"CPU usage {cpu}% • Battery {batt}%."

    if "search" in low and "youtube" in low:
        search_term = low.split("search", 1)[1].replace("on youtube", "").strip()
        if search_term:
            return _open(f"https://www.youtube.com/results?search_query={search_term}",
                         f"Searching YouTube for “{search_term}”")
        return "What do you want to search on YouTube?"

    if "search" in low and "google" in low:
        search_term = low.split("search", 1)[1].replace("on google", "").strip()
        if search_term:
            return _open(f"https://www.google.com/search?q={search_term}",
                         f"Searching Google for “{search_term}”")
        return "What do you want to search on Google?"

   
    model = get_genai_model()
    if model is None:
        return "Sorry, I couldn’t load the Gemini model. Please check your API key and internet connection."

    try:
    
        if any(x in low for x in ("write an application", "write a letter","write an email","write a mail","application","letter","email")):
            if any(x in low for x in ("write", "draft", "compose")):
                prompt = f"Generate a well-structured and appropriate response for the following request: {user_text}. Ensure the tone matches the context (e.g., professional for formal requests, casual for informal ones)."
            else:
                prompt = f"Provide a clear and concise answer to the following: {user_text}"
            response = model.generate_content(prompt)
            return response.text.strip()

        tag = _predict_tag(user_text)
        for intent in INTENTS["intents"]:
            if intent["tag"] == tag:
                return random.choice(intent["responses"])

  
        prompt = f"Provide a clear and concise answer to the following: {user_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e):
            return "I’ve hit the Gemini API rate limit (1,500 requests/day). Please try again later or reduce usage."
        return f"Gemini API error: {str(e)}"

if __name__ == "__main__":
    print("Hello! I’m Friday, your desktop assistant. How can I help you today?")
    speak("Hello! I’m Friday, your desktop assistant. How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Friday: Goodbye!")
            speak("Goodbye!")
            break
        response = reply(user_input)
        print(f"Friday: {response}")
        speak(response)
