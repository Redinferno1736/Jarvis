import speech_recognition as sr
import google.generativeai as palm
import os
import pyttsx3
import platform
from dotenv import load_dotenv
import requests
import datetime
import yt_dlp
# Load environment variables
load_dotenv()

# Configure PaLM API Key
palm.configure(api_key=os.getenv("PALM_API_KEY"))

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

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


def get_latest_news():
    if not NEWS_API_KEY:
        return "News service is unavailable due to missing API key."

    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url).json()
        
        # ✅ Debugging - Print the entire API response (optional)
        # print(f"🌍 Debug: Full News API Response - {response}")

        if response.get("status") == "ok":
            articles = response.get('articles', [])

            if not articles:
                return "No news articles found."

            # Get the top 2 headlines
            headlines = [f"{i+1}. {article.get('title', 'No title')}" for i, article in enumerate(articles[:2])]

            return "\n".join(headlines)  # Join with a newline for better readability

        else:
            return f"News API Error: {response.get('message', 'Unknown error')}"

    except Exception as e:
        return f"News service is unavailable. Error: {e}"

    

def fetch_real_time_data(query):
    query = query.lower()

    if "time" in query:
        current_time = datetime.datetime.now().strftime("%I:%M %p")  # 12-hour format
        jarvis_response = f"The current time is {current_time}."
        print(f"🤖 Jarvis: {jarvis_response}")  # Print what Jarvis says
        return jarvis_response

    elif "weather" in query:
        weather_info = get_weather_data()
        jarvis_response = f"The current weather is {weather_info}."
        print(f"🤖 Jarvis: {jarvis_response}")  # Print what Jarvis says
        return jarvis_response

    elif "news" in query or "headlines" in query:
        news_info = get_latest_news()
        jarvis_response = f"Here are the top news headlines: {news_info}"
        print(f"🤖 Jarvis: {jarvis_response}")  # Print what Jarvis says
        return jarvis_response

    elif "play" in query:
        jarvis_response=play(query)
        print(f"🤖 Jarvis: {jarvis_response}")
        # return f"Here is the link to your song: {play(query)}" 

    return None  # If no real-time data is needed


def get_weather_data():
    url = "https://wttr.in/?format=%C+%t"  # Free weather API (Condition + Temperature)
    
    try:
        response = requests.get(url).text.strip()
        return response  # Return weather data
    except:
        return "Weather service is unavailable."


def play(text):
    t = text.replace("play", "").strip()

    if not t:
        return "Please specify a song name."

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'format': 'bestaudio/best'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch:{t}", download=False)
        if search_results and 'entries' in search_results and len(search_results['entries']) > 0:
            first_video_url = search_results['entries'][0]['url']
            return first_video_url
        else:
            return "No results found."


def generate_response(user_input):
    try:
        # ✅ Check if the query requires real-time data
        real_time_info = fetch_real_time_data(user_input) 
        if real_time_info:
            return real_time_info  # Directly return real-time data if available

        # ✅ Otherwise, generate AI response
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