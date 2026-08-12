import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import smtplib
import requests
import threading
import json
import os
import re
import urllib.parse
from email.message import EmailMessage

# ==========================================
# CONFIGURATION & API KEYS
# ==========================================
# Replace with your OpenWeatherMap API Key (https://openweathermap.org/)
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY_HERE"

# Dummy Email Configuration (Use an app-specific password in production)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_dummy_email@gmail.com"
SENDER_PASSWORD = "your_app_password"

# Pre-defined contacts for voice-to-email mapping
CONTACTS = {
    "myself": "jelliot528@gmail.com",
    "test": "jelliot528@gmail.com"
}

CUSTOM_COMMANDS_FILE = "custom_commands.json"

# ==========================================
# TEXT-TO-SPEECH (TTS) SETUP
# ==========================================
engine = pyttsx3.init()
# Optional: Configure voice properties
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) # Index 0 usually male, 1 usually female
engine.setProperty('rate', 170) # Speaking rate

def speak(text):
    """Converts text to speech and prints it to the console."""
    print(f"\n Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

# ==========================================
# SPEECH-TO-TEXT (STT) SETUP
# ==========================================
def listen(prompt_text=None):
    """Listens to microphone input and converts it to text."""
    if prompt_text:
        speak(prompt_text)
        
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[Listening...]")
        # Adjust for ambient noise for better accuracy
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return None

    try:
        print("[Processing...]")
        text = recognizer.recognize_google(audio)
        print(f" You: {text}")
        return text.lower()
    except sr.UnknownValueError:
        # Graceful error handling for unrecognized speech
        return None
    except sr.RequestError as e:
        speak("My speech recognition service is currently unavailable. Please check your internet connection.")
        print(f"Error: {e}")
        return "ERROR"

# ==========================================
# NATURAL LANGUAGE UNDERSTANDING (NLU)
# ==========================================
def load_custom_commands():
    """Loads user-defined custom commands from a JSON config file."""
    if os.path.exists(CUSTOM_COMMANDS_FILE):
        with open(CUSTOM_COMMANDS_FILE, "r") as f:
            return json.load(f)
    return {}

def parse_intent(text):
    """
    Parses intent from free-form spoken sentences using regex and keyword mapping.
    This fulfills the advanced NLU requirement without heavy ML libraries.
    """
    custom_commands = load_custom_commands()
    
    # 1. Check Custom Commands first
    for cmd, response in custom_commands.items():
        if cmd in text:
            return {"intent": "custom", "response": response}

    # 2. Weather Intent (e.g., "What is the weather in London")
    weather_match = re.search(r'(weather|temperature).* in ([\w\s]+)', text)
    if weather_match:
        return {"intent": "weather", "city": weather_match.group(2).strip()}

    # 3. Search Intent (e.g., "Search for python tutorials")
    search_match = re.search(r'(search for|google|look up) (.*)', text)
    if search_match:
        return {"intent": "search", "query": search_match.group(2).strip()}

    # 4. Reminder Intent (e.g., "Remind me to drink water in 10 minutes")
    reminder_match = re.search(r'remind me to (.*) in (\d+) (second|minute|hour)s?', text)
    if reminder_match:
        return {
            "intent": "reminder", 
            "task": reminder_match.group(1).strip(), 
            "amount": int(reminder_match.group(2)), 
            "unit": reminder_match.group(3)
        }

    # 5. General Knowledge (e.g., "Who is Albert Einstein")
    qa_match = re.search(r'(who is|what is|tell me about) (.*)', text)
    if qa_match:
        # Exclude common phrases that might trigger false positives
        if qa_match.group(2) not in ["the time", "the date", "the weather"]:
            return {"intent": "question", "query": qa_match.group(2).strip()}

    # 6. Email Intent
    if "send an email" in text or "send email" in text:
        return {"intent": "email"}
        
    # 7. Add Custom Command Intent
    if "add custom command" in text or "learn a new command" in text:
        return {"intent": "add_custom"}

    # 8. Basic Keyword Intents
    if "time" in text:
        return {"intent": "time"}
    if "date" in text or "day is it" in text:
        return {"intent": "date"}
    if any(word in text.split() for word in ["hello", "hi", "hey", "greetings"]):
        return {"intent": "greeting"}
    if "stop" in text or "exit" in text or "goodbye" in text:
        return {"intent": "exit"}

    return {"intent": "unknown"}

# ==========================================
# ACTION HANDLERS
# ==========================================
def handle_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {now}")

def handle_date():
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {today}")

def handle_search(query):
    speak(f"Searching the web for {query}")
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(url)

def handle_weather(city):
    if OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY_HERE":
        speak("Weather API key is missing. Please configure it in the script.")
        return
        
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url).json()
        if response["cod"] == 200:
            temp = response["main"]["temp"]
            desc = response["weather"][0]["description"]
            speak(f"The current temperature in {city.title()} is {temp} degrees Celsius with {desc}.")
        else:
            speak(f"I couldn't find weather information for {city}.")
    except Exception as e:
        speak("There was an error fetching the weather data.")

