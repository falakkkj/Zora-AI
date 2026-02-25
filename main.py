import speech_recognition as sr
import webbrowser
import pyttsx3
import os
import datetime
import random
import time
import threading
import winsound
import pyautogui
import requests
import psutil
import wikipedia
import screen_brightness_control as sbc
import warnings
import subprocess
from groq import Groq
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# 1. Silence Wikipedia HTML Warnings
warnings.filterwarnings("ignore", category=UserWarning, module='wikipedia')

# =========================
# CONFIGURATION & API
# =========================
# Load the secret .env file
load_dotenv()

# Get the key from the vault
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
chatStr = ""
is_speaking = False  # Safety lock to prevent Zora from hearing herself


# =========================
# UI & SPEECH ENGINE
# =========================
def update_ui(status):
    """Writes status to a file for Electron to read"""
    try:
        with open("ui_state.txt", "w") as f:
            f.write(status)
    except:
        pass


def play_sound(event):
    if event == "wake":
        winsound.Beep(800, 100);
        winsound.Beep(1200, 150)
    elif event == "done":
        winsound.Beep(1200, 100);
        winsound.Beep(800, 150)


def speak_task(text):
    """The 'Bulletproof' Speech Fix: Init and Del engine inside the thread."""
    global is_speaking
    try:
        is_speaking = True
        update_ui(f"Zora: {text}")
        engine = pyttsx3.init('sapi5')
        engine.setProperty('rate', 190)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        del engine  # Critical for clearing the COM loop
    except Exception as e:
        print(f"Speech Error: {e}")
    finally:
        is_speaking = False
        update_ui("Dormant")


def say(text):
    """Threaded speech to keep the main loop and UI alive"""
    print(f"\nZora: {text}")
    threading.Thread(target=speak_task, args=(text,), daemon=True).start()


# =========================
# CORE FUNCTIONS
# =========================
def launch_ui():
    """Bypasses npx/npm and launches the executable directly to avoid SIGINT crashes"""
    try:
        # Kill any hanging electron processes first
        subprocess.run("taskkill /F /IM electron.exe /T", shell=True, stderr=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL)

        project_dir = os.getcwd()
        electron_cmd = os.path.join(project_dir, "node_modules", ".bin", "electron.cmd")

        if os.path.exists(electron_cmd):
            # Launch as a detached process so it doesn't close with the terminal
            subprocess.Popen([electron_cmd, "."], shell=True, creationflags=subprocess.DETACHED_PROCESS)
            print("🚀 Zora UI Launching...")
        else:
            # Final fallback
            subprocess.Popen(["npx", "electron", "."], shell=True)
    except Exception as e:
        print(f"UI Launch Error: {e}")


def takeCommand(timeout_val=None):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.6)
        try:
            audio = recognizer.listen(source, timeout=timeout_val, phrase_time_limit=7)
            print("🧠 Recognizing...")
            query = recognizer.recognize_google(audio, language="en-in")
            return query.lower()
        except:
            return "none"


def ai_chat(prompt):
    global chatStr
    chatStr += f"User: {prompt}\nZora: "
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": "You are Zora, a witty assistant. Be concise."}],
            max_tokens=200
        )
        res = completion.choices[0].message.content
        chatStr += f"{res}\n";
        return res
    except:
        return "Brain offline, sir."


