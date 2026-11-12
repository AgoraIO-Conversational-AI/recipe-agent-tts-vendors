"""TTS vendor registry — one readable builder per Agora-supported TTS vendor.

Each `build_<vendor>(env)` is a self-contained, copy-pasteable example of wiring
that vendor into an Agora Conversational AI agent: it shows the real SDK
constructor call and exactly which env vars it needs. `build_vendor(name)`
selects one by `TTS_VENDOR`. Optional `TTS_VOICE` / `TTS_MODEL` override the
vendor's voice / model where it has one.

Add or change a vendor by editing its builder below + the REGISTRY line.
"""
import os
from typing import Callable, Dict, List, Optional, Tuple

from agora_agent.agentkit import vendors as V

CATEGORY = "TTS"


def _voice(env, default: str) -> str:
    """The selected voice, overridable with TTS_VOICE."""
    return env.get("TTS_VOICE") or default


def _model(env, default: str) -> str:
    """The selected model, overridable with TTS_MODEL."""
    return env.get("TTS_MODEL") or default


# --- one builder per vendor (these are the samples) -------------------------

def build_minimax(env):
    """MiniMax — Agora-managed, key-less by default. Override voice with TTS_VOICE."""
    return V.MiniMaxTTS(
        model="speech_2_6_turbo",
        voice_id=_voice(env, "English_captivating_female1"),
    )


def build_openai(env):
    """OpenAI — Agora-managed, key-less by default. Override voice with TTS_VOICE."""
    return V.OpenAITTS(voice=_voice(env, "alloy"))


def build_elevenlabs(env):
    """ElevenLabs — set ELEVENLABS_API_KEY (elevenlabs.io)."""
    return V.ElevenLabsTTS(
        key=env["ELEVENLABS_API_KEY"],
        model_id="eleven_turbo_v2_5",
        voice_id=_voice(env, "21m00Tcm4TlvDq8ikWAM"),
        base_url="https://api.elevenlabs.io",
    )


def build_cartesia(env):
    """Cartesia — Agora-managed by default (TTS_MODEL overrides the managed model); set CARTESIA_API_KEY for BYOK."""
    if env.get("CARTESIA_API_KEY"):
        return V.CartesiaTTS(
            api_key=env["CARTESIA_API_KEY"],
            voice_id=_voice(env, "a0e99841-438c-4a64-b679-ae501e7d6091"),
            model_id="sonic-2",
        )
    return V.CartesiaTTS(
        credential_mode="managed",
        voice_id=_voice(env, "a0e99841-438c-4a64-b679-ae501e7d6091"),
        model_id=_model(env, "sonic-3.6"),
    )


def build_deepgram(env):
    """Deepgram — set DEEPGRAM_API_KEY (deepgram.com). Override model with TTS_MODEL."""
    return V.DeepgramTTS(
        api_key=env["DEEPGRAM_API_KEY"],
        model=_model(env, "aura-asteria-en"),
    )


def build_google(env):
    """Google — set GOOGLE_TTS_API_KEY (cloud.google.com)."""
    return V.GoogleTTS(
        key=env["GOOGLE_TTS_API_KEY"],
        voice_name=_voice(env, "en-US-Neural2-F"),
    )


def build_amazon(env):
    """Amazon Polly — set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION."""
    return V.AmazonTTS(
        access_key=env["AWS_ACCESS_KEY_ID"],
        secret_key=env["AWS_SECRET_ACCESS_KEY"],
        region=env["AWS_REGION"],
        voice_id=_voice(env, "Joanna"),
        engine="neural",
    )


def build_microsoft(env):
    """Microsoft Azure — set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION."""
    return V.MicrosoftTTS(
        key=env["AZURE_SPEECH_KEY"],
        region=env["AZURE_SPEECH_REGION"],
        voice_name=_voice(env, "en-US-JennyNeural"),
    )


def build_humeai(env):
    """Hume AI — set HUME_API_KEY (hume.ai)."""
    return V.HumeAITTS(
        key=env["HUME_API_KEY"],
        voice_id=_voice(env, "ito"),
        provider="HUME_AI",
    )


def build_rime(env):
    """Rime — Agora-managed by default; set RIME_API_KEY for BYOK."""
    if env.get("RIME_API_KEY"):
        return V.RimeTTS(
            key=env["RIME_API_KEY"],
            speaker="cove",
            model_id="mistv2",
        )
    return V.RimeTTS(
        credential_mode="managed",
        base_url="wss://users-ws.rime.ai/ws3",
        model_id="mistv3",
    )


def build_fishaudio(env):
    """Fish Audio — Agora-managed by default (TTS_MODEL overrides the managed backend); set FISH_API_KEY + FISH_REFERENCE_ID for BYOK."""
    if env.get("FISH_API_KEY"):
        if not env.get("FISH_REFERENCE_ID"):
            raise ValueError(
                f"{CATEGORY} vendor 'fishaudio' requires environment variable(s): FISH_REFERENCE_ID"
            )
        return V.FishAudioTTS(
            key=env["FISH_API_KEY"],
            reference_id=env["FISH_REFERENCE_ID"],
            backend="speech-1.6",
        )
    # Managed mode runs on Agora's Fish Audio account, so use a voice model that is
    # available there; FISH_REFERENCE_ID overrides it and TTS_MODEL overrides the backend.
    return V.FishAudioTTS(
        credential_mode="managed",
        reference_id=env.get("FISH_REFERENCE_ID") or "59cb5986671546eaa6ca8ae6f29f6d22",
        backend=_model(env, "s2.1-pro"),
    )


