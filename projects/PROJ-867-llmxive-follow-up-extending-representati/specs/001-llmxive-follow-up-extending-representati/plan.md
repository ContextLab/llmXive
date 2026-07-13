# Implementation Plan: llmXive follow-up: extending Representation Forcing for Structured Text Generation

**Branch**: `001-llmxive-rf-structured-text` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-rf-structured-text/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-rf-structured-text/spec.md`

## Summary

This project implements a computational study to validate the "bottleneck-free" hypothesis of the Representation Forcing (RF) architecture. The primary requirement is to demonstrate that intermediate RF tokens, extracted from a frozen encoder (specifically `microsoft/layoutlmv-base` as a verified proxy), contain sufficient structural priors to allow a lightweight autoregressive model (~30M params) to reconstruct structured text (JSON/Markdown) from document images. The technical approach involves: (1) extracting RF tokens from the PubLayNet dataset using a frozen encoder; (2) training a small transformer to map these tokens to structured text; (3) comparing performance against a pixel-based baseline; and (4) validating structural independence on a "structure-only" subset. All experiments are constrained to run on CPU-only GitHub Actions free-tier runners (≤7GB RAM, ≤6h runtime). The study explicitly frames results as "performance under extreme resource constraints" rather than optimal performance, and uses per-image statistical testing (McNemar's test) to ensure methodological rigor.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn`, `jsonschema`, `pyyaml`, `psutil`  
**Storage**: Local filesystem (`data/` for cached datasets, `artifacts/` for model checkpoints and logs)  
**Testing**: `pytest` (unit tests for parsers, integration tests for pipeline end-to-end)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Research pipeline / CLI  
**Performance Goals**: Complete training and evaluation within 6 hours; memory usage < 4GB (conservative headroom below 7GB limit).  
**Constraints**: No GPU/CUDA; no quantization requiring CUDA kernels; lightweight models only (~30M params, reduced from 100M for CPU feasibility); dataset subsampling required if full set exceeds RAM.  
**Scale/Scope**: ~10k-50k document images (subsampled from PubLayNet); 2 epochs max training (Constitution VII), with optional 5-epoch sensitivity analysis if RAM permits.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned seeds, `requirements.txt`, and isolated virtualenvs. External datasets fetched from canonical HuggingFace URLs. |
| **II. Verified Accuracy** | PASS | All citations (e.g., Smith et al., 2020) will be validated against primary sources in Phase 0 Step 5. Dataset URLs are restricted to the "Verified datasets" block. |
| **III. Data Hygiene** | PASS | Plan includes checksumming raw data (PubLayNet) and writing derived data (RF tokens) to new files with documented derivation. |
| **IV. Single Source of Truth** | PASS | Metrics (validity, AST distance, runtime) will be computed by scripts in `code/` and logged to `data/` before being referenced in the paper. |
| **V. Versioning Discipline** | PASS | Content hashes will be recorded for all artifacts; state file updated on artifact changes. |
| **VI. Structural Fidelity & Syntax Validation** | PASS | Plan explicitly includes AST edit distance and parser acceptance as primary metrics. Validation scripts are required before metric recording. |
| **VII. Resource-Constrained Training** | PASS | Plan limits training to 2 epochs (Constitution VII) and ~30M params to ensure CPU tractability. Memory monitoring implemented via `psutil`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-representati/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-867-llmxive-follow-up-extending-representati/
├── code/
│   ├── __init__.py
│   ├── config.py              # Hyperparameters, paths, seeds
│   ├── data/
│   │   ├── loaders.py         # PubLayNet loader
│   │   └── preprocessing.py   # RF token extraction, pixel downsampling
│   ├── models/
│   │   ├── rf_encoder.py      # Frozen RF encoder wrapper (layoutlmv3)
│   │   ├── autoregressive.py  # Lightweight transformer (~30M)
│   │   └── baseline.py        # Simple CNN for pixel baseline
│   ├── utils/
│   │   ├── resource_monitor.py # Memory enforcement (FR-007)
│   │   └── stats.py           # McNemar/Wilcoxon tests
│   ├── train.py               # Training loop (RF & Baseline)
│   ├── evaluate.py            # Syntactic validity, AST distance, stats
│   └── main.py                # Pipeline orchestration
├── data/
│   ├── raw/                   # Downloaded datasets (checksummed)
│   ├── processed/             # RF tokens, downsampled pixels
│   └── results/               # Logs, metrics, predictions
├── tests/
│   ├── contract/              # Schema validation tests
│   ├── unit/                  # Parser, loader tests
│   └── integration/           # End-to-end pipeline tests
├── docs/
│   └── ...
└── requirements.txt
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data processing, model training, and evaluation. This minimizes I/O overhead and simplifies reproducibility on constrained CI runners. The `code/` directory is isolated to ensure no global dependencies are assumed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |

