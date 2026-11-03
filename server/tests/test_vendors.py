import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import vendors as R  # noqa: E402

# vendors whose to_config() emits a "vendor" key, and the expected value
EXPECTED_VENDOR = {
    "minimax": "minimax",
    "openai": "openai",
    "elevenlabs": "elevenlabs",
    "cartesia": "cartesia",
    "deepgram": "deepgram",
    "google": "google",
    "amazon": "amazon",
    "microsoft": "microsoft",
    "humeai": "humeai",
    "rime": "rime",
    "fishaudio": "fishaudio",
    "sarvam": "sarvam",
    "murf": "murf",
    "gradium": "gradium",
    "mistral": "mistral",
    "typecast": "typecast",
    "smallestai": "smallestai",
    "gemini": "gemini",
}


def _dummy_env(name):
    return {var: "dummy" for var in R.required_env(name)}


def test_every_vendor_constructs_and_emits_config():
    for name in R.available():
        vendor = R.build_vendor(name, _dummy_env(name))
        cfg = vendor.to_config()
        assert isinstance(cfg, dict) and cfg, f"{name}: empty config"
        if name in EXPECTED_VENDOR:
            assert cfg.get("vendor") == EXPECTED_VENDOR[name], f"{name}: vendor mismatch"


def test_byo_vendor_missing_creds_raises():
    byo = [n for n in R.available() if R.required_env(n)]
    assert byo, "expected at least one BYO vendor"
    name = byo[0]
    try:
        R.build_vendor(name, {})
    except ValueError as e:
        assert R.required_env(name)[0] in str(e)
    else:
        raise AssertionError(f"{name} should raise when creds are absent")


def test_smallestai_defaults_to_english_and_supports_common_overrides():
    default_config = R.build_vendor(
        "smallestai", {"SMALLEST_API_KEY": "smallest-key"}
    ).to_config()
    assert default_config == {
        "vendor": "smallestai",
        "params": {
            "api_key": "smallest-key",
            "model": "lightning_v3.1_pro",
            "voice_id": "kaitlyn",
            "language": "en",
        },
    }

    override_config = R.build_vendor(
        "smallestai",
        {
            "SMALLEST_API_KEY": "smallest-key",
            "TTS_MODEL": "custom-model",
            "TTS_VOICE": "voice-id",
            "TTS_LANGUAGE": "hi",
        },
    ).to_config()
    assert override_config["params"]["model"] == "custom-model"
    assert override_config["params"]["voice_id"] == "voice-id"
    assert override_config["params"]["language"] == "hi"


def test_rime_defaults_to_agora_managed_credentials():
    assert R.required_env("rime") == []
    assert R.needs_key("rime") is False
    assert R.build_vendor("rime", {}).to_config() == {
        "vendor": "rime",
        "credential_mode": "managed",
        "params": {
            "modelId": "mistv3",
            "base_url": "wss://users-ws.rime.ai/ws3",
        },
    }


def test_rime_api_key_switches_to_byok():
    env = {"RIME_API_KEY": "rime-key"}

    assert R.required_env("rime") == []
    assert R.build_vendor("rime", env).to_config() == {
        "vendor": "rime",
        "params": {
            "modelId": "mistv2",
            "api_key": "rime-key",
            "speaker": "cove",
        },
    }


def test_cartesia_defaults_to_agora_managed_credentials():
    assert R.required_env("cartesia") == []
    assert R.needs_key("cartesia") is False
    config = R.build_vendor("cartesia", {}).to_config()
    assert config == {
        "vendor": "cartesia",
        "credential_mode": "managed",
        "params": {
            "model_id": "sonic-3.6",
            "voice": {"mode": "id", "id": "a0e99841-438c-4a64-b679-ae501e7d6091"},
        },
    }
    assert "base_url" not in config["params"]


