from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiClient:
    MODEL = "gemini-2.5-flash-lite"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required.")
        self.api_key = api_key
        self._configure()

    def _configure(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
        except ImportError:
            raise ImportError("Install google-generativeai: pip install google-generativeai")

    def summarize(self, prompt: str, temperature: float = 0.3) -> str:
        try:
            model = self._genai.GenerativeModel(
                model_name=self.MODEL,
                generation_config=self._genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                ),
            )
            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            return f"Gemini error: {exc}"

    def summarize_with_image(self, prompt: str, image_path: str) -> str:
        """Send a prompt + image to Gemini Vision."""
        try:
            import PIL.Image
            img = PIL.Image.open(image_path)
            model = self._genai.GenerativeModel(self.MODEL)
            response = model.generate_content([prompt, img])
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini Vision error: %s", exc)
            return f"Gemini Vision error: {exc}"
