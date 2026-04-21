# CampusEdge — Smart Campus Placement Platform

## Project Structure

```
placement_platform/
├── app.py                      ← Flask backend (all routes)
├── firebase_config.py          ← Firebase connection
├── requirements.txt
├── serviceAccountKey.json      ← YOU add this (see setup)
├── templates/
│   ├── index.html              ← Landing page
│   ├── tpo_login.html
│   ├── tpo_register.html
│   ├── tpo_dashboard.html
│   ├── student_login.html
│   ├── student_register.html
│   ├── student_dashboard.html
│   ├── alumni_login.html
│   ├── alumni_register.html
│   ├── alumni_dashboard.html
│   ├── market_intelligence.html
│   └── admin_dashboard.html
└── static/
    ├── css/style.css
    └── js/script.js
```

---

## Setup Instructions (VS Code)

### Step 1 — Clone / Open the Project
Open the `placement_platform/` folder in VS Code.

### Step 2 — Create Python Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Firebase Setup
1. Go to https://console.firebase.google.com
2. Create a new project (e.g. "campusedge")
3. Enable **Firestore Database** (Start in test mode)
4. Go to **Project Settings → Service Accounts**
5. Click **"Generate new private key"**
6. Download the JSON file → rename it `serviceAccountKey.json`
7. Place it in the `placement_platform/` root folder
8. Open `firebase_config.py` and replace `"your-project-id"` with your Firebase project ID

### Step 5 — Run the App
```bash
python app.py
```

### Step 6 — Open in Browser
```
http://localhost:5000
```

---

## Usage Guide

| Portal | URL | Flow |
|--------|-----|------|
| Landing | `/` | Entry point |
| TPO | `/tpo/register` → `/tpo/login` → `/tpo/dashboard` | Register first |
| Student | `/student/register` → `/student/login` → `/student/dashboard` | Register with CGPA & branch |
| Alumni | `/alumni/register` → `/alumni/login` → `/alumni/dashboard` | Register with company |
| Market | `/market` | No login required |
| Admin | `/admin` | No login required |

## Key Features

- **TPO creates a drive** → system auto-notifies eligible students
- **Student applies** → TPO tracks them through stages
- **Alumni submits referral** → TPO approves → students notified
- **AI Resume Analyzer** → POST `/student/analyze_resume` (connect OpenAI for real analysis)

## Connecting Real OpenAI Resume Analysis

In `app.py`, replace the mock in `analyze_resume()`:

```python
import openai
openai.api_key = "your-api-key"

def analyze_resume():
    # Read uploaded file text
    text = extract_text_from_resume(...)
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user","content":f"Analyze this resume and return JSON with score, missing_skills, suggestions: {text}"}]
    )
    return jsonify(json.loads(response.choices[0].message.content))
```
