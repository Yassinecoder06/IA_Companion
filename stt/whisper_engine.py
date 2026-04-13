from __future__ import annotations

import numpy as np
from faster_whisper import WhisperModel


class WhisperEngine:
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
    ) -> None:
        self.language = language
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        text_parts = [segment.text.strip() for segment in segments if segment.text.strip()]
        return " ".join(text_parts).strip()