def test_cartesia_managed_respects_tts_voice_override():
    config = R.build_vendor("cartesia", {"TTS_VOICE": "cartesia-voice"}).to_config()
    assert config == {
        "vendor": "cartesia",
        "credential_mode": "managed",
        "params": {
            "model_id": "sonic-3.6",
            "voice": {"mode": "id", "id": "cartesia-voice"},
        },
    }


def test_cartesia_managed_respects_tts_model_override():
    assert R.build_vendor("cartesia", {"TTS_MODEL": "sonic-3.5"}).to_config() == {
        "vendor": "cartesia",
        "credential_mode": "managed",
        "params": {
            "model_id": "sonic-3.5",
            "voice": {"mode": "id", "id": "a0e99841-438c-4a64-b679-ae501e7d6091"},
        },
    }


def test_cartesia_byok_ignores_tts_model():
    env = {"CARTESIA_API_KEY": "cartesia-key", "TTS_MODEL": "sonic-3.5"}

    assert R.build_vendor("cartesia", env).to_config() == {
        "vendor": "cartesia",
        "params": {
            "model_id": "sonic-2",
            "voice": {"mode": "id", "id": "a0e99841-438c-4a64-b679-ae501e7d6091"},
            "api_key": "cartesia-key",
        },
    }


def test_cartesia_api_key_switches_to_byok():
    env = {"CARTESIA_API_KEY": "cartesia-key"}

    assert R.build_vendor("cartesia", env).to_config() == {
        "vendor": "cartesia",
        "params": {
            "model_id": "sonic-2",
            "voice": {"mode": "id", "id": "a0e99841-438c-4a64-b679-ae501e7d6091"},
            "api_key": "cartesia-key",
        },
    }


def test_fishaudio_defaults_to_agora_managed_credentials():
    assert R.required_env("fishaudio") == []
    assert R.needs_key("fishaudio") is False
    config = R.build_vendor("fishaudio", {}).to_config()
    assert config == {
        "vendor": "fishaudio",
        "credential_mode": "managed",
        "params": {
            "reference_id": "59cb5986671546eaa6ca8ae6f29f6d22",
            "backend": "s2.1-pro",
        },
    }
    assert "base_url" not in config["params"]


def test_fishaudio_managed_accepts_reference_id_override():
    assert R.build_vendor("fishaudio", {"FISH_REFERENCE_ID": "fish-ref"}).to_config() == {
        "vendor": "fishaudio",
        "credential_mode": "managed",
        "params": {
            "reference_id": "fish-ref",
            "backend": "s2.1-pro",
        },
    }


def test_fishaudio_managed_respects_tts_model_override():
    assert R.build_vendor("fishaudio", {"TTS_MODEL": "s2-pro"}).to_config() == {
        "vendor": "fishaudio",
        "credential_mode": "managed",
        "params": {
            "reference_id": "59cb5986671546eaa6ca8ae6f29f6d22",
            "backend": "s2-pro",
        },
    }


def test_fishaudio_byok_ignores_tts_model():
    env = {"FISH_API_KEY": "fish-key", "FISH_REFERENCE_ID": "fish-ref", "TTS_MODEL": "s2-pro"}

    assert R.build_vendor("fishaudio", env).to_config() == {
        "vendor": "fishaudio",
        "params": {
            "reference_id": "fish-ref",
            "backend": "speech-1.6",
            "api_key": "fish-key",
        },
    }


def test_fishaudio_api_key_switches_to_byok():
    env = {"FISH_API_KEY": "fish-key", "FISH_REFERENCE_ID": "fish-ref"}

    assert R.build_vendor("fishaudio", env).to_config() == {
        "vendor": "fishaudio",
        "params": {
            "reference_id": "fish-ref",
            "backend": "speech-1.6",
            "api_key": "fish-key",
        },
    }


def test_fishaudio_byok_still_requires_reference_id():
    with pytest.raises(ValueError) as excinfo:
        R.build_vendor("fishaudio", {"FISH_API_KEY": "fish-key"})
    assert str(excinfo.value) == (
        "TTS vendor 'fishaudio' requires environment variable(s): FISH_REFERENCE_ID"
    )


