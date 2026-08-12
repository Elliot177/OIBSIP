#  Voice Assistant


A fully-featured Python voice assistant with **Beginner**,
built with `speech_recognition`
---

## Feature Checklist

###  Beginner Tier
| # | Feature | File |
|---|---------|------|
| 1 | Capture voice input via microphone | `voice_engine.py` |
| 2 | Respond to "Hello" with a greeting | `commands/basic.py` |
| 3 | Tell current time and date | `commands/basic.py` |
| 4 | Web search — open browser with query | `commands/basic.py` |
| 5 | Graceful error handling / retry on silence | `core.py` |
| 6 | Text-to-speech via pyttsx3 | `voice_engine.py` |


## Project Structure

```
voice_assistant/
├── main.py                         ← Entry point (CLI flags)
├── setup_check.py                  ← Installation verifier
├── requirements.txt
│
├── assistant/
│   ├── core.py                     ← Main run loop + command dispatch
│   ├── voice_engine.py             ← STT (Google) + TTS (pyttsx3)
│   └── commands/
│       ├── basic.py                ← Greeting, time, date, web search
│       ├── weather.py              ← OpenWeatherMap live weather
│       ├── reminder.py             ← Thread-based timed reminders
│       └── custom_cmd.py           ← User-defined commands
│
└── config/
    ├── settings.json               ← API keys & voice settings
    └── custom_commands.json        ← User-defined trigger→response pairs
```

---

## Installation

### Prerequisites

| Platform | System requirement |
|----------|--------------------|
| Windows  | Python 3.8+, VS CODE |


```

> **PyAudio on Windows**  
> If `pip install pyaudio`  
> 
### 2 — Verify

```bash
python setup_check.py
```

## Voice Commands 
|Say| Action|
|---|-------|
|"What time is it?" | Current time |
| "What's today's date?" | Current date |