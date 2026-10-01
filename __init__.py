import os
import json
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in the .env file.")

client = genai.Client(api_key=GEMINI_API_KEY)

# Try models one by one if a model is temporarily unavailable.
MODELS = [
    os.getenv("STORY_MODEL", "gemini-3.6-flash"),
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
]


def create_comic(
    idea: str,
    genre: str = "Adventure",
    audience: str = "General",
    number_of_panels: int = 6,
) -> dict[str, Any]:

    prompt = f"""
You are an expert AI comic story creator.

Create a complete comic based on the following information.

Story Idea:
{idea}

Genre:
{genre}

Audience:
{audience}

Number of Panels:
{number_of_panels}

Return ONLY valid JSON in exactly this format:

{{
  "outline": "A short story outline",
  "characters": [
    {{
      "name": "Character name",
      "role": "Character role",
      "description": "Short character description"
    }}
  ],
  "story": "Complete comic story",
  "panels": [
    {{
      "panel": 1,
      "scene": "Scene description",
      "dialogue": "Dialogue",
      "caption": "Caption or narration"
    }}
  ]
}}

Make the story creative, clear and suitable for the selected audience.
Make exactly {number_of_panels} comic panels.
"""

    last_error = None

    # Remove duplicate model names
    models_to_try = list(dict.fromkeys(MODELS))

    for model in models_to_try:

        # Retry temporary server errors twice
        for attempt in range(2):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=5000,
                        response_mime_type="application/json",
                    ),
                )

                if not response.text:
                    raise RuntimeError(
                        f"{model} returned an empty response."
                    )

                result = json.loads(response.text)

                return {
                    "idea": idea,
                    "genre": genre,
                    "audience": audience,
                    "number_of_panels": number_of_panels,
                    "outline": result.get("outline", ""),
                    "characters": result.get("characters", []),
                    "story": result.get("story", ""),
                    "panels": result.get("panels", []),
                }

            except Exception as e:
                last_error = e
                error_text = str(e)

                # Retry only temporary availability/server errors
                if "503" in error_text or "UNAVAILABLE" in error_text:
                    if attempt == 0:
                        time.sleep(2)
                        continue

                # Try the next model
                break

    raise RuntimeError(
        f"All Gemini models are temporarily unavailable. "
        f"Last error: {last_error}"
    )