import base64
import io
import re
import sqlite3
from datetime import datetime
from PIL import Image, ImageOps

DB_NAME = "quiz_app.db"
AVATAR_SIZE = (240, 240)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _get_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection configured with row mapping."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables and reset legacy schemas that lack roll number support."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(users)")
        existing_user_cols = [row["name"] for row in cursor.fetchall()]
        if "roll_number" not in existing_user_cols:
            cursor.execute("DROP TABLE IF EXISTS scores")
            cursor.execute("DROP TABLE IF EXISTS users")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            course TEXT DEFAULT '',
            email TEXT NOT NULL,
            profile_photo TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row["name"] for row in cursor.fetchall()]
    if "profile_photo" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT DEFAULT ''")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            quiz_mode TEXT NOT NULL,
            topic_or_file TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            attempted_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    conn.commit()
    conn.close()


# --- VALIDATION AND MEDIA HELPERS ---

def validate_roll_number(roll_number: str) -> str:
    """Validate that the roll number is strictly an 11-digit numeric string."""
    clean_roll = str(roll_number).strip()
    if not clean_roll.isdigit() or len(clean_roll) != 11:
        raise ValueError(
            "Roll number must be strictly an 11-digit number (digits 0-9 only, no fewer or more)."
        )
    return clean_roll


def validate_email(email: str) -> str:
    """Validate that a non-empty, properly formatted email address is provided."""
    clean_email = str(email).strip()
    if not clean_email:
        raise ValueError("Email address is required.")
    if not EMAIL_PATTERN.match(clean_email):
        raise ValueError("Please enter a valid email address (e.g., student@example.com).")
    return clean_email


