#!/usr/bin/env python3
"""
Generate English explanations and example sentences for Dutch vocabulary words.

Usage:
    python3 generate_explanations.py vocab/lesson1.json
    python3 generate_explanations.py vocab/lesson2.json
    python3 generate_explanations.py vocab/lesson1.json --overwrite

Requires:
    GOOGLE_API_KEY env var  (Gemini Flash 2.5, free tier)
    pip install google-generativeai

Output:
    explanation/lesson1.json  (keyed by word id)
"""

from google import genai
import json
import os
import sys
import time
from pathlib import Path

MODEL      = "gemini-2.5-flash"
BATCH_SIZE = 20

SYSTEM = (
    "You are a Dutch language teacher. For each Dutch word/phrase given, write "
    "a short English explanation (1–2 sentences, plain language) and exactly 2 simple "
    "Dutch example sentences with English translations. Keep sentences at A1–A2 level. "
    "Return valid JSON only — no markdown fences, no extra text."
)

PROMPT_TEMPLATE = """\
Words:
{words_json}

Respond with a JSON object keyed by the word id (as string):
{{
  "<id>": {{
    "explanation": "...",
    "examples": [
      {{"dutch": "...", "english": "..."}},
      {{"dutch": "...", "english": "..."}}
    ]
  }},
  ...
}}"""


def generate_batch(client, batch, attempt=1):
    words_json = json.dumps(
        [{"id": str(w["id"]), "dutch": w["dutch"], "english": w["english"]} for w in batch],
        ensure_ascii=False
    )
    prompt = SYSTEM + "\n\n" + PROMPT_TEMPLATE.format(words_json=words_json)
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        if attempt < 3:
            print(f"    retry (attempt {attempt+1}): {e}")
            time.sleep(3)
            return generate_batch(client, batch, attempt + 1)
        print(f"    failed after 3 attempts: {e}")
        return {str(w["id"]): {"explanation": w["english"], "examples": []} for w in batch}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_explanations.py vocab/lesson1.json [--overwrite]")
        sys.exit(1)

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: set GOOGLE_API_KEY environment variable")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    json_path  = Path(sys.argv[1])
    overwrite  = "--overwrite" in sys.argv
    lesson     = json_path.stem

    output_dir  = Path("explanation")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{lesson}.json"

    existing = {}
    if output_path.exists() and not overwrite:
        existing = json.loads(output_path.read_text(encoding="utf-8"))

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    all_words = [w for s in data["sections"] for w in s["words"]]
    todo = [w for w in all_words if str(w["id"]) not in existing]

    if not todo:
        print(f"All {len(all_words)} words already done. Use --overwrite to regenerate.")
        return

    print(f"Generating explanations for {len(todo)} words ({BATCH_SIZE}/batch)…\n")
    results = dict(existing)

    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i : i + BATCH_SIZE]
        ids   = [w["id"] for w in batch]
        print(f"  Batch {i//BATCH_SIZE + 1}: ids {ids[0]}–{ids[-1]}")
        results.update(generate_batch(client, batch))
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDone. {len(results)} explanations → {output_path}")


if __name__ == "__main__":
    main()
