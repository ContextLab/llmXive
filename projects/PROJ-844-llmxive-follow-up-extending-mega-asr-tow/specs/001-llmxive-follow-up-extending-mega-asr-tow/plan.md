# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-07-12 | **Spec**: `specs/001-semantic-collapse-threshold/spec.md`

## Summary

This feature implements a systematic stress-testing pipeline to identify "semantic collapse thresholds" in small ASR models under compound acoustic distortions (reverberation + noise). The approach involves: (1) downloading a stratified subset of clean audio from open ASR datasets, (2) applying 54 distinct distortion vectors with incrementally increasing intensity, (3) measuring Semantic Similarity Scores (SSS) via `all-MiniLM-L6-v2` and Word Error Rate (WER), (4) **rigorously selecting the best-fit degradation model (linear vs. sigmoid) for each stress curve**, and (5) training a CPU-tractable regression model to predict robustness profiles based on acoustic parameter vectors and their interaction terms. **Critical Correction**: The primary regression target is the *shape* of degradation (slope of the selected model at the 0.5 threshold), not the input intensity itself, to avoid circularity. The "collapse intensity" is retained only as a derived diagnostic for sensitivity analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `transformers` (CPU-optimized), `scikit-learn`, `jiwer` (WER), `torch` (CPU), `soundfile`, `librosa`, `pyroomacoustics`, `scipy`  
**Storage**: Local `data/` directory (streaming mode for large datasets), `data/derived/` for processed artifacts  
**Testing**: `pytest` with `conftest.py` for fixtures, unit tests for distortion logic, integration tests for pipeline stages  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM, no GPU)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: <6 hours total runtime, <7GB peak RSS memory  
**Constraints**: CPU-only execution, no synthetic data fabrication, real dataset streaming  
**Scale/Scope**: ~[deferred] audio clips, 54 distortion scenarios per clip, 5-10 ASR models  

### # Verified datasets
| Dataset | Verified Source URL | Role |
|---------|---------------------|------|
| OpenASR-Leaderboard (AMI) | `https://huggingface.co/datasets/hf-audio/open-asr-leaderboard/resolve/main/ami/test-00000-of-00015.parquet` | Primary source for clean audio clips with transcripts |
| LibriSpeech (test.clean) | `https://huggingface.co/datasets/openslr/librispeech_asr/resolve/main/all/test.clean/0000.parquet` | Secondary source for speaker diversity |
| Common Voice (en) | `https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0` | Human annotations for FR-011 validation (small subset) |

> **Spec Amendment Note**: The spec (FR-001) mandates "Voices-in-the-Wild-2M". This dataset has **no verified source**. The plan substitutes it with **OpenASR-Leaderboard (AMI)** and **LibriSpeech** (verified open sources). **Justification**: The research question targets the *interaction* of distortions, which is simulated via the 54 vectors. The base dataset's acoustic profile (studio vs. wild) is less critical than the *controlled application* of the distortion grid. The plan explicitly acknowledges that external validity to true "wild" audio is a hypothesis to be tested, not a guaranteed outcome of the dataset choice.

## Constitution Check

- **I. Reproducibility**: ✅ Random seeds pinned in `code/config.py`; all datasets fetched via `datasets.load_dataset` with explicit `trust_remote_code=False` and verified URLs.
- **II. Verified Accuracy**: ✅ All dataset URLs cited from the `# Verified datasets` block **above** (self-contained in this plan). No external citations added without verification.
- **III. Data Hygiene**: ✅ `data/` files checksummed; raw data preserved; derivations written to new files (`data/derived/`).
- **IV. Single Source of Truth**: ✅ All metrics trace to `data/derived/collapse_points.parquet` (for collapse points) and **`data/derived/regression_results.json`** (for critical interaction vectors and robustness profiles). No hand-typed numbers.
- **V. Versioning Discipline**: ✅ Content hashes recorded in state YAML; `requirements.txt` pins versions.
- **VI. Non-Linear Interaction Characterization**: ✅ Plan explicitly includes engineered interaction terms (SNR × RT60) and validates non-linearity by **testing the statistical significance of the interaction coefficient (p < 0.05 after FDR correction) in the Response Surface Model**. Synergy is confirmed if the interaction term explains significant variance beyond additive effects, avoiding invalid magnitude comparisons.
- **VII. CPU-Tractability**: ✅ All models (`all-MiniLM-L6-v2`, Whisper-tiny, Distil-Whisper) selected for CPU feasibility; streaming used for large datasets to stay under 7GB RAM.

