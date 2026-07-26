# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-mega-asr-tow/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-mega-asr-tow/spec.md`

## Summary

This feature implements a stress-testing pipeline to identify "semantic collapse thresholds" in small ASR models when subjected to compound acoustic distortions (Reverb + Noise). The approach involves downloading a stratified subset of clean audio from verified open datasets, synthetically applying multiple distinct distortion vectors (varying SNR and RT60), and measuring the Semantic Similarity Score (SSS) using `all-MiniLM-L6-v2` embeddings. **Crucially, the ground truth for the regression model is established via a human-in-the-loop validation workflow** to avoid circularity. A lightweight Generalized Additive Model (GAM) is then trained to predict the *probability of semantic collapse* based on acoustic interaction terms, validating the existence of a universal "critical interaction vector."

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers`, `datasets`, `torchaudio`, `scikit-learn`, `sentence-transformers`, `librosa`, `pandas`, `pyarrow`, `numpy`, `pygam`, `pytest`
**Storage**: Local `data/` directory (parquet/csv); no external database.
**Testing**: `pytest` with `conftest.py` for fixture management.
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only, 2 cores, 7GB RAM).
**Project Type**: Data Science / Research Pipeline.
**Performance Goals**: Complete stress curve generation and regression on a sample of ~500-1000 clips within 6 hours; peak RAM < 6GB.
**Constraints**: Must run entirely on CPU; no GPU offload required for `all-MiniLM-L6-v2` or scikit-learn models; must handle streaming to avoid OOM on large datasets.
**Scale/Scope**: 54 distortion scenarios per clip; 5-10 small ASR models (e.g., Whisper-tiny, Distil-Whisper); [deferred] total stress curve data points.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file `projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/.specify/memory/constitution.md`*

| Principle | Status | Action / Reference |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | Plan includes pinned `requirements.txt`, random seed initialization in `code/main.py`, and streaming dataset loading to ensure identical results on fresh runners. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs are restricted to the "Verified datasets" block provided in the prompt. **Explicitly cited in this table:** `, `. No fabricated metrics; all scores derived from real model inference or human annotation. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksumming of raw downloads in `data/` and writing derived artifacts (stress curves, collapse points) to new files in `data/derived/`. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in the final report will be generated via scripts reading `data/derived/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be recorded in the project state YAML via `code/utils/hygiene.py`. Every artifact change updates the project state timestamp. |
| **VI. Non-Linear Interaction** | **PASS** | Plan explicitly includes engineered interaction terms (SNR × RT60) and tests for non-linear synergistic failure via GAM smooth terms. |
| **VII. CPU-Tractability** | **PASS** | Models selected (`all-MiniLM-L6-v2`, `Whisper-tiny`, scikit-learn, pygam) are verified to run within 7GB RAM on CPU. No GPU dependencies. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-mega-asr-tow/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── stress_curve.schema.yaml
│ ├── collapse_point.schema.yaml
│ ├── regression_input.schema.yaml
│ └── regression_result.schema.yaml
└── tasks.md # Phase 2 output (to be created)
```

### Source Code (repository root)

```text
code/
├── main.py # Orchestration: download, stress, human, collapse, regress, sensitivity
├── utils/
│ ├── distortion.py # Audio augmentation logic (SNR, RT60)
│ ├── metrics.py # SSS, WER calculation
│ ├── analysis.py # Collapse point detection, regression training (GAM)
│ └── hygiene.py # Content hashing and state update
├── tests/
│ ├── unit/
│ │ ├── __init__.py
│ │ ├── test_distortion.py
│ │ ├── test_metrics.py
│ │ └── test_analysis.py
│ └── conftest.py # Pytest fixtures
└── requirements.txt # Pinned dependencies

data/
├── raw/ # Downloaded parquet/csv (checksummed)
└── derived/
 ├── stress_curves.parquet
 ├── human_annotations.csv
 ├── collapse_points.parquet
 └── regression_results.json

contracts/
├── stress_curve.schema.yaml
├── collapse_point.schema.yaml
├── regression_input.schema.yaml
└── regression_result.schema.yaml
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) chosen to minimize overhead and align with the "Research Pipeline" nature of the feature. The `tests/unit/` directory and `conftest.py` are explicitly created to satisfy T008. The `contracts/` directory contains all four required schema files to ensure plan consistency.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations. | N/A |