def build_sarvam(env):
    """Sarvam — set SARVAM_API_KEY (sarvam.ai). Override model/speaker with TTS_MODEL/TTS_VOICE."""
    return V.SarvamTTS(
        key=env["SARVAM_API_KEY"],
        model=_model(env, "bulbul:v3"),
        speaker=_voice(env, "ishita"),
        target_language_code="en-IN",
    )


def build_soniox(env):
    """Soniox — require SONIOX_API_KEY; leave omitted options to the provider."""
    options = {"api_key": env["SONIOX_API_KEY"]}
    if env.get("TTS_MODEL"):
        options["model"] = env["TTS_MODEL"]
    if env.get("TTS_VOICE"):
        options["voice"] = env["TTS_VOICE"]
    return V.SonioxTTS(**options)


def build_gemini(env):
    """Gemini TTS — set GEMINI_API_KEY (production endpoint). Override voice/model with TTS_VOICE/TTS_MODEL."""
    return V.GeminiTTS(
        api_key=env["GEMINI_API_KEY"],
        voice=_voice(env, "Puck"),
        model=_model(env, V.GeminiTTSModels.FLASH_38),
    )


def build_murf(env):
    """Murf — set MURF_API_KEY (murf.ai)."""
    return V.MurfTTS(key=env["MURF_API_KEY"])


def build_gradium(env):
    """Gradium — require GRADIUM_API_KEY; use provider defaults."""
    return V.GradiumTTS(api_key=env["GRADIUM_API_KEY"])


def build_mistral(env):
    """Mistral — require MISTRAL_API_KEY; allow TTS_MODEL/TTS_VOICE overrides."""
    return V.MistralTTS(
        api_key=env["MISTRAL_API_KEY"],
        model=_model(env, "voxtral-mini-tts-2603"),
        voice=_voice(env, "en_paul_neutral"),
    )


def build_typecast(env):
    """Typecast — require API key; use a conversational voice by default."""
    return V.TypecastTTS(
        api_key=env["TYPECAST_API_KEY"],
        voice_id=_voice(env, "tc_6620ee743bc61e2f6b79fdd1"),
        model=_model(env, "ssfm-v30"),
    )


def build_smallestai(env):
    """Smallest.ai — require SMALLEST_API_KEY; default to English synthesis."""
    options = {
        "api_key": env["SMALLEST_API_KEY"],
        "model": _model(env, "lightning_v3.1_pro"),
        "voice_id": _voice(env, "kaitlyn"),
        "language": env.get("TTS_LANGUAGE") or "en",
    }
    return V.SmallestAITTS(**options)


# --- registry: name -> (builder, required env vars) -------------------------
# An empty env list means the vendor is Agora-managed / key-less.
REGISTRY: Dict[str, Tuple[Callable, List[str]]] = {
    "minimax":    (build_minimax,    []),
    "openai":     (build_openai,     []),
    "elevenlabs": (build_elevenlabs, ["ELEVENLABS_API_KEY"]),
    "cartesia":   (build_cartesia,   []),  # CARTESIA_API_KEY is optional (BYOK)
    "deepgram":   (build_deepgram,   ["DEEPGRAM_API_KEY"]),
    "google":     (build_google,     ["GOOGLE_TTS_API_KEY"]),
    "amazon":     (build_amazon,     ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]),
    "microsoft":  (build_microsoft,  ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"]),
    "humeai":     (build_humeai,     ["HUME_API_KEY"]),
    "rime":       (build_rime,       []),  # RIME_API_KEY is optional (BYOK)
    "fishaudio":  (build_fishaudio,  []),  # FISH_API_KEY is optional (BYOK; then FISH_REFERENCE_ID is required)
    "sarvam":     (build_sarvam,     ["SARVAM_API_KEY"]),
    "murf":       (build_murf,       ["MURF_API_KEY"]),
    "gradium":    (build_gradium,    ["GRADIUM_API_KEY"]),
    "mistral":    (build_mistral,    ["MISTRAL_API_KEY"]),
    "typecast":   (build_typecast,   ["TYPECAST_API_KEY"]),
    "smallestai": (build_smallestai, ["SMALLEST_API_KEY"]),
    "soniox":     (build_soniox,     ["SONIOX_API_KEY"]),
    "gemini":     (build_gemini,     ["GEMINI_API_KEY"]),
}


def available() -> List[str]:
    return sorted(REGISTRY)


def required_env(name: str) -> List[str]:
    return list(REGISTRY[name][1])


def needs_key(name: str) -> bool:
    return bool(REGISTRY[name][1])


def build_vendor(name: str, env: Optional[Dict[str, str]] = None):
    """Build the selected vendor; raises ValueError naming any missing env vars."""
    env = env if env is not None else os.environ
    if name not in REGISTRY:
        raise ValueError(f"unknown {CATEGORY} vendor '{name}'; choose one of {available()}")
    builder, required = REGISTRY[name]
    missing = [var for var in required if not env.get(var)]
    if missing:
        raise ValueError(
            f"{CATEGORY} vendor '{name}' requires environment variable(s): {', '.join(missing)}"
        )
    return builder(env)
