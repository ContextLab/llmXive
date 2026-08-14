# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-07-12 | **Spec**: `specs/001-semantic-collapse-threshold/spec.md`
**Input**: Feature specification from `/specs/001-semantic-collapse-threshold/spec.md`

## Summary

This feature implements a systematic stress-testing pipeline to determine if non-linear interactions between acoustic distortions (reverberation RT60 and Signal-to-Noise Ratio SNR) create a universal "semantic collapse threshold" in small ASR models. The approach involves generating 54 compound distortion scenarios per audio clip from a stratified subset of the "CHiME-5" dataset (verified source for "Voices-in-the-Wild" characteristics), computing Semantic Similarity Scores (SSS) using `all-MiniLM-L6-v2`, identifying collapse points via inflection analysis, and fitting a hierarchical regression model to predict these thresholds.

**Causal vs. Associational Distinction**:
- **Synthetic Distortion (Causal)**: The plan explicitly treats the synthetic distortion generation (randomized SNR/RT60 levels) as a **randomized factorial experiment**. Findings regarding the *interaction effect* of these distortions on collapse are framed as **causal** due to the randomized intervention.
- **Natural Distribution (Associational)**: Findings regarding the natural distribution of the dataset (e.g., baseline SNR effects) are framed as **associational**, as per FR-007.

The plan adheres to CPU-first constraints (GitHub Actions free tier) with a specific GPU escape hatch for timeout/OOM failures, though the chosen embedding model is CPU-tractable.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pyroomacoustics` (acoustic simulation), `transformers` (ASR + embeddings), `scikit-learn` (regression), `pandas`/`polars` (data), `datasets` (Hugging Face), `shap` (interpretability), `pytest` (testing), `montreal-forced-aligner` (fallback).
**Storage**: Local filesystem (`data/raw`, `data/derived`), Parquet format for derived data.
**Testing**: `pytest` with `conftest.py` for fixtures and `pytest.ini` configuration.
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7GB RAM).
**Project Type**: Computational research pipeline / CLI tool.
**Performance Goals**: Process ≥50k clips (stratified sample) within 6h on CPU; generate stress curves for multiple scenarios per clip.
**Constraints**: Must run on CPU (no local GPU); data must be streamed or sampled to fit limited disk capacity; no fabricated data; strict adherence to Constitution Principle VI (Non-Linear Interaction Characterization).
**Scale/Scope**: [deferred]+ audio clips, 54 distortion scenarios each, 5-10 small ASR models.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan includes pinned `requirements.txt`, random seed management, and streaming data loading to ensure re-runs fetch the same source.
- **Principle II (Verified Accuracy)**: **Explicit Step**: A 'Reference-Validator Agent' will be executed in Phase 0 to verify all dataset URLs against the "# Verified datasets" block before pipeline execution.
- **Principle III (Data Hygiene)**: Raw data is read-only; derived artifacts (`stress_curves.parquet`, `collapse_points.parquet`) are written with checksums (`sha256sum`). PII scan is mandated.
- **Principle IV (Single Source of Truth)**: All metrics (SSS, WER, R²) are logged to `data/derived` and traced to code blocks. No hand-typed numbers in reports.
- **Principle V (Versioning)**: **Mechanism**: Content hashes will be generated using `sha256sum` and recorded in `state/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow.yaml` upon artifact generation.
- **Principle VI (Non-Linear Interaction Characterization)**: The plan explicitly includes engineered interaction terms (SNR × RT60) and SHAP analysis to validate non-linear synergies, not additive assumptions.
- **Principle VII (CPU-Tractability)**: The plan uses `all-MiniLM-L6-v2` (CPU-tractable) and `pyroomacoustics` (CPU-based). **Clarification**: The GPU escape hatch is strictly a fallback for timeout/OOM failures, not a standard operational mode.

## Project Structure

### Documentation (this feature)

```text
specs/001-semantic-collapse-threshold/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Static definitions for Phase 1 (NOT generated)
│   ├── dataset.schema.yaml
│   ├── stress_curve.schema.yaml
│   ├── collapse_point.schema.yaml
│   ├── regression_input.schema.yaml
│   └── regression_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Hugging Face dataset loaders
│   ├── stratify.py          # Sampling logic for 50k clips
│   └── validate.py          # FR-011, FR-018 validation scripts
├── simulation/
│   ├── distortion_engine.py # Pyroomacoustics wrapper (SNR/RT60)
│   └── stress_generator.py  # Cartesian product loop
├── analysis/
│   ├── metrics.py           # SSS, WER, Inflection point logic
│   ├── collapse_detector.py # FR-021 algorithm
│   └── regression.py        # Hierarchical model + SHAP
├── cli/
│   └── main.py              # Orchestration CLI
└── utils/
    ├── config.py            # Seeding, paths
    └── logging.py           # Audit trails

