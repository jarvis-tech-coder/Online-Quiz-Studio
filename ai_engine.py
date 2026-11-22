import json
import os
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env
load_dotenv(override=True)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Verified fast Gemini models ordered by primary preference and fallback priority
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
]

DEFAULT_TIMEOUT_MS = 15000


def _get_client() -> genai.Client:
    """Initialize and return a Google GenAI client with a fast request timeout."""
    if not API_KEY or API_KEY == "yahan_apni_api_key_paste_karein":
        raise ValueError(
            "GEMINI_API_KEY is missing. Please configure a valid API key in your .env file."
        )
    return genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT_MS),
    )


def _generate_with_fallback(
    client: genai.Client,
    contents,
    temperature: float = 0.8,
) -> str:
    """Request JSON output across configured models, failing over immediately on errors."""
    last_error = None

    for model_name in MODELS:
        print(f"Trying model: {model_name}...", flush=True)
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
            if response.text:
                print(f"Success with: {model_name}", flush=True)
                return response.text
        except Exception as exc:
            last_error = exc
            err_msg = str(exc)
            print(f"Model {model_name} skipped ({type(exc).__name__})", flush=True)
            if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg:
                raise ValueError(
                    "Invalid GEMINI_API_KEY. Please verify your API key in the .env file."
                )
            continue

    raise RuntimeError(
        f"All configured Gemini models are currently experiencing high traffic. "
        f"Please try again shortly. (Last error: {last_error})"
    )


def _get_difficulty_instruction(difficulty: str) -> str:
    """Return prompt instructions tailored to the selected difficulty level."""
    if difficulty == "Advance":
        return (
            "DIFFICULTY: ADVANCE (HARD). Generate challenging, deep conceptual, scenario-based, "
            "or edge-case questions. Make all four options closely related and nuanced so only "
            "someone with strong mastery can answer accurately. Avoid surface-level definitions."
        )
    return (
        "DIFFICULTY: BASIC (NORMAL). Generate clear, foundational, and straightforward conceptual "
        "questions suitable for standard review and core comprehension."
    )


def _parse_quiz_json(raw_text: str) -> list:
    """Parse, validate, and shuffle options for the JSON array returned by the model."""
    if not raw_text:
        raise ValueError("Empty response received from the Gemini API. Please try again.")

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    questions = json.loads(cleaned)

    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("No valid questions list was returned by the model. Please try again.")

    required_keys = ("question", "options", "correct_answer", "explanation")
    for question_item in questions:
        if not all(key in question_item for key in required_keys):
            raise ValueError("Generated question object is missing required fields.")
        if not isinstance(question_item["options"], list) or len(question_item["options"]) != 4:
            raise ValueError("Each generated question must contain exactly four options.")
        random.shuffle(question_item["options"])

    return questions


def generate_topic_quiz(topic: str, num_questions: int = 5, difficulty: str = "Basic") -> list:
    """Generate randomized multiple-choice questions for a given subject or topic."""
    client = _get_client()
    seed_hint = random.randint(1000, 9999)
    diff_guide = _get_difficulty_instruction(difficulty)

    prompt = f"""
    You are an expert assessment question generator. Generate {num_questions} unique, randomized
    multiple-choice questions (MCQs) on the topic: "{topic}".
    Variation seed: {seed_hint} (ensure distinct questions covering varied concepts within the topic).
    {diff_guide}

    Rules:
    1. Each question must have exactly 4 distinct options.
    2. "correct_answer" must match one of the strings in "options" verbatim.
    3. Keep "explanation" concise (1-2 sentences).

    Return strictly a JSON array following this schema:
    [
      {{
        "question": "Question text here?",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer": "Option 1",
        "explanation": "Concise explanation of why Option 1 is correct."
      }}
    ]
    """

    raw_text = _generate_with_fallback(client, prompt, temperature=0.8)
    return _parse_quiz_json(raw_text)


def generate_doc_quiz(
    content_type: str,
    content,
    num_questions: int = 5,
    difficulty: str = "Basic",
) -> list:
    """Generate multiple-choice questions grounded in parsed document text or an uploaded image."""
    client = _get_client()
    diff_guide = _get_difficulty_instruction(difficulty)

    base_instructions = f"""
    Carefully analyze the provided document or image content and generate {num_questions}
    multiple-choice questions (MCQs) strictly grounded in the facts, concepts, or information
    present in it.
    {diff_guide}

    Rules:
    1. Each question must have exactly 4 distinct options.
    2. "correct_answer" must match one of the strings in "options" verbatim.
    3. Keep "explanation" concise (1-2 sentences) referencing the source material.

    Return strictly a JSON array following this schema:
    [
      {{
        "question": "Question text here?",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer": "Option 1",
        "explanation": "Concise explanation based on the source material."
      }}
    ]
    """

    if content_type == "image":
        contents = [base_instructions, content]
    else:
        trimmed_text = str(content)[:25000]
        contents = (
            f"{base_instructions}\n\n"
            f"--- DOCUMENT CONTENT START ---\n{trimmed_text}\n--- DOCUMENT CONTENT END ---"
        )

    raw_text = _generate_with_fallback(client, contents, temperature=0.7)
    return _parse_quiz_json(raw_text)