# =========================
# MAIN APP LOOP
# =========================
if __name__ == "__main__":
    launch_ui()
    time.sleep(3)
    say("All systems active. Zora is online.")

    while True:
        # Don't listen if Zora is talking
        if is_speaking:
            time.sleep(0.5)
            continue

        print("\n--- Dormant (Waiting for 'Hey Zora') ---")
        update_ui("Waiting for 'Hey Zora'...")
        wake = takeCommand()

        if "zora" in wake or "hey zora" in wake:
            update_ui("Active")
            play_sound("wake")
            say(random.choice(["At your service.", "I'm here.", "Go ahead.", "Yes?"]))

            # Wait for Zora to finish speaking before opening the mic
            while is_speaking:
                time.sleep(0.1)

            print("🎤 Listening...")
            update_ui("Listening...")
            command = takeCommand(timeout_val=5)

            if command == "none":
                continue

            # --- 1. DATETIME & OS (ALL FEATURES PRESERVED) ---
            if any(x in command for x in ["time", "clock"]):
                say(f"Sir, the current time is {datetime.datetime.now().strftime('%I:%M %p')}")
            elif any(x in command for x in ["date", "today"]):
                say(f"Today's date is {datetime.datetime.now().strftime('%B %d, %Y')}")
            elif "day" in command:
                say(f"Today is {datetime.datetime.now().strftime('%A')}")
            elif "list" in command and ("directory" in command or "files" in command):
                files = os.listdir(os.getcwd())
                print(f"Files: {files}")
                say(f"Listing directory. I found {len(files)} items.")

            # --- 2. HARDWARE CONTROLS ---
            elif "volume" in command:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                vol = cast(interface, POINTER(IAudioEndpointVolume))
                if "up" in command:
                    vol.SetMasterVolumeLevelScalar(min(vol.GetMasterVolumeLevelScalar() + 0.2, 1.0), None)
                    say("Volume up.")
                else:
                    vol.SetMasterVolumeLevelScalar(max(vol.GetMasterVolumeLevelScalar() - 0.2, 0.0), None)
                    say("Volume down.")

            elif "brightness" in command:
                curr = sbc.get_brightness()[0]
                if "up" in command or "increase" in command:
                    sbc.set_brightness(min(curr + 25, 100));
                    say("Brightness up.")
                else:
                    sbc.set_brightness(max(curr - 25, 0));
                    say("Brightness down.")

            # --- 3. APPS & MEDIA ---
            elif "spotify" in command:
                say("Opening Spotify");
                pyautogui.press("win");
                time.sleep(0.5);
                pyautogui.write("spotify");
                pyautogui.press("enter")
            elif "play" in command:
                song = command.replace("play", "").strip()
                say(f"Playing {song} on YouTube");
                webbrowser.open(f"https://youtube.com/results?search_query={song}")
            elif "open website" in command:
                site = command.replace("open website", "").strip()
                say(f"Opening {site}");
                webbrowser.open(f"https://www.{site}.com")

            # --- 4. SYSTEM STATS & WEATHER ---
            elif "system" in command or "status" in command:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                battery = psutil.sensors_battery()
                status = f"CPU is at {cpu} percent. Memory is at {ram} percent."
                if battery: status += f" Battery is at {battery.percent} percent."
                say(status)
            elif "weather" in command:
                try:
                    res = requests.get("https://wttr.in/Ajmer?format=3")
                    say(f"In Ajmer, {res.text.strip()}")
                except:
                    say("Weather service unreachable.")

            # --- NEWS HEADLINES (requests) ---
            elif "news" in command:
                say("Fetching the latest headlines for you, sir.")
                try:
                    # Using a public API (NewsAPI requires a key, but we can scrape or use a free feed)
                    # For a quick start, we use a curated tech feed
                    res = requests.get("https://newsapi.org/v2/top-headlines?sources=techcrunch&apiKey=YOUR_API_KEY")
                    data = res.json()
                    articles = data['articles'][:3]  # Get top 3
                    for i, ar in enumerate(articles):
                        say(f"Headline number {i + 1}: {ar['title']}")
                except:
                    say("I'm sorry, I couldn't reach the news server right now.")

            # --- 5. SEARCH & UTILITIES ---
            elif "screenshot" in command:
                pyautogui.screenshot(f"shot_{int(time.time())}.png");
                say("Captured.")
            elif "who is" in command or "what is" in command:
                topic = command.replace("who is", "").replace("what is", "").strip()
                try:
                    res = wikipedia.summary(topic, sentences=2)
                    say(res)
                except:
                    say(ai_chat(topic))

            elif any(x in command for x in ["exit", "quit", "goodbye"]):
                say("Goodbye, sir.");
                play_sound("done");
                break

            # --- 6. AI FALLBACK ---
            else:
                say(ai_chat(command))

            print("--- Task Finished ---")