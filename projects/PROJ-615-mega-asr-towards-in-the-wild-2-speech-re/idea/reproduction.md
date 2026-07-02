# Reproduce & validate: Mega-ASR: Towards In-the-wild^2 Speech Recognition via Scaling up Real-world Acoustic Simulation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/   (clone of https://github.com/xzf-thu/Voices-in-the-Wild-Bench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Mega-ASR: Towards In-the-wild^2 Speech Recognition via Scaling up Real-world Acoustic Simulation

**Abstract:** Despite rapid advances in automatic speech recognition (ASR) and large audio-language models, robust recognition in real-world environments remains limited by an "acoustic robustness bottleneck": models often lose acoustic grounding and produce omissions or hallucinations under severe, compositional distortions. We propose Mega-ASR, a unified ASR-in-the-wild framework that combines scalable compound-data construction with progressive acoustic-to-semantic optimization. We introduce Voices-in-the-Wild-2M, covering 7 classic acoustic phenomena and 54 physically plausible compound scenarios, and train Mega-ASR with Acoustic-to-Semantic Progressive Supervised Fine-Tuning and Dual-Granularity WER-Gated Policy Optimization. Extensive experiments demonstrate that Mega-ASR achieves significant advantages over prior state-of-the-art systems on adverse-condition ASR benchmarks (45.69% vs. 54.01% on VOiCES R4-B-F, and 21.49% vs. 29.34% on NOIZEUS Sta-0). On complex compositional acoustic scenarios, Mega-ASR further delivers over 30% relative WER reduction against strong open- and closed-source baselines, establishing a scalable paradigm for robust ASR in-the-wild.

## Shipped code — file tree (`projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/`)

```
.gitignore
CITATION.cff
LICENSE
README.md
data/README.md
data/examples/audio/distortion.wav
data/examples/audio/dropout.wav
data/examples/audio/echo.wav
data/examples/audio/far_field.wav
data/examples/audio/mixed.wav
data/examples/audio/noise.wav
data/examples/audio/obstructed.wav
data/examples/audio/recording.wav
data/examples.jsonl
docs/assets/.gitkeep
docs/assets/audio/distortion.wav
docs/assets/audio/dropout.wav
docs/assets/audio/echo.wav
docs/assets/audio/far_field.wav
docs/assets/audio/mixed.wav
docs/assets/audio/noise.wav
docs/assets/audio/obstructed.wav
docs/assets/audio/recording.wav
docs/index.html
pyproject.toml
requirements.txt
results/README.md
scripts/README.md
scripts/evaluate_predictions.py
scripts/run_inference.py
src/voices_in_the_wild_bench/__init__.py
src/voices_in_the_wild_bench/datasets/__init__.py
src/voices_in_the_wild_bench/datasets/categories.py
src/voices_in_the_wild_bench/datasets/jsonl.py
src/voices_in_the_wild_bench/metrics/__init__.py
src/voices_in_the_wild_bench/metrics/error_rate.py
src/voices_in_the_wild_bench/models/__init__.py
src/voices_in_the_wild_bench/models/base.py
src/voices_in_the_wild_bench/models/canary.py
src/voices_in_the_wild_bench/models/kimi_audio.py
src/voices_in_the_wild_bench/models/mega_asr.py
src/voices_in_the_wild_bench/models/parakeet.py
src/voices_in_the_wild_bench/models/qwen3_asr.py
src/voices_in_the_wild_bench/models/stepaudio2.py
src/voices_in_the_wild_bench/models/utils.py
src/voices_in_the_wild_bench/models/whisper.py
src/voices_in_the_wild_bench/reporting/__init__.py
src/voices_in_the_wild_bench/reporting/breakdown.py
```

## Detected entry points

- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/scripts/evaluate_predictions.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/scripts/run_inference.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/datasets/categories.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/datasets/jsonl.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/metrics/error_rate.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/base.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/canary.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/kimi_audio.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/mega_asr.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/parakeet.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/qwen3_asr.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/stepaudio2.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/utils.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/models/whisper.py`
- `projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/external/Voices-in-the-Wild-Bench/src/voices_in_the_wild_bench/reporting/breakdown.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Voices-in-the-Wild-Bench` — not re-implementing it.
