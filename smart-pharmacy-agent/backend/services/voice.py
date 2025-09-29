import tempfile
from gtts import gTTS
from faster_whisper import WhisperModel
import os

# Defaults from env (but can override in app)
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")
WHISPER_LANG = os.getenv("WHISPER_LANG", "en")

# ---- Speech-to-Text ----
def load_whisper(model_size: str = WHISPER_MODEL_SIZE):
    return WhisperModel(model_size, device="cpu", compute_type="int8")

def transcribe_audio_bytes(wav_bytes: bytes, language: str = WHISPER_LANG) -> str:
    model = load_whisper()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(wav_bytes)
        tmp.flush()
        path = tmp.name
    segments, _ = model.transcribe(path, language=language, vad_filter=True)
    return "".join(segment.text for segment in segments).strip()

# ---- Text-to-Speech ----
def speak_text_to_audio_bytes(text: str, lang: str = "en"):
    if not text.strip():
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts = gTTS(text=text, lang=lang)
        tts.save(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
