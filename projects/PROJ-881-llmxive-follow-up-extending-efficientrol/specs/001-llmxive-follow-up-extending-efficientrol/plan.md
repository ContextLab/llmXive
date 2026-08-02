# Implementation Plan: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

**Branch**: `001-entropy-validity-prediction` | **Date**: 2026-07-13 | **Spec**: `specs/001-entropy-validity-prediction/spec.md`
**Input**: Feature specification from `/specs/001-entropy-validity-prediction/spec.md`

## Summary

This project implements a computational study to determine if intermediate-layer entropy in transformer models predicts token validity in RL rollouts. The approach involves generating ground-truth sequences on GSM8K and MiniGrid tasks using a CPU-tractable model (Qwen1.5-0.5B), extracting entropy profiles from intermediate layers via single-sequence streaming, and fitting Mixed-Effects Logistic Regression (GLMM) models to correlate entropy with validity labels. The study adheres to strict reproducibility, data hygiene, and hardware-agnostic signal validation principles defined in the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-optimized), `transformers`, `datasets` (streaming), `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `pytest`, `statsmodels` (for GLMM)  
**Storage**: Local file system (JSONL for intermediate states, Parquet for datasets)  
**Testing**: `pytest` (unit, integration, contract)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Research/Computational Study  
**Performance Goals**: Process 500 examples with 512-token sequences within 6 hours; memory usage < 7GB via single-sequence streaming.  
**Constraints**: No local GPU; CPU-first execution; strict adherence to single-sequence processing for entropy extraction to prevent OOM.  
**Scale/Scope**: A representative set of GSM8K problems and MiniGrid episodes; a substantial volume of token-level observations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Compliance Status | Action Plan |
|-----------|-------------------|-------------|
| I. Reproducibility | **PASS** | `requirements.txt` pinned; random seeds fixed in `code/config.py`; datasets fetched via `datasets.load_dataset` with explicit revision. |
| II. Verified Accuracy | **PASS** | All citations in `research.md` restricted to the "Verified datasets" block; Reference-Validator Agent checks `CITATION_TITLE_OVERLAP_THRESHOLD` (0.7) on every artifact write. |
| III. Data Hygiene | **PASS** | `data/` directory structure with checksums; raw data preserved; derivations written to new files with `derived_from` metadata. |
| IV. Single Source of Truth | **PASS** | All statistics in `results/` trace to specific rows in `data/processed/`; no hand-typed numbers in `paper/`. |
| V. Versioning Discipline | **PASS** | Content hashes recorded in `state/` via `state/...yaml` artifact_hashes map; `updated_at` timestamps updated on artifact changes by the Advancement-Evaluator Agent. |
| VI. Hardware-Agnostic Signal Validation | **PASS** | Analysis uses CPU-only `torch`; threshold optimization is independent of hardware latency; signal decay analyzed across sequence lengths, not hardware. |
| VII. Ground-Truth Dependency Discipline | **PASS** | Validity labels derived strictly from full forward pass ground-truth match; no heuristic early exits used for labeling. |

## Project Structure

### Documentation (this feature)

```text
specs/001-entropy-validity-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-881-llmxive-follow-up-extending-efficientrol/
├── code/
│   ├── src/
│   │   ├── config.py           # Environment loading, seed pinning
│   │   ├── data/
│   │   │   ├── download.py     # Dataset fetching (GSM8K, MiniGrid)
│   │   │   └── preprocessing.py # Streaming, batching (tokens)
│   │   ├── generation/
│   │   │   └── generation.py   # Autoregressive generation, ground-truth labeling
│   │   ├── analysis/
│   │   │   ├── entropy_calc.py # Shannon entropy calculation, layer extraction
│   │   │   └── regression.py   # Logistic regression, AUC, FDR correction
│   │   ├── utils/
│   │   │   └── validators.py   # Schema validation (EntropyProfile, TokenSequence)
│   │   └── contracts/          # Schema definitions
│   │       ├── entropy_profile.schema.yaml
│   │       ├── token_sequence.schema.yaml
│   │       └── analysis_result.schema.yaml
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_entropy_calc.py
│   │   │   └── test_validators.py
│   │   └── integration/
│   │       └── test_full_pipeline.py
│   ├── requirements.txt        # Pinned dependencies
│   └── pyproject.toml          # Project metadata, tooling config
├── data/
│   ├── raw/                    # Downloaded datasets (checksummed)
│   ├── processed/              # Intermediate states, entropy profiles
│   └── results/                # Model outputs, reports
├── scripts/
│   └── setup.sh                # Directory creation, environment setup
└── docs/
    └── constitution.md         # Project constitution
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data generation, extraction, and analysis. `code/src` mirrors the logical flow: `data` -> `generation` -> `analysis`. `tests` are co-located with source logic for unit testing, with integration tests in `tests/integration`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Implementation Phases

### Phase 0: Research & Design
- **T001**: Define Semantic Alignment logic for GSM8K/MiniGrid.
- **T002**: Select Qwen1.5-0.5B model for CPU feasibility.
- **T003**: Design GLMM with random intercepts for sequence_id.

### Phase 1: Data Acquisition & Ground Truth Labeling (FR-001, FR-002)
- **T010**: Download GSM8K and MiniGrid datasets using `datasets.load_dataset(..., streaming=True)`.
- **T011**: Generate sequences using Qwen1.5-0.5B (temperature=0.0).
- **T012**: Apply Semantic Alignment to label tokens as valid/invalid based on external ground truth.
- **T013**: Output `data/processed/ground_truth_labels.jsonl`.

### Phase 2: Intermediate State Extraction (FR-003, FR-007)
- **T020**: Re-run generation with hooks to capture logits at every layer.
- **T021**: Process sequences **one at a time** (single-sequence streaming) to fit GB RAM. Calculate Shannon entropy for each token at each layer.
- **T022**: Merge temporary batch files (if any) into `data/processed/entropy_profiles.jsonl`.
- **T023**: Validate schema using `contracts/entropy_profile.schema.yaml`.

### Phase 3: Statistical Analysis (FR-004, FR-005, FR-006)
- **T030**: Merge `ground_truth_labels.jsonl` and `entropy_profiles.jsonl` into `data/processed/merged_analysis.jsonl`.
- **T031**: Fit Mixed-Effects Logistic Regression (GLMM) with random intercept for `sequence_id`.
- **T032**: Apply Benjamini-Hochberg (FDR) correction to p-values across layers/tasks. Output `data/results/fdr_report.json`.
- **T033**: Perform Decay Analysis: stratify by sequence length (short/long) and task type. Output `data/results/decay_analysis.json`.
- **T034**: Generate Final Report `data/results/regression_results.json` containing coefficients, AUC, FDR-corrected p-values, and optimal thresholds.

### Phase 4: Verification & Reporting
- **T040**: Run `pytest` on unit and integration tests.
- **T041**: Verify all artifacts against `contracts/` schemas.
- **T042**: Update `state/...yaml` with content hashes and `updated_at` timestamps.