import time
import streamlit as st
import database
import doc_parser
import ai_engine

QUIZ_BOOK_FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect x='8' y='6' width='44' height='52' rx='6' fill='%234f46e5'/%3E"
    "%3Crect x='14' y='10' width='34' height='44' rx='3' fill='%23eef2ff'/%3E"
    "%3Cline x1='20' y1='20' x2='42' y2='20' stroke='%2394a3b8' stroke-width='3' stroke-linecap='round'/%3E"
    "%3Cline x1='20' y1='28' x2='38' y2='28' stroke='%2394a3b8' stroke-width='3' stroke-linecap='round'/%3E"
    "%3Ccircle cx='44' cy='46' r='13' fill='%237c3aed'/%3E"
    "%3Ctext x='44' y='51' text-anchor='middle' fill='%23ffffff' font-family='Arial,sans-serif' font-size='15' font-weight='bold'%3EQ%3C/text%3E"
    "%3C/svg%3E"
)

# Page configuration
st.set_page_config(
    page_title="Online Quiz Studio",
    page_icon=QUIZ_BOOK_FAVICON,
    layout="centered",
)

# Initialize database schema
database.init_db()

# Pre-defined quiz topics
PREDEFINED_TOPICS = [
    "Python Programming",
    "Data Structures & Algorithms",
    "Database Management Systems (DBMS)",
    "Operating Systems",
    "Computer Networks",
    "Object-Oriented Programming (OOP)",
    "Artificial Intelligence & Machine Learning",
    "Web Development Basics",
]

QUESTION_TIME_LIMIT = 60  # Advance mode per-question countdown duration in seconds

# Default session state values
SESSION_DEFAULTS = {
    "splash_shown": False,
    "current_user": None,
    "active_page": "main",  # "main" or "profile"
    "home_section": "Topic-Wise Quiz",
    "quiz_active": False,
    "quiz_completed": False,
    "questions": [],
    "current_q": 0,
    "score": 0,
    "answered": False,
    "selected_option": None,
    "score_saved": False,
    "difficulty": "Basic",
    "q_start_time": None,
    "quiz_meta": {"mode": "", "source": "", "difficulty": "Basic"},
}

for key, default_value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


def render_avatar_html(user: dict, size_px: int = 72) -> str:
    """Return circular avatar HTML for a user profile photo or fallback monogram."""
    photo_data = (user or {}).get("profile_photo", "")
    if photo_data:
        return (
            f'<img src="{photo_data}" alt="Profile Photo" '
            f'style="width:{size_px}px;height:{size_px}px;border-radius:50%;'
            f'object-fit:cover;border:2px solid #6366f1;" />'
        )

    full_name = ((user or {}).get("full_name") or "U").strip()
    initials = "".join(part[0].upper() for part in full_name.split()[:2]) or "U"
    font_size = max(14, int(size_px * 0.36))
    return (
        f'<div style="width:{size_px}px;height:{size_px}px;border-radius:50%;'
        f'background:rgba(99,102,241,0.18);border:2px solid #6366f1;color:#6366f1;'
        f'font-weight:700;display:flex;align-items:center;justify-content:center;'
        f'font-size:{font_size}px;">{initials}</div>'
    )


# --- STARTUP ANIMATED SPLASH SCREEN (2.5 Seconds) ---
if not st.session_state.splash_shown:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"], [data-testid="stHeader"] {
                display: none !important;
            }
            @keyframes floatPulse {
                0% { transform: translateY(0px) scale(1); filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.5)); }
                50% { transform: translateY(-12px) scale(1.1); filter: drop-shadow(0 0 28px rgba(129, 140, 248, 0.95)); }
                100% { transform: translateY(0px) scale(1); filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.5)); }
            }
            @keyframes spinRing {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes loadingBar {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            .splash-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 75vh;
                text-align: center;
            }
            .icon-wrapper {
                position: relative;
                width: 120px;
                height: 120px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 24px;
            }
            .glow-ring {
                position: absolute;
                width: 115px;
                height: 115px;
                border-radius: 50%;
                border: 4px solid transparent;
                border-top-color: #6366f1;
                border-right-color: #a855f7;
                animation: spinRing 1.2s linear infinite;
            }
            .splash-emblem {
                font-size: 2.2rem;
                font-weight: 800;
                letter-spacing: 1px;
                color: #818cf8;
                animation: floatPulse 1.6s ease-in-out infinite;
            }
            .splash-title {
                font-size: 2rem;
                font-weight: 800;
                letter-spacing: 0.5px;
                margin-bottom: 6px;
            }
            .splash-sub {
                font-size: 0.95rem;
                opacity: 0.75;
                margin-bottom: 22px;
            }
            .bar-track {
                width: 240px;
                height: 6px;
                background: rgba(148, 163, 184, 0.25);
                border-radius: 999px;
                overflow: hidden;
            }
            .bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #6366f1, #a855f7);
                border-radius: 999px;
                animation: loadingBar 2.4s ease-in-out forwards;
            }
        </style>
        <div class="splash-container">
            <div class="icon-wrapper">
                <div class="glow-ring"></div>
                <div class="splash-emblem">OQS</div>
            </div>
            <div class="splash-title">Online Quiz Studio</div>
            <div class="splash-sub">Preparing smart assessments and student portal...</div>
            <div class="bar-track">
                <div class="bar-fill"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(2.5)
    st.session_state.splash_shown = True
    st.rerun()


