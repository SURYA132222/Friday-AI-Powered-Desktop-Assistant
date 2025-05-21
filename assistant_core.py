"""
Friday’s full logic for the Flask web assistant.

Public API
----------
reply(text)  -> str     # choose a response + perform side-effects
greet()      -> str     # day/time greeting message
speak(text)            # optional server-side TTS
"""

import datetime, time, os, webbrowser, random, json, pickle, psutil
import pyautogui, pyttsx3, numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# ── Load ML assets once ────────────────────────────────────────────
with open("intents.json") as f:
    INTENTS = json.load(f)

MODEL       = load_model("chat_model.h5")
TOKENIZER   = pickle.load(open("tokenizer.pkl", "rb"))
LABEL_ENC   = pickle.load(open("label_encoder.pkl", "rb"))
MAX_LEN     = 20

# ── Server-side TTS (optional) ─────────────────────────────────────
_tts = None
def speak(txt: str):
    global _tts
    if _tts is None:
        _tts = pyttsx3.init("sapi5")
        _tts.setProperty("voice", _tts.getProperty("voices")[1].id)
        _tts.setProperty("rate", _tts.getProperty("rate")-50)
        _tts.setProperty("volume", 1.0)
    _tts.say(txt)
    _tts.runAndWait()

# ── Greeting on page load ──────────────────────────────────────────
def greet() -> str:
    now   = datetime.datetime.now()
    day   = now.strftime("%A")
    clock = now.strftime("%I:%M %p")
    if   now.hour < 12:  return f"Good morning! It’s {day}, {clock}."
    elif now.hour < 17:  return f"Good afternoon! It’s {day}, {clock}."
    else:                return f"Good evening! It’s {day}, {clock}."

# ── Helpers for side-effects ───────────────────────────────────────
def _open(url, msg):       webbrowser.open(url) ; return msg
def _app(path, name):      os.startfile(path)   ; return f"Opening {name}"
def _kill(exe, name):      os.system(f"taskkill /f /im {exe}") ; return f"Closing {name}"

WEEK = {
    "monday":    "9-9:50 Python (CR-201); 10-11 ML (CR-405)",
    "tuesday":   "8-10 DSA (LT-201); 2-2:50 DAA (CR-402)",
    "wednesday": "2:10-4 ML (LT-301)",
    "thursday":  "8-9:50 Python (CR-301); 1-1:50 DL (CR-405)",
    "friday":    "3-5 DSA (LT-401)",
    "saturday":  "9-9:50 Python; 10-11 ML",
    "sunday":    "Holiday 🎉"
}

def _predict_tag(text):
    seq  = TOKENIZER.texts_to_sequences([text])
    pad  = pad_sequences(seq, maxlen=MAX_LEN, truncating="post")
    tag  = LABEL_ENC.inverse_transform([np.argmax(MODEL.predict(pad,verbose=0))])[0]
    return tag

# ── MAIN REPLY FUNCTION ────────────────────────────────────────────
def reply(user_text: str) -> str:
    low = user_text.lower()

    # ---- direct keyword actions -----------------------------------
    if any(site in low for site in ("facebook","whatsapp","discord","instagram")):
        if "facebook" in low:  return _open("https://www.facebook.com","Opening Facebook")
        if "whatsapp" in low:  return _open("https://web.whatsapp.com","Opening WhatsApp")
        if "discord"  in low:  return _open("https://discord.com","Opening Discord")
        if "instagram" in low: return _open("https://www.instagram.com","Opening Instagram")

    if "open calculator" in low:   return _app(r"C:\Windows\System32\calc.exe","Calculator")
    if "open notepad"    in low:   return _app(r"C:\Windows\System32\notepad.exe","Notepad")
    if "open paint"      in low:   return _app(r"C:\Windows\System32\mspaint.exe","Paint")

    if "close calculator" in low:  return _kill("calc.exe","Calculator")
    if "close notepad"    in low:  return _kill("notepad.exe","Notepad")
    if "close paint"      in low:  return _kill("mspaint.exe","Paint")

    if "volume up" in low or "increase volume" in low:
        pyautogui.press("volumeup");   return "Volume increased 🔊"
    if "volume down" in low or "decrease volume" in low:
        pyautogui.press("volumedown"); return "Volume decreased 🔉"
    if "mute" in low:
        pyautogui.press("volumemute"); return "Volume muted 🔇"

    if "schedule" in low or "time table" in low:
        today = datetime.datetime.today().strftime("%A").lower()
        return f"Your schedule for today: {WEEK[today]}"

    if "system condition" in low or "condition of the system" in low:
        cpu   = psutil.cpu_percent()
        batt  = psutil.sensors_battery().percent
        return f"CPU usage {cpu} % • Battery {batt} %."

    # ---- ML intent fall-back --------------------------------------
    tag = _predict_tag(user_text)
    for intent in INTENTS["intents"]:
        if intent["tag"] == tag:
            return random.choice(intent["responses"])

    return "Sorry, I didn’t catch that 🤔."
