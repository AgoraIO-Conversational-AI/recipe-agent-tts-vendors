"""Vendor registry — data-driven switchboard over the A4.1 TTS vendors."""
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from agora_agent.agentkit import vendors as V

CATEGORY = "TTS"   # one of: STT | LLM | TTS | REALTIME  (per repo)


@dataclass
class VendorSpec:
    cls: Callable[..., Any]
    creds: Dict[str, str] = field(default_factory=dict)   # sdk_field -> ENV_VAR (required, no default)
    defaults: Dict[str, Any] = field(default_factory=dict)  # sdk_field -> default value
    model_field: Optional[str] = None   # field overridden by {CATEGORY}_MODEL
    voice_field: Optional[str] = None   # field overridden by {CATEGORY}_VOICE


SPECS: Dict[str, VendorSpec] = {
  "minimax":   VendorSpec(V.MiniMaxTTS, {}, {"model": "speech_2_6_turbo", "voice_id": "English_captivating_female1"}, voice_field="voice_id"),
  "openai":    VendorSpec(V.OpenAITTS, {}, {"voice": "alloy"}, voice_field="voice"),
  "elevenlabs":VendorSpec(V.ElevenLabsTTS, {"key": "ELEVENLABS_API_KEY"},
                 {"model_id": "eleven_turbo_v2_5", "voice_id": "21m00Tcm4TlvDq8ikWAM", "base_url": "https://api.elevenlabs.io"}, voice_field="voice_id"),
  "cartesia":  VendorSpec(V.CartesiaTTS, {"api_key": "CARTESIA_API_KEY"},
                 {"voice_id": "a0e99841-438c-4a64-b679-ae501e7d6091", "model_id": "sonic-2"}, voice_field="voice_id"),
  "deepgram":  VendorSpec(V.DeepgramTTS, {"api_key": "DEEPGRAM_API_KEY"}, {"model": "aura-asteria-en"}, model_field="model"),
  "google":    VendorSpec(V.GoogleTTS, {"key": "GOOGLE_TTS_API_KEY"}, {"voice_name": "en-US-Neural2-F"}, voice_field="voice_name"),
  "amazon":    VendorSpec(V.AmazonTTS, {"access_key": "AWS_ACCESS_KEY_ID", "secret_key": "AWS_SECRET_ACCESS_KEY", "region": "AWS_REGION"}, {"voice_id": "Joanna", "engine": "neural"}, voice_field="voice_id"),
  "microsoft": VendorSpec(V.MicrosoftTTS, {"key": "AZURE_SPEECH_KEY", "region": "AZURE_SPEECH_REGION"}, {"voice_name": "en-US-JennyNeural"}, voice_field="voice_name"),
  "humeai":    VendorSpec(V.HumeAITTS, {"key": "HUME_API_KEY"}, {"voice_id": "ito", "provider": "HUME_AI"}, voice_field="voice_id"),
  "rime":      VendorSpec(V.RimeTTS, {"key": "RIME_API_KEY"}, {"speaker": "cove", "model_id": "mistv2"}),
  "fishaudio": VendorSpec(V.FishAudioTTS, {"key": "FISH_API_KEY", "reference_id": "FISH_REFERENCE_ID"}, {"backend": "speech-1.6"}),
  "sarvam":    VendorSpec(V.SarvamTTS, {"key": "SARVAM_API_KEY"}, {"speaker": "meera", "target_language_code": "en-IN"}),
  "murf":      VendorSpec(V.MurfTTS, {"key": "MURF_API_KEY"}, {}),
}


def available() -> List[str]:
    return sorted(SPECS)


def required_env(name: str) -> List[str]:
    return list(SPECS[name].creds.values())


def build_vendor(name: str, env: Optional[Dict[str, str]] = None):
    env = env if env is not None else os.environ
    if name not in SPECS:
        raise ValueError(f"unknown {CATEGORY} vendor '{name}'; choose one of {available()}")
    spec = SPECS[name]
    kwargs: Dict[str, Any] = dict(spec.defaults)
    # generic model/voice overrides
    if spec.model_field and env.get(f"{CATEGORY}_MODEL"):
        kwargs[spec.model_field] = env[f"{CATEGORY}_MODEL"]
    if spec.voice_field and env.get(f"{CATEGORY}_VOICE"):
        kwargs[spec.voice_field] = env[f"{CATEGORY}_VOICE"]
    # required creds + infra from env
    missing: List[str] = []
    for sdk_field, var in spec.creds.items():
        val = env.get(var)
        if not val:
            missing.append(var)
        else:
            kwargs[sdk_field] = val
    if missing:
        raise ValueError(
            f"{CATEGORY} vendor '{name}' requires environment variable(s): {', '.join(missing)}"
        )
    return spec.cls(**kwargs)