def handle_question(query):
    # Using Wikipedia API via requests to answer general knowledge questions
    speak(f"Looking up {query}...")
    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=&explaintext=&titles={urllib.parse.quote(query)}"
    try:
        response = requests.get(url).json()
        pages = response["query"]["pages"]
        for page_id in pages:
            if page_id == "-1":
                speak("I couldn't find an answer to that question.")
                return
            extract = pages[page_id]["extract"]
            # Read only the first sentence or two
            short_answer = extract.split(". ")[0] + "."
            speak(short_answer)
            return
    except Exception:
        speak("I had trouble accessing the knowledge database.")

def handle_email():
    recipient_name = listen("Who would you like to email? (Say 'myself' or 'test')")
    if not recipient_name:
        speak("Email cancelled.")
        return
        
    recipient_email = CONTACTS.get(recipient_name)
    if not recipient_email:
        speak(f"I don't have an email address saved for {recipient_name}.")
        return

    message_body = listen("What should the email say?")
    if not message_body:
        speak("Email cancelled.")
        return

    speak("Sending email now...")
    try:
        msg = EmailMessage()
        msg.set_content(message_body)
        msg['Subject'] = 'Message from Voice Assistant'
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        speak("Email has been sent successfully.")
    except Exception as e:
        print(f"Email Error: {e}")
        speak("I was unable to send the email. Please check your credentials and internet connection.")

def handle_reminder(task, amount, unit):
    # Convert time to seconds
    multiplier = {"second": 1, "minute": 60, "hour": 3600}
    delay_seconds = amount * multiplier[unit]
    
    speak(f"Reminder set! I will remind you to {task} in {amount} {unit}s.")
    
    def alarm():
        # Play a sound or speak when time is up
        print("\n [REMINDER ALERT] ")
        # Initialize a new TTS engine instance for the thread to prevent COM errors on Windows
        thread_engine = pyttsx3.init()
        thread_engine.say(f"Reminder alert! It is time to {task}")
        thread_engine.runAndWait()

    # Run reminder in a background thread so it doesn't block the assistant
    t = threading.Timer(delay_seconds, alarm)
    t.daemon = True
    t.start()

def add_custom_command():
    trigger = listen("What should I listen for? For example, say 'activate protocol omega'.")
    if not trigger:
        speak("Command addition cancelled.")
        return
        
    response = listen(f"What should I say when you say {trigger}?")
    if not response:
        speak("Command addition cancelled.")
        return
        
    commands = load_custom_commands()
    commands[trigger] = response
    
    with open(CUSTOM_COMMANDS_FILE, "w") as f:
        json.dump(commands, f, indent=4)
        
    speak(f"Custom command saved. I will now respond to '{trigger}'.")

# ==========================================
# MAIN ASSISTANT LOOP
# ==========================================
def main():
    speak("System initialized. Hello, I am your voice assistant. How can I help you?")
    
    while True:
        command = listen()
        
        # Graceful error handling: if voice is not understood
        if command is None:
            speak("I didn't catch that. Could you please repeat?")
            continue
        if command == "ERROR":
            continue # API error already spoken in listen()

        # Parse Intent
        parsed = parse_intent(command)
        intent = parsed["intent"]

        # Route to appropriate action handler
        if intent == "greeting":
            speak("Hello there! I'm ready to assist you.")
        elif intent == "time":
            handle_time()
        elif intent == "date":
            handle_date()
        elif intent == "search":
            handle_search(parsed["query"])
        elif intent == "weather":
            handle_weather(parsed["city"])
        elif intent == "question":
            handle_question(parsed["query"])
        elif intent == "reminder":
            handle_reminder(parsed["task"], parsed["amount"], parsed["unit"])
        elif intent == "email":
            handle_email()
        elif intent == "add_custom":
            add_custom_command()
        elif intent == "custom":
            speak(parsed["response"])
        elif intent == "exit":
            speak("Goodbye! Shutting down.")
            break
        else:
            speak("I'm not sure how to help with that yet. You can try rephrasing.")

if __name__ == "__main__":
    main()