import os, sys
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