tests/
├── unit/
│   ├── __init__.py
│   ├── test_distortion_engine.py
│   ├── test_collapse_detector.py
│   └── test_metrics.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/                     # Downloaded subsets (streamed)
└── derived/
    ├── stress_curves.parquet
    ├── collapse_points.parquet
    └── regression_results.json
```

**Structure Decision**: Single project structure selected to maintain tight coupling between simulation, analysis, and CLI. The `tests/unit/` directory is explicitly created to satisfy T008. The `data/derived` directory is the target for T015 and T022 artifacts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Hierarchical Regression | Required to separate model-specific idiosyncrasies from universal acoustic interactions (FR-005). | Standard linear regression would confound model variance with distortion effects, failing the "universal vector" hypothesis test. |
| SHAP Analysis | Required to validate non-linear interaction forms (FR-013, Principle VI). | Coefficient inspection alone cannot confirm synergistic failure modes in non-linear models. |
| Streaming Data Loading | Required to fit 50k clips × 54 scenarios into 14GB disk/7GB RAM. | Loading full dataset into memory would cause OOM on CI runner. |
| Distributed Simulation (Ray Local Mode) | Required to satisfy FR-002 logic. | True distributed cluster (K8s/Slurm) is infeasible on CI free-tier; **Ray in Local Mode** simulates the distributed logic for the 50k sample scope while adhering to hardware constraints. |

## Compute Feasibility & GPU Escape Hatch

- **Primary Path (CPU)**:
    - **Distortion**: `pyroomacoustics` runs on CPU.
    - **Embeddings**: `all-MiniLM-L6-v2` runs on CPU (default precision).
    - **ASR**: Small models (Whisper-tiny) run on CPU.
    - **Regression**: `scikit-learn` runs on CPU.
    - **Strategy**: Stream data, process in batches of 100 clips to stay under 7GB RAM.

- **GPU Escape Hatch (Kaggle)**:
    - **Condition**: Only triggered if the `all-MiniLM-L6-v2` inference or ASR inference on the full 50k sample exceeds the 6h time limit or 7GB RAM on CPU.
    - **Scaled GPU Plan**: If offloaded, we will use `device="cuda"` with `load_in_8bit` for ASR models if necessary.
    - **Constitution Compliance**: This is strictly a fallback for timeout/OOM, not a standard operational mode, ensuring compliance with Principle VII.

## FR/SC Coverage Map

- **FR-001 (50k Stratified Sample)**: Addressed in `data/stratify.py` with specific SNR < 15dB oversampling.
- **FR-002 (Distributed Execution)**: Addressed via `Ray` in Local Mode (simulating distributed logic).
- **FR-005 (Hierarchical Regression)**: Addressed in `analysis/regression.py` with random intercepts/slopes.
- **FR-007 (Associational vs Causal)**: Addressed by distinguishing synthetic (causal) vs natural (associational) findings.
- **FR-011 (Human Validation)**: Addressed in `data/validate.py` with a defined annotation protocol.
- **FR-018 (Real-world Validation)**: Addressed in `data/validate.py` using DNS Challenge subset.
- **FR-022 (MFA Fallback)**: Addressed in `analysis/metrics.py` with conditional logic (SSS < 0.6 -> MFA).
- **FR-021 (Collapse Algorithm)**: Addressed in `analysis/collapse_detector.py`.
- **SC-001 to SC-006**: Addressed in `analysis/regression.py` and `data/derived` outputs.