def test_gradium_uses_api_key_only():
    assert R.build_vendor(
        "gradium",
        {"GRADIUM_API_KEY": "gradium-key"},
    ).to_config() == {
        "vendor": "gradium",
        "params": {
            "api_key": "gradium-key",
        },
    }


def test_mistral_maps_generic_model_and_voice_overrides():
    env = {
        "MISTRAL_API_KEY": "mistral-key",
        "TTS_MODEL": "mistral-model",
        "TTS_VOICE": "mistral-voice",
    }

    assert R.build_vendor("mistral", env).to_config() == {
        "vendor": "mistral",
        "params": {
            "api_key": "mistral-key",
            "model": "mistral-model",
            "voice": "mistral-voice",
        },
    }


def test_mistral_uses_a_runnable_default_model_and_voice():
    assert R.build_vendor(
        "mistral",
        {"MISTRAL_API_KEY": "mistral-key"},
    ).to_config() == {
        "vendor": "mistral",
        "params": {
            "api_key": "mistral-key",
            "model": "voxtral-mini-tts-2603",
            "voice": "en_paul_neutral",
        },
    }


def test_typecast_maps_credentials_and_generic_overrides():
    env = {
        "TYPECAST_API_KEY": "typecast-key",
        "TTS_MODEL": "typecast-model",
        "TTS_VOICE": "typecast-override-voice",
    }

    assert R.build_vendor("typecast", env).to_config() == {
        "vendor": "typecast",
        "params": {
            "api_key": "typecast-key",
            "voice_id": "typecast-override-voice",
            "model": "typecast-model",
        },
    }


def test_typecast_uses_runnable_model_and_voice_defaults():
    assert R.required_env("typecast") == ["TYPECAST_API_KEY"]
    assert R.build_vendor(
        "typecast",
        {
            "TYPECAST_API_KEY": "typecast-key",
        },
    ).to_config() == {
        "vendor": "typecast",
        "params": {
            "api_key": "typecast-key",
            "voice_id": "tc_6620ee743bc61e2f6b79fdd1",
            "model": "ssfm-v30",
        },
    }


def test_gemini_requires_api_key_and_uses_sdk_defaults():
    assert R.required_env("gemini") == ["GEMINI_API_KEY"]
    config = R.build_vendor(
        "gemini",
        {"GEMINI_API_KEY": "gemini-key"},
    ).to_config()

    assert config == {
        "vendor": "gemini",
        "params": {
            "api_key": "gemini-key",
            "model": "gemini-3.8-flash-tts",
            "voice": "Puck",
        },
    }


def test_gemini_maps_generic_model_and_voice_overrides():
    override_config = R.build_vendor(
        "gemini",
        {
            "GEMINI_API_KEY": "gemini-key",
            "TTS_MODEL": "gemini-model",
            "TTS_VOICE": "Kore",
        },
    ).to_config()
    assert override_config["params"]["model"] == "gemini-model"
    assert override_config["params"]["voice"] == "Kore"


def test_sarvam_pins_bulbul_v3_and_supports_common_overrides():
    assert R.required_env("sarvam") == ["SARVAM_API_KEY"]
    default_config = R.build_vendor(
        "sarvam", {"SARVAM_API_KEY": "sarvam-key"}
    ).to_config()
    assert default_config == {
        "vendor": "sarvam",
        "params": {
            "api_subscription_key": "sarvam-key",
            "speaker": "ishita",
            "target_language_code": "en-IN",
            "model": "bulbul:v3",
        },
    }

    override_config = R.build_vendor(
        "sarvam",
        {
            "SARVAM_API_KEY": "sarvam-key",
            "TTS_MODEL": "sarvam-model",
            "TTS_VOICE": "sarvam-speaker",
        },
    ).to_config()
    assert override_config["params"]["model"] == "sarvam-model"
    assert override_config["params"]["speaker"] == "sarvam-speaker"
    assert override_config["params"]["target_language_code"] == "en-IN"