def apply_dynamic_theme(is_advance: bool):
    """Apply smooth theme styling for Basic mode and animated red danger styling for Advance mode."""
    base_transition = """
    <style>
        .stApp, [data-testid="stSidebar"], [data-testid="stHeader"],
        .stButton > button, [data-testid="stVerticalBlockBorderWrapper"] {
            transition: background 0.65s ease, background-color 0.65s ease,
                        color 0.45s ease, border-color 0.55s ease, box-shadow 0.55s ease !important;
        }
        .mode-subtext {
            font-size: 0.9rem;
            opacity: 0.85;
            margin-top: -6px;
            margin-bottom: 12px;
        }
    """

    if not is_advance:
        st.markdown(
            base_transition
            + """
            [data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 12px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return

    # Advance Mode: Red Danger Theme + Animated Danger Cards, Buttons, and Icons
    st.markdown(
        base_transition
        + """
        @keyframes dangerPulse {
            0% { box-shadow: 0 0 8px rgba(239, 68, 68, 0.35), inset 0 0 8px rgba(220, 38, 38, 0.15); border-color: #dc2626; }
            50% { box-shadow: 0 0 22px rgba(239, 68, 68, 0.85), inset 0 0 16px rgba(220, 38, 38, 0.35); border-color: #f87171; }
            100% { box-shadow: 0 0 8px rgba(239, 68, 68, 0.35), inset 0 0 8px rgba(220, 38, 38, 0.15); border-color: #dc2626; }
        }

        @keyframes dangerShake {
            0%, 100% { transform: translateX(0) scale(1); }
            25% { transform: translateX(-2px) rotate(-4deg) scale(1.08); }
            75% { transform: translateX(2px) rotate(4deg) scale(1.08); }
        }

        @keyframes sirenBlink {
            0%, 100% { opacity: 1; text-shadow: 0 0 10px #ef4444; }
            50% { opacity: 0.45; text-shadow: none; }
        }

        .stApp {
            background: radial-gradient(circle at top, #2d080c 0%, #140305 60%, #090102 100%) !important;
            color: #fee2e2 !important;
        }

        [data-testid="stHeader"] {
            background: rgba(20, 3, 5, 0.75) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #240609 0%, #110204 100%) !important;
            border-right: 1px solid rgba(239, 68, 68, 0.45) !important;
        }

        [data-testid="stSidebar"] * {
            color: #fecaca !important;
        }

        h1, h2, h3, p, label, .stMarkdown {
            color: #fef2f2 !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(145deg, rgba(69, 10, 10, 0.65), rgba(24, 4, 6, 0.85)) !important;
            border: 1.5px solid #ef4444 !important;
            border-radius: 14px !important;
            animation: dangerPulse 2.2s infinite ease-in-out !important;
            position: relative;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
            color: #ffffff !important;
            border: 1px solid #f87171 !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 0.4px;
            box-shadow: 0 4px 15px rgba(220, 38, 38, 0.45) !important;
        }

        .stButton > button[kind="primary"]::before {
            content: "🚨 ";
            display: inline-block;
            animation: dangerShake 1.1s infinite ease-in-out;
        }

        .stButton > button[kind="secondary"] {
            background: rgba(69, 10, 10, 0.6) !important;
            color: #fecaca !important;
            border: 1px solid #ef4444 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 0 24px rgba(248, 113, 113, 0.85) !important;
            transform: translateY(-1px);
        }

        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #ef4444, #f97316) !important;
        }

        .danger-banner {
            background: rgba(153, 27, 27, 0.35);
            border: 1px solid #ef4444;
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            animation: dangerPulse 2s infinite;
        }

        .danger-icon-anim {
            display: inline-block;
            animation: dangerShake 0.9s infinite ease-in-out;
            font-size: 1.2rem;
        }

        .timer-box {
            background: linear-gradient(90deg, rgba(185, 28, 28, 0.45), rgba(69, 10, 10, 0.8));
            border: 1.5px solid #f87171;
            border-radius: 10px;
            padding: 10px 16px;
            margin-bottom: 14px;
            text-align: center;
            font-size: 1.1rem;
            font-weight: 700;
            color: #fecaca;
            animation: dangerPulse 1.5s infinite;
        }

        .siren-text {
            animation: sirenBlink 1s infinite;
            color: #fca5a5;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def go_to_next_question():
    """Advance to the next question and reset the per-question timer."""
    if st.session_state.current_q + 1 < len(st.session_state.questions):
        st.session_state.current_q += 1
        st.session_state.answered = False
        st.session_state.selected_option = None
        st.session_state.q_start_time = time.time()
    else:
        st.session_state.quiz_completed = True


def start_new_quiz(questions: list, mode: str, source: str, difficulty: str):
    """Initialize a new active quiz session."""
    st.session_state.active_page = "main"
    st.session_state.quiz_active = True
    st.session_state.quiz_completed = False
    st.session_state.questions = questions
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.selected_option = None
    st.session_state.score_saved = False
    st.session_state.q_start_time = time.time()
    st.session_state.quiz_meta = {"mode": mode, "source": source, "difficulty": difficulty}


def reset_to_home(target_section: str = "Topic-Wise Quiz"):
    """Reset active quiz state and return to the requested home section."""
    st.session_state.active_page = "main"
    st.session_state.quiz_active = False
    st.session_state.quiz_completed = False
    st.session_state.questions = []
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.selected_option = None
    st.session_state.score_saved = False
    st.session_state.q_start_time = None
    st.session_state.home_section = target_section


@st.fragment(run_every=1)
def render_sidebar_timer():
    """Render live 59-to-0 countdown in the sidebar during Advance mode."""
    if st.session_state.q_start_time is None:
        st.session_state.q_start_time = time.time()

    if st.session_state.answered:
        timer_label = "Paused"
    else:
        elapsed = int(time.time() - st.session_state.q_start_time)
        remaining = max(0, (QUESTION_TIME_LIMIT - 1) - elapsed)
        timer_label = f"{remaining:02d}s"

    st.markdown(
        f"""
        <div class="danger-banner">
            <span><span class="danger-icon-anim">⚠️</span> <b>ADVANCE DANGER</b></span>
            <span class="siren-text">{timer_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.fragment(run_every=1)
def render_question_timer():
    """Render live 59-to-0 countdown per question and auto-advance at zero."""
    if not st.session_state.quiz_active or st.session_state.quiz_completed:
        return

    if st.session_state.q_start_time is None:
        st.session_state.q_start_time = time.time()

    if st.session_state.answered:
        st.markdown(
            """
            <div class="timer-box">
                <span class="danger-icon-anim">🚨</span>
                &nbsp; ANSWER SUBMITTED — PROCEED TO NEXT QUESTION &nbsp;
                <span class="danger-icon-anim">🔥</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    elapsed = int(time.time() - st.session_state.q_start_time)
    remaining = max(0, (QUESTION_TIME_LIMIT - 1) - elapsed)

    st.markdown(
        f"""
        <div class="timer-box">
            <span class="danger-icon-anim">🚨</span>
            &nbsp; QUESTION TIMER: <span class="siren-text">00:{remaining:02d} sec</span> &nbsp;
            <span class="danger-icon-anim">🔥</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if elapsed >= QUESTION_TIME_LIMIT:
        go_to_next_question()
        st.rerun()


# --- SIDEBAR ---
with st.sidebar:
    user = st.session_state.current_user

    if user is not None:
        s_col1, s_col2 = st.columns([1, 3])
        with s_col1:
            st.markdown(render_avatar_html(user, size_px=44), unsafe_allow_html=True)
        with s_col2:
            if st.button(
                user["full_name"],
                use_container_width=True,
                disabled=st.session_state.quiz_active,
                help="Open your profile, update details, and view growth analytics",
            ):
                st.session_state.active_page = "profile"
                st.rerun()

        if st.session_state.active_page == "profile":
            if st.button("Back to Quiz Page", use_container_width=True):
                st.session_state.active_page = "main"
                st.rerun()

        st.divider()

    st.header("Quiz Settings")
    num_questions = st.slider("Number of Questions", min_value=3, max_value=15, value=5)

    st.radio(
        "Difficulty Level",
        options=["Basic", "Advance"],
        key="difficulty",
        horizontal=True,
        disabled=st.session_state.quiz_active,
        help="Basic: Standard questions | Advance: Hard questions with a 60-second per-question timer",
    )

    if st.session_state.difficulty == "Advance":
        if st.session_state.quiz_active and not st.session_state.quiz_completed:
            render_sidebar_timer()
        else:
            st.markdown(
                """
                <div class="danger-banner">
                    <span><span class="danger-icon-anim">⚠️</span> <b>ADVANCE DANGER</b></span>
                    <span class="siren-text">60s / Q</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.session_state.quiz_active:
        st.divider()
        if st.button("Exit Current Quiz", use_container_width=True):
            reset_to_home()
            st.rerun()

    if user is not None and not st.session_state.quiz_active:
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.active_page = "main"
            reset_to_home()
            st.rerun()

# Apply active theme
is_advance_mode = st.session_state.difficulty == "Advance"
apply_dynamic_theme(is_advance_mode)


# --- VIEW 0: ACCOUNT ACCESS / REGISTRATION ---
if st.session_state.current_user is None:
    st.title("Online Quiz Studio")
    st.caption("Sign in with your 11-digit roll number or create a new student profile.")

    auth_tab1, auth_tab2 = st.tabs(["Existing Account", "New Account"])

    with auth_tab1:
        with st.container(border=True):
            st.subheader("Sign In to Existing Account")
            with st.form("login_roll_form"):
                login_roll = st.text_input(
                    "11-Digit Roll Number *",
                    max_chars=11,
                    placeholder="Enter your 11-digit numeric roll number",
                )
                login_btn = st.form_submit_button("Sign In", type="primary", use_container_width=True)

                if login_btn:
                    try:
                        found_user = database.get_user_by_roll_number(login_roll)
                        if found_user:
                            st.session_state.current_user = found_user
                            st.session_state.active_page = "main"
                            st.rerun()
                        else:
                            st.error("No account found with this roll number. Please register under New Account.")
                    except Exception as e:
                        st.error(str(e))

    with auth_tab2:
        with st.container(border=True):
            st.subheader("Create New Account")
            with st.form("create_account_form"):
                reg_roll = st.text_input(
                    "Roll Number (Strictly 11 Digits) *",
                    max_chars=11,
                    placeholder="e.g., 23010100123",
                )
                reg_fullname = st.text_input("Full Name *", placeholder="e.g., John Doe")
                reg_email = st.text_input("Email Address *", placeholder="e.g., student@example.com")
                reg_course = st.text_input("Course / Branch (Optional)", placeholder="e.g., BCA / B.Tech CSE")
                reg_photo = st.file_uploader(
                    "Profile Photo (Optional - JPG, JPEG, PNG, WEBP)",
                    type=["jpg", "jpeg", "png", "webp"],
                )
                create_btn = st.form_submit_button("Create Account", type="primary", use_container_width=True)

                if create_btn:
                    try:
                        photo_b64 = database.encode_profile_photo(reg_photo) if reg_photo else ""
                        new_user = database.create_user(
                            roll_number=reg_roll,
                            full_name=reg_fullname,
                            email=reg_email,
                            course=reg_course,
                            profile_photo=photo_b64,
                        )
                        st.session_state.current_user = new_user
                        st.session_state.active_page = "main"
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


# --- VIEW 1: DEDICATED PROFILE, UPDATE & SUBJECT-WISE GROWTH PAGE ---
elif st.session_state.active_page == "profile":
    active_user = st.session_state.current_user

    col_avatar, col_title, col_back = st.columns([1, 3, 1])
    with col_avatar:
        st.markdown(render_avatar_html(active_user, size_px=80), unsafe_allow_html=True)
    with col_title:
        st.title(active_user["full_name"])
        st.caption(
            f"Roll Number (Private): **{active_user['roll_number']}** | Member since: {active_user['created_at']}"
        )
    with col_back:
        st.write("")
        if st.button("Back to Quizzes", type="primary", use_container_width=True):
            st.session_state.active_page = "main"
            st.rerun()

    with st.container(border=True):
        st.subheader("Profile Photo and Personal Details")
        with st.form("profile_page_edit_form"):
            c1, c2 = st.columns(2)
            with c1:
                upd_name = st.text_input("Full Name *", value=active_user["full_name"])
                upd_course = st.text_input("Course / Branch", value=active_user.get("course", ""))
            with c2:
                upd_email = st.text_input("Email Address *", value=active_user["email"])
                st.text_input("Roll Number (Private and Fixed)", value=active_user["roll_number"], disabled=True)

            upd_photo = st.file_uploader(
                "Upload or Change Profile Photo (JPG, JPEG, PNG, WEBP)",
                type=["jpg", "jpeg", "png", "webp"],
            )
            remove_photo = st.checkbox(
                "Remove current profile photo",
                value=False,
                disabled=not bool(active_user.get("profile_photo")),
            )

            if st.form_submit_button("Save Profile Changes", type="primary", use_container_width=True):
                try:
                    new_photo_value = None
                    if remove_photo:
                        new_photo_value = ""
                    elif upd_photo is not None:
                        new_photo_value = database.encode_profile_photo(upd_photo)

                    updated_user = database.update_user_profile(
                        user_id=active_user["id"],
                        full_name=upd_name,
                        email=upd_email,
                        course=upd_course,
                        profile_photo=new_photo_value,
                    )
                    st.session_state.current_user = updated_user
                    st.success("Profile details and photo have been updated.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with st.container(border=True):
        st.subheader("Personal Average Score and Subject-Wise Growth")
        stats = database.get_user_growth_stats(active_user["id"])

        if stats["total_quizzes"] == 0:
            st.info("No quiz attempts recorded yet. Complete a quiz to view your subject-wise growth.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Quizzes", stats["total_quizzes"])
            m2.metric("Average Score", f"{stats['avg_accuracy']}%")
            m3.metric(
                "Overall Growth",
                f"{stats['overall_growth']:+.1f}%" if stats["total_quizzes"] >= 2 else "Baseline",
                delta=f"{stats['overall_growth']:+.1f}%" if stats["total_quizzes"] >= 2 else None,
            )
            m4.metric("Total Correct", f"{stats['total_correct']} / {stats['total_questions']}")

            st.divider()
            st.markdown("#### Subject / Topic-Wise Total Growth")
            subject_table = [
                {
                    "Subject / Topic": s["Subject / Topic"],
                    "Attempts": s["Attempts"],
                    "Average Score (%)": f"{s['Average Score (%)']}%",
                    "Best Score (%)": f"{s['Best Score (%)']}%",
                    "First vs Latest": s["First vs Latest"],
                    "Total Growth": s["Total Growth"],
                }
                for s in stats["subjects"]
            ]
            st.dataframe(subject_table, use_container_width=True, hide_index=True)

            st.markdown("#### Subject-Wise Average Performance (%)")
            chart_data = {s["Subject / Topic"]: s["raw_avg"] for s in stats["subjects"]}
            st.bar_chart(chart_data)

    with st.container(border=True):
        st.subheader("My Quiz Attempt History")
        my_scores = database.get_user_scores(active_user["id"])
        if my_scores:
            formatted_my_scores = [
                {
                    "Mode": r["quiz_mode"],
                    "Subject / File": r["topic_or_file"],
                    "Score": f"{r['score']} / {r['total_questions']}",
                    "Accuracy": f"{round((r['score'] / r['total_questions']) * 100)}%",
                    "Date & Time": r["attempted_at"],
                }
                for r in my_scores
            ]
            st.dataframe(formatted_my_scores, use_container_width=True, hide_index=True)
        else:
            st.info("You have not completed any quizzes yet.")


# --- VIEW 2: MAIN QUIZ HOME SCREEN ---
elif not st.session_state.quiz_active:
    if is_advance_mode:
        st.markdown(
            '<h1><span class="danger-icon-anim">🔥</span> Online Quiz Studio — ADVANCE MODE</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="mode-subtext"><span class="danger-icon-anim">⚠️</span> '
            "Danger Mode Active: Challenging questions with a 60-second per-question timer.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.title("Online Quiz Studio")
        st.markdown(
            '<div class="mode-subtext">Select a topic or upload study documents or images to generate an instant quiz.</div>',
            unsafe_allow_html=True,
        )

    nav_options = [
        "Topic-Wise Quiz",
        "Document Upload Quiz",
        "Image Upload Quiz",
        "Global Scoreboard",
    ]
    st.radio(
        "Navigation",
        options=nav_options,
        key="home_section",
        horizontal=True,
        label_visibility="collapsed",
    )

    section = st.session_state.home_section

    # SECTION 1: Pre-defined Topics
    if section == "Topic-Wise Quiz":
        with st.container(border=True):
            if is_advance_mode:
                st.markdown(
                    '<span class="danger-icon-anim">⚠️</span> <b>DANGER ZONE — HARD TOPIC CHALLENGE</b>',
                    unsafe_allow_html=True,
                )
            st.subheader("Select a Pre-Defined Topic")
            selected_topic = st.selectbox("Subject / Topic:", PREDEFINED_TOPICS)

            btn_label = f"Start {st.session_state.difficulty} Quiz"
            if st.button(btn_label, type="primary", use_container_width=True):
                with st.spinner(
                    f"Generating {num_questions} {st.session_state.difficulty} questions on '{selected_topic}'..."
                ):
                    try:
                        questions = ai_engine.generate_topic_quiz(
                            selected_topic, num_questions, difficulty=st.session_state.difficulty
                        )
                        start_new_quiz(
                            questions,
                            mode="Topic-Wise",
                            source=selected_topic,
                            difficulty=st.session_state.difficulty,
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # SECTION 2: Document Upload (PDF / DOCX)
    elif section == "Document Upload Quiz":
        with st.container(border=True):
            if is_advance_mode:
                st.markdown(
                    '<span class="danger-icon-anim">⚠️</span> <b>DANGER ZONE — DEEP DOCUMENT SCAN</b>',
                    unsafe_allow_html=True,
                )
            st.subheader("Upload a Study Document (PDF / DOCX)")
            uploaded_doc = st.file_uploader(
                "Supported document formats: PDF, DOCX",
                type=["pdf", "docx"],
            )

            if uploaded_doc is not None:
                st.info(f"Selected Document: **{uploaded_doc.name}**")
                if st.button(
                    f"Scan and Start {st.session_state.difficulty} Quiz",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner("Scanning document and generating quiz questions..."):
                        try:
                            content_type, content = doc_parser.parse_uploaded_file(uploaded_doc)
                            questions = ai_engine.generate_doc_quiz(
                                content_type, content, num_questions, difficulty=st.session_state.difficulty
                            )
                            start_new_quiz(
                                questions,
                                mode="Document Scan",
                                source=uploaded_doc.name,
                                difficulty=st.session_state.difficulty,
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    # SECTION 3: Dedicated Image Upload (JPG, JPEG, PNG, WEBP)
    elif section == "Image Upload Quiz":
        with st.container(border=True):
            if is_advance_mode:
                st.markdown(
                    '<span class="danger-icon-anim">⚠️</span> <b>DANGER ZONE — IMAGE VISION SCAN</b>',
                    unsafe_allow_html=True,
                )
            st.subheader("Upload Notes, Handwritten Page, or Diagram Image")
            uploaded_image = st.file_uploader(
                "Upload Image (JPG, JPEG, PNG, WEBP)",
                type=["jpg", "jpeg", "png", "webp"],
                key="dedicated_image_uploader",
            )

            if uploaded_image is not None:
                st.success(f"Uploaded Image: **{uploaded_image.name}**")
                st.image(uploaded_image, caption="Uploaded Image Preview", width=360)

                if st.button(
                    f"Scan Image and Start {st.session_state.difficulty} Quiz",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner("Scanning image and generating quiz questions..."):
                        try:
                            content_type, content = doc_parser.parse_uploaded_file(uploaded_image)
                            questions = ai_engine.generate_doc_quiz(
                                content_type, content, num_questions, difficulty=st.session_state.difficulty
                            )
                            start_new_quiz(
                                questions,
                                mode="Image Scan",
                                source=uploaded_image.name,
                                difficulty=st.session_state.difficulty,
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    # SECTION 4: Global Scoreboard (Roll numbers remain private)
    elif section == "Global Scoreboard":
        with st.container(border=True):
            st.subheader("Global Scoreboard")
            scores = database.get_all_scores()
            if scores:
                formatted_scores = [
                    {
                        "Student": row["student_name"],
                        "Course": row["course"],
                        "Mode": row["quiz_mode"],
                        "Topic / File": row["topic_or_file"],
                        "Score": f"{row['score']} / {row['total_questions']}",
                        "Accuracy": f"{round((row['score'] / row['total_questions']) * 100)}%",
                        "Date & Time": row["attempted_at"],
                    }
                    for row in scores
                ]
                st.dataframe(formatted_scores, use_container_width=True, hide_index=True)
            else:
                st.info("No quiz scores recorded yet. Complete a quiz to appear on the scoreboard.")


# --- VIEW 3: ACTIVE QUIZ SCREEN ---
elif st.session_state.quiz_active and not st.session_state.quiz_completed:
    if is_advance_mode:
        render_question_timer()

    questions = st.session_state.questions
    idx = st.session_state.current_q
    total = len(questions)
    q = questions[idx]

    st.progress((idx + 1) / total)
    st.caption(
        f"Candidate: **{st.session_state.current_user['full_name']}** | "
        f"Question **{idx + 1}** of **{total}** | "
        f"Level: **{st.session_state.difficulty}** | "
        f"Source: **{st.session_state.quiz_meta['source']}**"
    )

    with st.container(border=True):
        if is_advance_mode:
            st.markdown(
                f'<span class="danger-icon-anim">⚠️</span> <b>DANGER QUESTION #{idx + 1}</b>',
                unsafe_allow_html=True,
            )
        st.subheader(f"Q{idx + 1}. {q['question']}")

        choice = st.radio(
            "Select an option:",
            options=q["options"],
            index=None,
            key=f"radio_q_{idx}",
            disabled=st.session_state.answered,
        )

        if not st.session_state.answered:
            col_sub, col_skip = st.columns([2, 1])
            with col_sub:
                submit_clicked = st.button("Submit Answer", type="primary", use_container_width=True)
            with col_skip:
                skip_clicked = st.button("Skip Question", type="secondary", use_container_width=True)

            if submit_clicked:
                if choice is None:
                    st.warning("Please select an option before submitting, or skip the question.")
                else:
                    st.session_state.answered = True
                    st.session_state.selected_option = choice
                    if choice == q["correct_answer"]:
                        st.session_state.score += 1
                    st.rerun()

            if skip_clicked:
                go_to_next_question()
                st.rerun()
        else:
            if st.session_state.selected_option == q["correct_answer"]:
                st.success("Correct Answer.")
            else:
                st.error(f"Incorrect Answer. Correct answer: **{q['correct_answer']}**")

            st.info(f"Explanation: {q['explanation']}")

            if idx + 1 < total:
                if st.button("Next Question", type="primary"):
                    go_to_next_question()
                    st.rerun()
            else:
                if st.button("Finish and View Scorecard", type="primary"):
                    st.session_state.quiz_completed = True
                    st.rerun()


# --- VIEW 4: FINAL SCORECARD ---
elif st.session_state.quiz_completed:
    active_user = st.session_state.current_user
    total = len(st.session_state.questions)
    score = st.session_state.score
    accuracy = round((score / total) * 100)
    mode_label = f"{st.session_state.quiz_meta['mode']} ({st.session_state.difficulty})"

    if not st.session_state.score_saved:
        database.save_score(
            user_id=active_user["id"],
            student_name=active_user["full_name"],
            quiz_mode=mode_label,
            topic_or_file=st.session_state.quiz_meta["source"],
            score=score,
            total_questions=total,
        )
        st.session_state.score_saved = True

    with st.container(border=True):
        if accuracy >= 60:
            st.balloons()
        st.success(f"Quiz completed, **{active_user['full_name']}**. Your score has been saved.")

        col1, col2, col3 = st.columns(3)
        col1.metric("Final Score", f"{score} / {total}")
        col2.metric("Accuracy", f"{accuracy}%")
        col3.metric("Level", st.session_state.difficulty)

    st.divider()

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Return to Main Page", type="primary", use_container_width=True):
            reset_to_home(target_section="Topic-Wise Quiz")
            st.rerun()
    with btn_col2:
        if st.button("See Global Scoreboard", type="secondary", use_container_width=True):
            reset_to_home(target_section="Global Scoreboard")
            st.rerun()