## Project Structure

### Documentation (this feature)
```text
specs/001-semantic-collapse-threshold/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── stress_curve.schema.yaml
    ├── collapse_point.schema.yaml
    ├── regression_input.schema.yaml
    └── regression_result.schema.yaml
```

### Source Code (repository root)
```text
src/
├── models/              # ASR model wrappers (Whisper-tiny, etc.)
├── services/
│   ├── distortion.py    # Apply reverberation/noise
│   ├── metrics.py       # SSS and WER calculation
│   ├── curve_fit.py     # Model selection (Linear vs. Sigmoid) and fitting
│   └── collapse.py      # Threshold detection logic
├── cli/
│   └── main.py          # Orchestration script (full CLI args, stress-curve generation)
└── lib/
    └── config.py        # Seeds, paths, hyperparameters

tests/
├── unit/                # Distortion logic, metric calculations, curve fitting
│   ├── __init__.py      # REQUIRED: Empty file to make package
│   ├── test_distortion.py
│   ├── test_metrics.py
│   └── test_curve_fit.py
├── integration/         # End-to-end pipeline tests
└── contract/            # Schema validation tests

data/
├── raw/                 # Streamed/downloaded datasets (checksummed)
└── derived/
    ├── stress_curves.parquet
    ├── collapse_points.parquet
    └── regression_results.json
```

**Structure Decision**: Single-project structure selected to minimize overhead; `src/` organization separates concerns (models, services, CLI) while `tests/` mirrors the `src/` layout for maintainability. `data/` is strictly read-only for raw and append-only for derived.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 54 Distortion Scenarios | Required by spec to capture non-linear interaction space | Reducing scenarios would miss synergistic failure modes (Constitution Principle VI) |
| Dual Metric Validation (SSS + WER) | Prevents circular dependency on a single metric (FR-009) | Using only SSS would fail to detect "silent" collapses where embeddings remain stable but transcription fails |
| Model Selection Protocol (Linear vs. Sigmoid) | Required to distinguish degradation types (Constitution Principle VI) | Forcing a sigmoid fit on linear data yields misleading slopes; must select best-fit model |
| Stratified Random Sampling | Required to ensure speaker/SNR diversity (FR-001) | "First N" streaming is biased and may miss critical acoustic conditions |
| Pre-Distortion Split | Required for SC-001 (held-out test set) | Splitting after curve fitting causes data leakage |

## Testing Strategy

- **Unit Tests**: `tests/unit/` must contain `__init__.py` and tests for `distortion.py`, `metrics.py`, and `curve_fit.py`.
- **Integration Tests**: `tests/integration/` must verify the full pipeline from download to regression.
- **Contract Tests**: `tests/contract/` must validate `stress_curves.parquet` and `collapse_points.parquet` against the YAML schemas.
- **Configuration**: `pytest.ini` must be present in the root to configure test paths and coverage.
- **Missing Artifact Resolution**: The plan explicitly requires `tests/unit/__init__.py` and `pytest.ini` to be created. `src/cli/main.py` must be a full orchestration script, not a stub. `data/derived/collapse_points.parquet` must be generated as a byproduct of the sensitivity analysis.

## Orchestration Logic (T015 Compliance)

The `src/cli/main.py` script MUST implement the following sequence:
1. **Parse CLI Args**: Accept `--subset-size`, `--models`, `--thresholds`, etc.
2. **Download & Split**: Stream datasets, perform stratified sampling, and **immediately split clips into train/test sets**.
3. **Distortion Loop**: For each clip in the **training set**, apply 54 distortion vectors, compute SSS/WER, and save to `stress_curves.parquet`.
4. **Curve Fitting**: Fit both linear and sigmoid models to each curve, select best fit, and extract slope/area.
5. **Regression**: Train model on training data, evaluate on test data.
6. **Sensitivity**: Repeat collapse detection with varying thresholds, saving `collapse_points.parquet`.
7. **Output**: Generate `regression_results.json` and summary reports.
