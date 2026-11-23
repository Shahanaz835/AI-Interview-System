# AI-Based Interview Preparation and Candidate Performance Evaluation System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-092E20.svg)](https://www.djangoproject.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Cloud-f55036.svg)](https://groq.com/)
[![Web Speech API](https://img.shields.io/badge/Voice-Web%20Speech%20API-success.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
[![Bootstrap 5](https://img.shields.io/badge/UI-Bootstrap%205-purple.svg)](https://getbootstrap.com/)
[![Chart.js](https://img.shields.io/badge/Visuals-Chart.js-orange.svg)](https://www.chartjs.org/)

An industry-level, AI-driven mock interview and performance evaluation platform designed for Computer Science & Engineering students and job seekers. The system acts as a real-time conversational interviewer that reads candidate resumes, asks tailored technical and behavioral questions, listens to spoken answers via Web Speech recognition, evaluates responses using Large Language Models (LLMs), and talks back in real time.

---

## Key Features

1. **User Authentication & Candidate Profile**:
   - Secure registration, login, and candidate profile management.
   - Profile settings to choose target engineering roles and experience levels.

2. **Resume PDF Upload & NLP Technical Extraction**:
   - Parses resumes using `pypdf`.
   - NLP taxonomy matching extracts 70+ technical skills across Languages, Frameworks, Databases, Tools, and Core CS Concepts.
   - Detects Projects, Education, Experience, and Certifications.
   - Provides a Resume Readiness Score (0-100) and gap analysis.

3. **Resume-Grounded AI Interview Questions**:
   - Dynamic prompts ground interview questions directly into the candidate's actual projects and technical stack.
   - Context-aware questioning avoids generic, repetitive queries.

4. **Three Core Interview Tracks**:
   - **Technical Interview**: Python, Java, C/C++, SQL, DBMS, DSA, OOP, OS, Networks, Web Development.
   - **HR Behavioral Interview**: Leadership, conflict resolution, teamwork, and situational STAR format questions.
   - **Aptitude & Reasoning Interview**: Quantitative aptitude, speed math, logical deduction, and analytical problems.

5. **Real-Time Voice-to-Voice Interaction**:
   - **Text-to-Speech (TTS)**: Web SpeechSynthesis API speaks questions and feedback automatically.
   - **Speech-to-Text (STT)**: Web SpeechRecognition API captures microphone speech in real-time with visual audio wave animations.
   - Text typing fallback supported if a microphone is unavailable.

6. **Intelligent Multidimensional Evaluation**:
   - Scores responses out of 10.
   - Evaluates technical correctness, relevance, completeness, and clarity.
   - Identifies strengths, missing concepts, mistakes, and provides an ideal model answer.

7. **Adaptive Difficulty Engine**:
   - Strong answers raise question complexity; incomplete answers trigger hints or clarifying questions.

8. **Performance Dashboard & Chart.js Analytics**:
   - Score improvement timeline (Line Chart).
   - Track-wise performance comparison (Bar Chart).
   - Subject-by-subject mastery breakdown table.

9. **Personalized AI Learning Roadmap**:
   - Analyzes detected mistakes to synthesize a tailored 7-day study schedule, priority study topics, and targeted practice questions.

---

## Technology Stack

- **Backend Framework**: Django 5.x (Python)
- **Database**: SQLite3
- **AI & LLM Inference**: Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`)
- **Document Processing**: `pypdf`
- **Voice Interaction**: Web Speech API (`SpeechRecognition` & `SpeechSynthesis`)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, FontAwesome 6
- **Data Visualization**: Chart.js
- **Environment Management**: `python-dotenv`

---

## Project Structure

```text
AI Interviewer/
├── accounts/                  # User authentication & candidate profile app
│   ├── forms.py               # Custom registration & login forms
│   ├── models.py              # UserProfile model with signals
│   ├── urls.py                # Accounts routing
│   └── views.py               # Auth & dashboard controllers
├── interviews/                # Core AI interview engine app
│   ├── forms.py               # Resume upload & interview setup forms
│   ├── groq_service.py        # Groq LLM prompts & inference service
│   ├── models.py              # Resume, Session, Question, Evaluation models
│   ├── resume_parser.py       # PyPDF parser & NLP skill extractor
│   ├── urls.py                # Interview routing & JSON APIs
│   └── views.py               # Live room, results, analytics & roadmaps
├── ai_interview_system/       # Main project settings & URL configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                    # CSS stylesheets & JS voice scripts
│   ├── css/styles.css
│   └── js/voice_interview.js
├── templates/                 # Bootstrap 5 HTML templates
│   ├── accounts/
│   ├── interviews/
│   └── base.html
├── Sample_CSE_Resume.pdf      # Sample resume for quick testing
├── requirements.txt           # Project dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Security rules (ignores .env, db, venv)
└── manage.py                  # Django CLI
```

---

## Quick Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-interview-system.git
cd ai-interview-system
```

### 2. Create and Activate Virtual Environment
```bash
# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env   # Windows
# or: cp .env.example .env (Linux/Mac)
```
Add your free Groq API key in `.env`:
```env
SECRET_KEY=django-insecure-ai-interviewer-cse-key
DEBUG=True
GROQ_API_KEY=your_groq_api_key_here
```
*(Get a free Groq API key at [console.groq.com](https://console.groq.com/keys)).*

### 5. Run Migrations & Test Suite
```bash
python manage.py migrate
python manage.py test
```

### 6. Start the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your web browser.

---

## Sample Credentials for Testing

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Candidate** | `demo_candidate` | `Password@123` | Testing live voice interviews, resumes, roadmaps |
| **Admin** | `admin` | `Admin@123` | Django Admin inspection at `/admin/` |

---

## License

This project is developed as an academic final-year Computer Science & Engineering capstone project. Free to use for educational and research purposes.
