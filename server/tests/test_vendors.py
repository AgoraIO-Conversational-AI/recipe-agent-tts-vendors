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
