from __future__ import annotations

import requests


class OllamaClient:
    def __init__(
        self,
        url: str = "http://localhost:11434/api/generate",
        model: str = "tinyllama",
        keep_alive: str = "30m",
        timeout_sec: int = 90,
        system_prompt: str = "",
    ) -> None:
        self.url = url
        self.model = model
        self.keep_alive = keep_alive
        self.timeout_sec = timeout_sec
        self.system_prompt = system_prompt
        self.session = requests.Session()

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
        }
        if self.system_prompt:
            payload["system"] = self.system_prompt
        response = self.session.post(self.url, json=payload, timeout=self.timeout_sec)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def warmup(self) -> None:
        self.generate("Say: ready")
