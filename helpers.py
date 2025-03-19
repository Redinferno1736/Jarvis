import speech_recognition as sr
import google.generativeai as palm
import os
import pyttsx3
import platform
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure PaLM API Key
palm.configure(api_key=os.getenv("PALM_API_KEY"))

def recognize_speech():
    recognizer = sr.Recognizer()

    # ✅ OS-Specific Handling
    if platform.system() == "Windows":
        # Windows uses PyAudio directly
        mic_source = sr.Microphone()
    else:
        # Linux uses FFmpeg (Render)
        mic_source = sr.Microphone()

    with mic_source as source:
        print("🎤 Say something...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣 You said: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return None
    except sr.RequestError:
        print("❌ Speech recognition service unavailable")
        return None

def generate_response(user_input):
    try:
        # Load the latest Gemini model
        model = palm.GenerativeModel('models/gemini-1.5-pro')

        prompt = f"You are Jarvis. Respond accurately:\nUser: {user_input}\nJarvis:"
        response = model.generate_content(prompt)
        
        tony_response = response.text
        print(f"🤖 Jarvis: {tony_response}")
        return tony_response

    except Exception as e:
        print(f"❌ Error: {e}")
        return "I'm currently unable to process that. Try again later."

def speak_text(text):
    engine = pyttsx3.init()

    # ✅ Adjust speed (default = 200)
    engine.setProperty('rate', 200)

    # ✅ Adjust voice based on OS
    voices = engine.getProperty('voices')
    if platform.system() == "Windows":
        engine.setProperty('voice', voices[0].id)  # 0 = male, 1 = female
    else:  # Linux (Render) → Use espeak
        engine.setProperty('voice', "english")

    engine.say(text)
    engine.runAndWait()

# Full conversation loop
if __name__ == "__main__":
    while True:
        user_query = recognize_speech()
        if user_query:
            response = generate_response(user_query)
            speak_text(response)