def encode_profile_photo(uploaded_file) -> str:
    """Normalize, crop to a square avatar, and encode an uploaded image as a JPEG data URI."""
    if uploaded_file is None:
        return ""

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image = ImageOps.exif_transpose(image)

        if image.mode in ("RGBA", "LA", "P"):
            rgba_image = image.convert("RGBA")
            background = Image.new("RGB", rgba_image.size, (255, 255, 255))
            background.paste(rgba_image, mask=rgba_image.split()[3])
            image = background
        else:
            image = image.convert("RGB")

        avatar = ImageOps.fit(image, AVATAR_SIZE, method=Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        avatar.save(buffer, format="JPEG", quality=85)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception as exc:
        raise ValueError(f"Unable to process profile photo: {exc}")


# --- USER PROFILE OPERATIONS ---

def create_user(
    roll_number: str,
    full_name: str,
    email: str,
    course: str = "",
    profile_photo: str = "",
) -> dict:
    """Create a new student account using an 11-digit roll number, email, and optional photo."""
    clean_roll = validate_roll_number(roll_number)
    clean_name = str(full_name).strip()
    clean_email = validate_email(email)

    if not clean_name:
        raise ValueError("Full name is required.")

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE roll_number = ?", (clean_roll,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(
            "An account with this roll number already exists. Please sign in under Existing Account."
        )

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute(
        """
        INSERT INTO users (roll_number, full_name, course, email, profile_photo, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (clean_roll, clean_name, str(course).strip(), clean_email, profile_photo or "", created_at),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return get_user_by_id(user_id)


def get_user_by_roll_number(roll_number: str):
    """Fetch a registered user record by their 11-digit roll number."""
    clean_roll = validate_roll_number(roll_number)
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE roll_number = ?", (clean_roll,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    """Fetch a user record by internal primary key ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_profile(
    user_id: int,
    full_name: str,
    email: str,
    course: str = "",
    profile_photo: str = None,
) -> dict:
    """Update profile details and optional avatar photo while keeping score names in sync."""
    clean_name = str(full_name).strip()
    clean_email = validate_email(email)

    if not clean_name:
        raise ValueError("Full name cannot be empty.")

    conn = _get_connection()
    cursor = conn.cursor()

    if profile_photo is not None:
        cursor.execute(
            """
            UPDATE users
            SET full_name = ?, email = ?, course = ?, profile_photo = ?
            WHERE id = ?
            """,
            (clean_name, clean_email, str(course).strip(), profile_photo, user_id),
        )
    else:
        cursor.execute(
            """
            UPDATE users
            SET full_name = ?, email = ?, course = ?
            WHERE id = ?
            """,
            (clean_name, clean_email, str(course).strip(), user_id),
        )

    cursor.execute(
        """
        UPDATE scores
        SET student_name = ?
        WHERE user_id = ?
        """,
        (clean_name, user_id),
    )

    conn.commit()
    conn.close()
    return get_user_by_id(user_id)


# --- SCORE AND GROWTH ANALYTICS ---

def save_score(
    user_id: int,
    student_name: str,
    quiz_mode: str,
    topic_or_file: str,
    score: int,
    total_questions: int,
) -> None:
    """Persist a completed quiz score in the database."""
    conn = _get_connection()
    cursor = conn.cursor()
    attempted_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute(
        """
        INSERT INTO scores (user_id, student_name, quiz_mode, topic_or_file, score, total_questions, attempted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, student_name, quiz_mode, topic_or_file, score, total_questions, attempted_at),
    )
    conn.commit()
    conn.close()


def get_all_scores() -> list:
    """Return global scoreboard entries without exposing private roll numbers or identifiers."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            s.id,
            COALESCE(u.full_name, s.student_name) AS student_name,
            COALESCE(u.course, '-') AS course,
            s.quiz_mode,
            s.topic_or_file,
            s.score,
            s.total_questions,
            s.attempted_at
        FROM scores s
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.id DESC
        """
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_user_scores(user_id: int) -> list:
    """Return quiz attempts belonging strictly to the specified user."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT quiz_mode, topic_or_file, score, total_questions, attempted_at
        FROM scores
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_user_growth_stats(user_id: int) -> dict:
    """Calculate overall accuracy, progression delta, and subject-wise growth for a user."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT quiz_mode, topic_or_file, score, total_questions, attempted_at
        FROM scores
        WHERE user_id = ?
        ORDER BY id ASC
        """,
        (user_id,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not rows:
        return {
            "total_quizzes": 0,
            "total_correct": 0,
            "total_questions": 0,
            "avg_accuracy": 0.0,
            "overall_growth": 0.0,
            "subjects": [],
        }

    percentages = [
        round((row["score"] / row["total_questions"]) * 100, 1)
        if row["total_questions"] > 0
        else 0.0
        for row in rows
    ]

    total_quizzes = len(rows)
    total_correct = sum(row["score"] for row in rows)
    total_questions = sum(row["total_questions"] for row in rows)
    avg_accuracy = round(sum(percentages) / total_quizzes, 1)
    overall_growth = round(percentages[-1] - percentages[0], 1) if total_quizzes >= 2 else 0.0

    subject_scores = {}
    for row, pct in zip(rows, percentages):
        subject = row["topic_or_file"]
        subject_scores.setdefault(subject, []).append(pct)

    subjects_summary = []
    for subject, pct_list in subject_scores.items():
        attempts = len(pct_list)
        subj_avg = round(sum(pct_list) / attempts, 1)
        subj_best = round(max(pct_list), 1)
        subj_growth = round(pct_list[-1] - pct_list[0], 1) if attempts >= 2 else 0.0
        subjects_summary.append(
            {
                "Subject / Topic": subject,
                "Attempts": attempts,
                "Average Score (%)": subj_avg,
                "Best Score (%)": subj_best,
                "First vs Latest": (
                    f"{pct_list[0]}% -> {pct_list[-1]}%" if attempts >= 2 else f"{pct_list[0]}% (1st)"
                ),
                "Total Growth": f"{subj_growth:+.1f}%" if attempts >= 2 else "Baseline",
                "raw_avg": subj_avg,
            }
        )

    return {
        "total_quizzes": total_quizzes,
        "total_correct": total_correct,
        "total_questions": total_questions,
        "avg_accuracy": avg_accuracy,
        "overall_growth": overall_growth,
        "subjects": subjects_summary,
    }