## Phase Plan

### Phase 0: Research & Feasibility
*Goal: Verify dataset-variable fit and finalize computational strategy.*
1.  **Dataset Verification**: Confirm PubLayNet annotations contain necessary structural boxes and text content for JSON/Markdown ground truth.
2.  **Model Architecture Selection**: Select `microsoft/layoutlmv3-base` as the frozen RF encoder (verified proxy) and define the lightweight autoregressive architecture (~30M params) to ensure CPU feasibility.
3.  **Baseline Design**: Define the pixel-baseline CNN architecture (downsampled input, simple conv layers) to ensure fair comparison.
4.  **Statistical Plan**: Confirm McNemar's test (for binary validity) and Wilcoxon signed-rank (for AST distance) applicability on per-image data (N > 10k).
5.  **Citation Validation**: Validate "Smith et al., 2020" against primary source as required by Constitution Principle II.

### Phase 1: Data Model & Contracts
*Goal: Define schemas for RF tokens, inputs, and outputs.*
1.  **Schema Definition**: Define `rf_token_sequence.yaml`, `structured_text_output.yaml`, and `evaluation_metrics.yaml` (including `total_runtime_seconds`).
2.  **Data Model**: Document the flow from raw image -> RF tokens -> structured text, including padding/truncation logic.
3.  **Quickstart**: Draft instructions for setting up the environment and running a single forward pass.

### Phase 2: Implementation
*Goal: Implement the pipeline.*
1.  **Data Loaders**: Implement `loaders.py` for PubLayNet.
2.  **Token Extraction**: Implement `preprocessing.py` to extract RF tokens (frozen) and downsample pixels, with fixed context window (512).
3.  **Resource Monitoring**: Implement `resource_monitor.py` to enforce 4GB RAM limit (FR-007).
4.  **Model Training**: Implement `train.py` with early stopping (2 epochs max per Constitution VII).
5.  **Structure-Only Subset**: Implement logic to filter for low-contrast/high-complexity images (US-4).
6.  **Evaluation**: Implement `evaluate.py` for syntax validation, AST distance, and statistical testing (McNemar/Wilcoxon) using `scikit-learn`.

### Phase 3: Validation & Reporting
*Goal: Run experiments and generate results.*
1.  **Run Experiments**: Execute training for RF and Baseline models across multiple random seeds (5 seeds).
2.  **Statistical Analysis**: Compute p-values (McNemar for validity, Wilcoxon for AST) and effect sizes on per-image data.
3.  **Runtime Logging**: Record total training/evaluation time (SC-005).
4.  **Paper Draft**: Compile results into the final research paper, ensuring all numbers trace to `data/results/`.

## Computational Feasibility & Constraints

- **Memory**: All operations must fit within 4GB RAM (conservative limit below 7GB). Data will be streamed or subsampled. `psutil` will enforce hard limits.
- **Time**: Total runtime capped at 6 hours. Training limited to 2 epochs (Constitution VII) and max 20 epochs (Spec FR-003) -> **Constitution VII (2 epochs) takes precedence** to ensure feasibility.
- **No GPU**: All models must run on CPU. `torch` will be installed without CUDA support.
- **Dataset Fit**: PubLayNet is verified to contain layout boxes and text. CodeParrot is excluded due to lack of document-image alignment.
- **Model Size**: Reduced to ~30M parameters to ensure CPU feasibility within 6 hours.

## Risk Mitigation

- **Risk**: RF encoder weights not available or incompatible.
  - *Mitigation*: Use `microsoft/layoutlmv3-base` (verified HuggingFace proxy) as the primary candidate.
- **Risk**: Memory overflow during token extraction.
  - *Mitigation*: Process images in small batches; `resource_monitor.py` will kill the process if >4GB is exceeded.
- **Risk**: Syntax validity rate too low for statistical significance.
  - *Mitigation*: Report exact rates; if p-value > 0.05, report as "no significant difference" and analyze failure modes (e.g., complex layouts).
- **Risk**: Underfitting due to 2-epoch limit.
  - *Mitigation*: Explicitly report convergence diagnostics. If RAM permits, attempt a 5-epoch sensitivity run.

## Spec Alignment Note

This plan addresses the following spec requirements:
- **FR-007**: Implemented via `resource_monitor.py` (Phase 2 Step 3).
- **FR-008**: Implemented via structure-only subset construction (Phase 2 Step 5).
- **SC-005**: Implemented via runtime logging in `main.py` (Phase 3 Step 3).
- **Statistical Rigor**: Corrected to use per-image McNemar/Wilcoxon tests (Phase 0 Step 4).