# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-07-12 | **Spec**: `specs/001-semantic-collapse-threshold/spec.md`
**Input**: Feature specification from `/specs/001-semantic-collapse-threshold/spec.md`

## Summary

This feature implements a systematic stress-testing pipeline to determine if non-linear interactions between acoustic distortions (reverberation RT60 and noise SNR) create a universal "semantic collapse threshold" in small ASR models. The approach involves: (1) downloading a stratified subset of clean audio from an open ASR dataset; (2) synthesizing multiple compound distortion scenarios per clip using physical acoustic models; (3) running ASR inference and computing Semantic Similarity Scores (SSS) via `all-MiniLM-L6-v2` (Q801455); (4) algorithmically identifying collapse points (inflection + threshold); and (5) training a hierarchical regression model with interaction terms to predict collapse intensity, validating the existence of a "critical interaction vector."

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `pyroomacoustics`, `transformers`, `sentence-transformers`, `scikit-learn`, `shap`, `pandas`, `numpy`, `torchaudio`  
**Storage**: Local filesystem (`data/raw`, `data/derived`, `data/interim`) in Parquet/CSV format.  
**Testing**: `pytest` (unit, integration, contract).  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-first, 2 cores, 7GB RAM).  
**Project Type**: Research CLI / Data Pipeline.  
**Performance Goals**: Complete stress generation and analysis in ≤ 4 hours wall-clock; peak RSS ≤ 7GB.  
**Constraints**: No local GPU; must handle streaming for large datasets; must strictly adhere to a comprehensive set of distortion scenarios (Cartesian product).  
**Scale/Scope**: ~100 audio clips × 54 scenarios = 5,400 distortion inferences (CPU Pilot); ~500 clips × 54 scenarios = 27,000 inferences (GPU Primary).

> **Deferred Values**: Exact sample size calibration (targeting f² ≥ 0.02 power), specific correlation thresholds for FR-011/FR-022, and exact R² targets for SC-001 are determined in `research.md` based on dataset availability and pilot runs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | All random seeds pinned in `code/config.py`; `requirements.txt` pins exact versions; datasets fetched via canonical HF URLs. |
| **II. Verified Accuracy** | ✅ | All citations (e.g., `all-MiniLM-L6-v2`) cross-referenced with Wikidata/official repos via the **Reference-Validator Agent** (threshold `CITATION_TITLE_OVERLAP_THRESHOLD` ≥ 0.7) in `research.md`. |
| **III. Data Hygiene** | ✅ | Raw data checksummed; derivations written to new files (`data/derived/`); no in-place modification. |
| **IV. Single Source of Truth** | ✅ | All metrics in `paper/` trace to `data/derived/collapse_points.parquet` via `code/analysis.py`. |
| **V. Versioning** | ✅ | **Mechanism**: `code/utils/versioning.py` calculates SHA-256 hashes for all artifacts and updates `state/projects/PROJ-844-...yaml` `artifact_hashes` and `updated_at` timestamps on every run. |
| **VI. Non-Linear Interaction** | ✅ | Regression model explicitly includes `SNR * RT60`, `SNR²`, `RT60²`; SHAP analysis used to verify interaction form. |
| **VII. CPU-Tractability** | ✅ | `all-MiniLM-L6-v2` (Q8 quantized if needed) and `pyroomacoustics` run on CPU; ASR models (Whisper-tiny) run in default precision on CPU. |

## Project Structure

### Documentation (this feature)

```text
specs/001-semantic-collapse-threshold/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Orchestration: download -> distort -> infer -> collapse -> regress
│                        # [NOTE: Currently truncated; full logic to be implemented by Implementer Agent]
├── config.py            # Seeds, paths, hyperparameters (deferred values resolved here)
├── data/
│   ├── __init__.py
│   ├── download.py      # HF dataset loading with stratification
│   ├── distort.py       # PyRoomAcoustics synthesis (RT60, SNR)
│   └── metrics.py       # SSS, WER, Collapse Algorithm (FR-021)
├── models/
│   ├── __init__.py
│   ├── regress.py       # Hierarchical regression / FDA
│   └── shap_analysis.py # Interaction verification
├── tests/
│   ├── __init__.py
│   ├── unit/            # [T008: Required directory created]
│   │   ├── __init__.py
│   │   ├── test_distort.py
│   │   ├── test_metrics.py
│   │   └── test_collapse_algo.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── utils/
│   ├── __init__.py
│   ├── logging.py
│   └── versioning.py    # [V. Versioning: Hash calculation & state update]
└── pytest.ini           # [T008: Required config file]
```

**Structure Decision**: Single project structure with modular `code/` subpackages. `tests/unit/` is explicitly created to satisfy T008. `data/derived` is the sole output location for T015 and T022.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Hierarchical Regression | Required to separate model-specific idiosyncrasies from universal acoustic interactions (FR-005, FR-025). | Standard linear regression would conflate model bias with acoustic interaction effects. |
| Synthetic Distortion | Real-world "compound" data with known ground truth for 54 specific scenarios does not exist. | Using only real noisy data would lack controlled variation for inflection point detection. |
| SSS + WER Dual Gate | Single metric (e.g., WER) fails to capture semantic integrity in high-reverb scenarios. | Relying solely on WER would miss "hallucinated" but phonetically plausible errors. |
| Composite Score | Prevents p-hacking by avoiding data-dependent metric switching. | Switching metrics post-hoc based on performance invalidates statistical inference. |

## Phase Definitions

### Phase 0: Human Validation (FR-011)
- **Goal**: Validate SSS metric against human annotations.
- **Action**: Download Common Voice English subset, compute SSS vs human ratings.
- **Gate**: If Pearson r < 0.6, halt workflow (FR-016) or use pre-registered composite score.

### Phase 1: Stress Curve Generation (FR-002, FR-024)
- **Goal**: Generate 54 distortion scenarios per clip.
- **Action**: Apply Cartesian product of SNR (negative to high values) and RT60 (0.1s to 0.6s).
- **Check**: Log warnings for missing scenarios (FR-017).

### Phase 2: Collapse Identification (FR-021, FR-012)
- **Goal**: Identify collapse intensity and curve morphology.
- **Action**: Compute derivatives, inflection points, and classify curve shape (sigmoid vs linear).
- **Output**: `data/derived/collapse_points.parquet` (T022).

### Phase 3: Sensitivity Analysis (FR-006)
- **Goal**: Sweep thresholds to ensure robustness.
- **Action**: Vary SSS threshold. The specific value to remove/generalize: 'the specific threshold value'. Rewritten passage: Vary the SSS threshold across a range of values to evaluate its impact on model performance. and WER multiplier (x-3.0x).
- **Output**: Variance of critical interaction vector.

### Phase 4: Regression & Interaction (FR-005, FR-013)
- **Goal**: Predict collapse intensity and identify universal vector.
- **Action**: Hierarchical regression with interaction terms; FDR correction (FR-008).
- **Output**: `data/derived/regression_results.json`.
