from __future__ import annotations

from collections import deque
from queue import Queue

import numpy as np
import sounddevice as sd

from utils.audio_utils import int16_to_float32


class VoiceRecorder:
    def __init__(
        self,
        sample_rate: int,
        chunk_size: int,
        vad,
        start_speech_chunks: int,
        end_silence_chunks: int,
        pre_speech_chunks: int,
        min_speech_chunks: int,
        max_utterance_chunks: int,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.vad = vad
        self.start_speech_chunks = start_speech_chunks
        self.end_silence_chunks = end_silence_chunks
        self.pre_speech_chunks = pre_speech_chunks
        self.min_speech_chunks = min_speech_chunks
        self.max_utterance_chunks = max_utterance_chunks

        self._queue: Queue[np.ndarray] = Queue(maxsize=200)
        self._stream: sd.InputStream | None = None

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            print(f"[audio] input status: {status}")
        chunk = indata[:, 0].copy()
        try:
            self._queue.put_nowait(chunk)
        except Exception:
            pass

    def start(self) -> None:
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.chunk_size,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def listen_for_utterance(self) -> np.ndarray:
        pre_buffer: deque[np.ndarray] = deque(maxlen=self.pre_speech_chunks)
        utterance_chunks: list[np.ndarray] = []

        speech_run = 0
        silence_run = 0
        speech_started = False

        while True:
            raw_chunk = self._queue.get()
            chunk = int16_to_float32(raw_chunk)
            pre_buffer.append(chunk)
            is_speech = self.vad.is_speech(chunk)

            if not speech_started:
                if is_speech:
                    speech_run += 1
                else:
                    speech_run = 0

                if speech_run >= self.start_speech_chunks:
                    speech_started = True
                    utterance_chunks.extend(list(pre_buffer))
                    silence_run = 0
                continue

            utterance_chunks.append(chunk)
            if is_speech:
                silence_run = 0
            else:
                silence_run += 1

            if len(utterance_chunks) >= self.max_utterance_chunks:
                break

            if silence_run >= self.end_silence_chunks and len(utterance_chunks) >= self.min_speech_chunks:
                break

        return np.concatenate(utterance_chunks, axis=0)
