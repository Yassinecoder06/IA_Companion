from __future__ import annotations

import numpy as np
import torch


class SileroVAD:
    def __init__(self, sample_rate: int = 16000, threshold: float = 0.5, device: str = "cpu") -> None:
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.device = device
        self.window_size_samples = 512 if sample_rate == 16000 else 256

        self.model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        self.model.to(self.device)
        self.model.eval()

    def speech_probability(self, audio_chunk: np.ndarray) -> float:
        if audio_chunk.ndim != 1:
            raise ValueError("audio_chunk must be mono")

        if len(audio_chunk) < self.window_size_samples:
            pad = self.window_size_samples - len(audio_chunk)
            audio_chunk = np.pad(audio_chunk, (0, pad), mode="constant")
        elif len(audio_chunk) > self.window_size_samples:
            audio_chunk = audio_chunk[: self.window_size_samples]

        tensor = torch.from_numpy(audio_chunk).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            prob = self.model(tensor, self.sample_rate).item()
        return float(prob)

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        return self.speech_probability(audio_chunk) >= self.threshold
