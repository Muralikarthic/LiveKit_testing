# Amanda Voice Bot

Amanda Voice Bot is a minimal, local, real-time voice assistant built with:
- **LiveKit**: Real-time WebRTC infrastructure
- **LiveKit Agents**: Python framework for building real-time AI agents
- **Google Gemini Live API**: Multimodal real-time model powering natural voice interactions
- **Python**: Core runtime
- **Aoede**: Natural female voice for Amanda

---

## Architecture

```
[ Microphone ] ---> [ Local LiveKit Server ] ---> [ Amanda Agent ]
                                                         |
                                                         v
[ Speaker ] <--- [ Amanda Voice (Aoede) ] <--- [ Google Gemini Live API ]
```

> [!NOTE]
> This project is a **100% LOCAL development setup**. It connects directly to a locally running LiveKit Server on your machine and **does not require LiveKit Cloud**.

---

## Prerequisites

Before starting, ensure you have the following installed on your local machine:

1. **Operating System:** Windows 10/11 (or macOS/Linux)
2. **Python:** Version 3.10 or higher
3. **LiveKit CLI (`lk`):** Installed via winget on Windows:
   ```powershell
   winget install LiveKit.LiveKitCLI
   ```
4. **Local LiveKit Server:** A local `livekit-server.exe` executable in the project root or PATH.
5. **Google Gemini API Key:** An active API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## Project Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/Muralikarthic/LiveKit_testing.git
   cd LiveKit_testing
   ```

2. **Switch to the Amanda branch:**
   ```powershell
   git checkout Amanda-Voice-bot
   ```

3. **Create and activate a Python virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

4. **Install project dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Windows Execution Alias Fix:**
   On Windows, the LiveKit CLI invokes `python3`. To ensure `lk` uses your virtual environment, copy `python.exe` to `python3.exe` inside your virtual environment scripts directory:
   ```powershell
   Copy-Item .\venv\Scripts\python.exe .\venv\Scripts\python3.exe -Force
   ```

---

## Environment Variables

Copy `.env.example` to create your local `.env` file:

```powershell
copy .env.example .env
```

Your `.env` file must contain the following variables:

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
GOOGLE_API_KEY=your_gemini_api_key_here
```

> [!CAUTION]
> `.env` contains sensitive credentials and is intentionally ignored by `.gitignore`. **Never commit `.env` or your real API key to Git.**

### How to get a Gemini API Key:
1. Go to **Google AI Studio**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account.
3. Click **Create API Key**.
4. Copy the generated key and replace `your_gemini_api_key_here` in your local `.env` file.

---

## Running Amanda Locally

To run Amanda locally, open **three separate terminal windows** in the project directory:

### Terminal 1: Local LiveKit Server
Start the local LiveKit WebRTC server in development mode:
```powershell
.\livekit-server.exe --dev
```
*Listens on `http://localhost:7880` with default developer credentials (`devkey` / `secret`).*

---

### Terminal 2: Amanda Python Agent
Activate the virtual environment and launch the agent worker:
```powershell
.\venv\Scripts\activate
lk agent dev --dev agent.py
```
*Connects the Amanda agent to your local LiveKit server and watches for code changes with auto-reload.*

---

### Terminal 3: Voice Console Client
Activate the virtual environment and start the audio console:
```powershell
.\venv\Scripts\activate
lk agent console --dev
```
*Connects your local microphone and speakers to the local LiveKit room so you can speak to Amanda and hear her responses.*

---

## How It Works

1. **Terminal 1 (`livekit-server`)** hosts the WebRTC media routing server locally.
2. **Terminal 2 (`lk agent dev`)** executes `agent.py`, registering the `amenda` worker with the local server.
3. **Terminal 3 (`lk agent console`)** joins the room as a local audio client, sending your microphone audio over WebRTC to the agent worker.
4. **Amanda** processes input audio stream via **Google Gemini Live API** and streams back real-time audio responses using the **Aoede** female voice to your speakers.

---

## Voice

Amanda uses Gemini's **`Aoede`** voice—a natural, warm, female-sounding voice.

The voice is configured in `agent.py`:
```python
session = AgentSession(
    llm=google.realtime.RealtimeModel(
        voice="Aoede",
    ),
)
```

---

## Current Scope

### What is implemented:
- Local real-time microphone audio input
- Real-time conversational AI via Google Gemini Live API
- Spoken voice responses from Amanda
- Local LiveKit WebRTC server integration
- Aoede female voice configuration
- Fully local development workflow

### What is NOT implemented:
- Camera / video input
- Avatar / video output
- Web frontend
- Database storage
- User authentication
- Tool / function calling
- Persistent session memory
- Production cloud deployment
- LiveKit Cloud infrastructure

---

## Troubleshooting

* **LiveKit Server Port Conflict (`7880` in use):**
  Ensure no previous instance of `livekit-server` is running:
  ```powershell
  Get-Process livekit-server -ErrorAction SilentlyContinue | Stop-Process
  ```

* **Invalid Gemini API Key (Error 1007):**
  If you see `API key not valid. Please pass a valid API key`, verify that your `GOOGLE_API_KEY` in `.env` is correct and active in [Google AI Studio](https://aistudio.google.com/app/apikey).

* **`Python was not found` error with `lk agent dev` on Windows:**
  Ensure you ran the copy command in your virtual environment:
  ```powershell
  Copy-Item .\venv\Scripts\python.exe .\venv\Scripts\python3.exe -Force
  ```

* **Audio Device Selection:**
  To list available input and output devices:
  ```powershell
  lk agent console --dev --list-devices
  ```
  You can specify input/output devices explicitly if needed:
  ```powershell
  lk agent console --dev --input-device "Microphone Array" --output-device "Headphones"
  ```

---

## Repository Structure

```
├── agent.py          # Amanda agent worker logic and entrypoint
├── pyproject.toml    # Python project configuration and dependencies
├── requirements.txt  # Python dependency specification for pip
├── .env.example      # Environment variable template with placeholders
├── .gitignore        # Git ignore rules for virtualenvs, keys, binaries
└── README.md         # Project setup and usage instructions
```

---

## Security

- Never commit `.env` or any secrets to version control.
- `GOOGLE_API_KEY` must remain strictly local to your machine.
- `.env.example` contains template placeholders only.

---

## Quick Start

```powershell
# 1. Clone & checkout branch
git clone https://github.com/Muralikarthic/LiveKit_testing.git
cd LiveKit_testing
git checkout Amanda-Voice-bot

# 2. Setup Virtual Environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .\venv\Scripts\python.exe .\venv\Scripts\python3.exe -Force

# 3. Configure Environment
copy .env.example .env
# Edit .env and paste your GOOGLE_API_KEY from Google AI Studio

# 4. Launch (3 Terminals)
# Terminal 1: .\livekit-server.exe --dev
# Terminal 2: .\venv\Scripts\activate; lk agent dev --dev agent.py
# Terminal 3: .\venv\Scripts\activate; lk agent console --dev
```
