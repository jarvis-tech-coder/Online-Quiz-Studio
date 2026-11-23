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


Tech Stack
Language: Python
Web Framework: Streamlit
AI SDK & Models: google-genai (Gemini Flash models)
Database: SQLite (sqlite3)
Libraries: pypdf, python-docx, Pillow (PIL), python-dotenv
