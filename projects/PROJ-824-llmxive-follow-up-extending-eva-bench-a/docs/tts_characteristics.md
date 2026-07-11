# TTS Engine Characteristics (FR-011 Compliance)

This document defines the "known characteristics" of the synthetic TTS engine used as a fallback for missing EVA-Bench audio data.
These characteristics ensure reproducibility and allow for controlled comparison in the presence of synthetic data.

## Engine Configuration

| Parameter | Value | Description |
|:--- |:--- |:--- |
| **Model Name** | `tts_models/en/ljspeech/tacotron2-DDC` | Coqui TTS model identifier. Selected for stability and standard English prosody. |
| **Speaker ID** | `ljspeech` | Single speaker voice from the LJSpeech dataset. |
| **Language** | `en` | English language. |
| **Sample Rate** | `22050` Hz | Native output sample rate of the Tacotron2-DDC model. |
| **Device** | Auto (CPU/CUDA) | Runs on available hardware; deterministic behavior ensured via seeds. |

## Reproducibility Settings

To satisfy **FR-011**, the following deterministic settings are enforced:

- **Random Seed**: `42`
 - Applied to `random`, `numpy.random`, and `torch` (including `torch.cuda.manual_seed_all`).
 - Ensures that the same input text produces the exact same output waveform across runs on the same hardware.
- **Prosody Settings**:
 - **Speed**: 1.0 (Normal)
 - **Pitch**: 1.0 (Normal)
 - **Description**: No artificial modifications to speed or pitch are applied by default. The model generates natural prosody based on the input text and its internal alignment.

## Usage in Pipeline

The `code/synthetic/tts_engine.py` module implements this configuration.
When the pipeline detects a missing EVA-Bench audio file, it invokes this engine with the corresponding transcript to generate a fallback `.wav` file.

### Verification
The generated files are deterministic. Running the synthesis twice with the same seed and text will produce byte-identical audio files (assuming identical hardware acceleration paths).

## Limitations

- **Prosody Variation**: While the seed ensures reproducibility, the model itself may have inherent limitations in capturing complex emotional or speaker-specific nuances present in the original EVA-Bench recordings.
- **Background Noise**: The synthetic audio is clean. It does not include background noise unless explicitly added by the `AcousticPerturber` (US4) later in the pipeline.
- **Latency**: Generation time is not part of the audio signal but may affect pipeline throughput.

## Reference

- **Task**: T007
- **Requirement**: FR-011 (Fallback for missing EVA-Bench audio with known characteristics)
- **Model Source**: Coqui TTS (https://github.com/coqui-ai/TTS)