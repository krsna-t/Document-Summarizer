

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Optional

logger = logging.getLogger(__name__)


class LlamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    # ── Public methods ────────────────────────────────────────────────────────

    def summarize(self, prompt: str, temperature: float = 0.3) -> str:
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 1024,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except urllib.error.URLError as exc:
            logger.error("Ollama connection error: %s", exc)
            return (
                f"Could not connect to Ollama at {self.base_url}.\n"
                "Make sure Ollama is running: https://ollama.ai\n"
                f"Then pull the model: ollama pull {self.model}"
            )
        except Exception as exc:
            logger.error("Llama error: %s", exc)
            return f"Llama error: {exc}"

    def list_models(self) -> list[str]:
        """Return list of available models in Ollama."""
        req = urllib.request.Request(f"{self.base_url}/api/tags")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5)
            return True
        except Exception:
            return False
