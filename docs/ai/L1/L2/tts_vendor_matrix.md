# Deep Dive — TTS Vendor Matrix

> **When to Read This:** You are adding a new TTS vendor, auditing an existing vendor's SDK constructor fields, choosing which vendor to use, or checking what credentials are required. For the high-level registry design, start at [02_architecture](../02_architecture.md).

All 13 vendors live in `server/src/vendors.py`. Each has a self-contained `build_<vendor>(env)` function — the actual SDK constructor call — plus an entry in `REGISTRY` mapping its name to `(builder, required_env_list)`.

## Registry overview

| `TTS_VENDOR` | Managed | SDK class | Required env vars |
| ------------ | :-----: | --------- | ----------------- |
| `minimax` 🟢 | yes | `V.MiniMaxTTS` | _none_ |
| `openai` 🟢 | yes | `V.OpenAITTS` | _none_ |
| `elevenlabs` | | `V.ElevenLabsTTS` | `ELEVENLABS_API_KEY` |
| `cartesia` | | `V.CartesiaTTS` | `CARTESIA_API_KEY` |
| `deepgram` | | `V.DeepgramTTS` | `DEEPGRAM_API_KEY` |
| `google` | | `V.GoogleTTS` | `GOOGLE_TTS_API_KEY` |
| `amazon` | | `V.AmazonTTS` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| `microsoft` | | `V.MicrosoftTTS` | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` |
| `humeai` | | `V.HumeAITTS` | `HUME_API_KEY` |
| `rime` | | `V.RimeTTS` | `RIME_API_KEY` |
| `fishaudio` | | `V.FishAudioTTS` | `FISH_API_KEY`, `FISH_REFERENCE_ID` |
| `sarvam` | | `V.SarvamTTS` | `SARVAM_API_KEY` |
| `murf` | | `V.MurfTTS` | `MURF_API_KEY` |

🟢 = Agora-managed (keyless). All imports are from `agora_agent.agentkit.vendors`.

## Per-vendor constructor details

### MiniMax (managed, keyless)

```python
V.MiniMaxTTS(
    model=_model(env, "speech_2_6_turbo"),
    voice_id=_voice(env, "English_captivating_female1"),
)
```

Override: `TTS_VOICE`, `TTS_MODEL`.

### OpenAI (managed, keyless)

```python
V.OpenAITTS(voice=_voice(env, "alloy"))
```

Override: `TTS_VOICE`.

### ElevenLabs

```python
V.ElevenLabsTTS(
    key=env["ELEVENLABS_API_KEY"],
    model_id="eleven_turbo_v2_5",
    voice_id=_voice(env, "21m00Tcm4TlvDq8ikWAM"),
    base_url="https://api.elevenlabs.io",
)
```

Override: `TTS_VOICE`. Source: elevenlabs.io.

### Cartesia

```python
V.CartesiaTTS(
    api_key=env["CARTESIA_API_KEY"],
    voice_id=_voice(env, "a0e99841-438c-4a64-b679-ae501e7d6091"),
    model_id="sonic-2",
)
```

Override: `TTS_VOICE`. Source: cartesia.ai.

### Deepgram

```python
V.DeepgramTTS(
    api_key=env["DEEPGRAM_API_KEY"],
    model=_model(env, "aura-asteria-en"),
)
```

Override: `TTS_MODEL`. Source: deepgram.com.

### Google

```python
V.GoogleTTS(
    key=env["GOOGLE_TTS_API_KEY"],
    voice_name=_voice(env, "en-US-Neural2-F"),
)
```

Override: `TTS_VOICE`. Source: cloud.google.com.

### Amazon Polly

```python
V.AmazonTTS(
    access_key=env["AWS_ACCESS_KEY_ID"],
    secret_key=env["AWS_SECRET_ACCESS_KEY"],
    region=env["AWS_REGION"],
    voice_id=_voice(env, "Joanna"),
    engine="neural",
)
```

Override: `TTS_VOICE`. Note: three credentials required. Typical `AWS_REGION`: `us-east-1`.

### Microsoft Azure

```python
V.MicrosoftTTS(
    key=env["AZURE_SPEECH_KEY"],
    region=env["AZURE_SPEECH_REGION"],
    voice_name=_voice(env, "en-US-JennyNeural"),
)
```

Override: `TTS_VOICE`. Typical `AZURE_SPEECH_REGION`: `eastus`.

### Hume AI

```python
V.HumeAITTS(
    key=env["HUME_API_KEY"],
    voice_id=_voice(env, "ito"),
    provider="HUME_AI",
)
```

Override: `TTS_VOICE`. Source: hume.ai.

### Rime

```python
V.RimeTTS(
    key=env["RIME_API_KEY"],
    speaker="cove",
    model_id="mistv2",
)
```

Source: rime.ai. No `TTS_VOICE`/`TTS_MODEL` override in the current builder (speaker/model are hardcoded).

### Fish Audio

```python
V.FishAudioTTS(
    key=env["FISH_API_KEY"],
    reference_id=env["FISH_REFERENCE_ID"],
    backend="speech-1.6",
)
```

Two credentials required: API key + reference ID for the voice clone. Source: fish.audio.

### Sarvam

```python
V.SarvamTTS(
    key=env["SARVAM_API_KEY"],
    speaker="meera",
    target_language_code="en-IN",
)
```

Source: sarvam.ai. Designed for Indian-English (`en-IN`).

### Murf

```python
V.MurfTTS(key=env["MURF_API_KEY"])
```

Source: murf.ai. Uses SDK defaults for voice/model.

## Voice and model override helpers

`_voice(env, default)` — returns `TTS_VOICE` if set, else the given default.
`_model(env, default)` — returns `TTS_MODEL` if set, else the given default.

These are applied where the vendor's SDK supports a voice/model override. Check the per-vendor section above to see which vendors use them.

## Adding a new vendor

1. Identify the `agora_agent.agentkit.vendors.<ClassName>` for the new vendor.
2. Write `build_<vendor>(env)` following the existing pattern — one SDK call, all required fields from `env`, optional voice/model override with `_voice`/`_model`.
3. Add to `REGISTRY`: `"name": (build_<vendor>, ["REQUIRED_ENV_VAR", ...])`.
4. Run `verify:backend` + `pytest tests` — `test_vendors.py::test_every_vendor_constructs_and_emits_config` will cover the new vendor automatically.
5. Update `README.md` Vendors table and `server/.env.example` with the new vendor block.

## Related L1

- [02_architecture](../02_architecture.md) · [04_conventions](../04_conventions.md) · [06_interfaces](../06_interfaces.md)
