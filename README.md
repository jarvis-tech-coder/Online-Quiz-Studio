# Online Quiz Studio

An AI-powered quiz generation, timed assessment, and student growth analytics web application built with **Python**, **Streamlit**, **Google GenAI SDK (Gemini)**, and **SQLite**.

## Key Features

* **Topic-Wise AI Quiz Generation:** Generate randomized multiple-choice questions (MCQs) with four shuffled options, verified answers, and concise explanations across predefined subjects.
* **Document & Image Quiz Generation:** Upload study documents (`.pdf`, `.docx`) or images (`.jpg`, `.jpeg`, `.png`, `.webp`) of notes, diagrams, or handwritten pages to generate source-grounded quizzes.
* **Dual Difficulty Modes & Dynamic Theming:**
  * **Basic Mode:** Standard quiz flow for foundational learning and practice.
  * **Advance Mode (Danger Mode):** High-difficulty conceptual questions paired with a crimson theme transition, animated danger indicators, a live `59 -> 0` second per-question countdown timer, automatic next-question progression on timeout, and manual question skipping.
* **11-Digit Roll Number Authentication & Privacy:** Students register and sign in using a strictly validated 11-digit numeric roll number and mandatory email address. Roll numbers remain private and are excluded from the public Global Scoreboard.
* **Profile, Avatar & Subject-Wise Growth Analytics:** Dedicated student profile view to update personal details, upload or remove a square-cropped JPEG profile avatar, track overall accuracy and progression delta, and inspect subject-wise growth tables and bar charts.
* **Multi-Model Gemini Fallback:** Routes quiz requests across prioritized Gemini Flash models with a 15-second timeout and strict JSON validation for reliable availability.

## Project Structure

```text
online-quiz-studio/
├── app.py              # Splash screen, auth/profile views, Advance timer & theme, quiz UI, scoreboard
├── ai_engine.py        # Gemini client setup, multi-model fallback, prompts, and JSON quiz parser
├── doc_parser.py       # PDF/DOCX text extraction and PIL image preparation
├── database.py         # SQLite schema, validation, avatar encoding, scores, and growth analytics
├── requirements.txt    # Python package dependencies
├── .env.example        # Sample environment variable template
├── .gitignore          # Ignored files (.env, *.db, venv/, __pycache__/, .vscode/)
└── README.md           # Project documentation

## Tech Stack & Architecture

| Layer | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core application logic, validation, and data handling |
| **Web Framework** | Streamlit | Interactive UI, reactive countdown fragments, and analytics charts |
| **AI & Vision Engine** | Google GenAI SDK (`google-genai`) | Topic, document, and image-based MCQ generation with multi-model fallback |
| **Database** | SQLite (`sqlite3`) | Local relational storage (`quiz_app.db`) for student profiles, avatars, and scores |
| **Document Parsers** | `pypdf` & `python-docx` | Text extraction from uploaded `.pdf` and `.docx` study materials |
| **Image Processing** | Pillow (`PIL`) | EXIF normalization and square avatar thumbnail encoding (`240x240` JPEG) |
| **Configuration** | `python-dotenv` | Loads `GEMINI_API_KEY` securely from `.env` |

---

## Prerequisites

Before setting up the project locally, make sure you have:

* **Python 3.10 or higher** installed on your system
* **Git** installed for cloning the repository
* A valid **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

---

## Step-by-Step Local Setup & Installation

### Step 1: Clone the Repository
Open your terminal (PowerShell or Command Prompt) and clone this repository:

```bash
git clone https://github.com/jarvis-tech-coder/Online-Quiz-Studio.git
cd Online-Quiz-Studio

### Step 2: Create & Activate a Virtual Environment
Isolate project dependencies using a Python virtual environment:
python -m venv venv
.\venv\Scripts\Activate.ps1

### Step 3: Install Required Dependencies
Install all required Python packages listed in requirements.txt:
pip install -r requirements.txt

### Step 4: Configure Environment Variables
   * **Create a .env file in the root directory (or copy .env.example):** copy .env.example .env
   * **Open .env and add your Google Gemini API key:** GEMINI_API_KEY=your_actual_gemini_api_key_here

### Step 5: Run the Application
### Start the Streamlit development server: ###
streamlit run app.py

Once started, open your browser and visit:

* Local URL: http://localhost:8501
```

