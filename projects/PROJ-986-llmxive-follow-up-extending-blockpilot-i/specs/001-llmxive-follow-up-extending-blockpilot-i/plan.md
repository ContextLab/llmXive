# Implementation Plan: llmXive follow-up: extending "BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Spec"

**Branch**: `001-llmxive-blockpilot-extension` | **Date**: 2026-08-30 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-llmxive-blockpilot-extension/spec.md`

## Summary

This project implements a lightweight, CPU-tractable policy learning system to predict the optimal block size ($B^*$) for diffusion-based speculative decoding. The approach avoids neural policy networks in favor of classical **classification** models (XGBoost, Random Forest, Decision Trees) trained on static prefilling features (prompt length, mean attention entropy, hidden state norms). The system generates ground-truth labels via an exhaustive sweep of block sizes on open datasets (GSMK, HumanEval, Dolly) and validates the hypothesis that static features serve as robust, architecture-agnostic proxies for model uncertainty.

**Critical Methodological Note**: The target variable ($B^*$) is derived from an exhaustive sweep maximizing acceptance length. While this creates a circular definition for the target within a single dataset, the validity of the "proxy" hypothesis is tested **exclusively** by the **generalization** of the learned mapping to unseen architectures and domains (e.g., Train on Qwen/Math -> Test on Llama/Code). If the model fails to generalize, the hypothesis is rejected. An independent correlation with perplexity (FR-006), calculated via a separate greedy pass, serves as secondary validation. All results are framed as **exploratory** due to sample size constraints. The task is explicitly framed as **Classification** (predicting discrete classes {1, 2, 4, 8, 16, 32}), not regression.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-optimized), `datasets`, `scikit-learn`, `xgboost`, `torch` (CPU-only build), `pandas`, `numpy`, `pyyaml`, `pytest`, `statsmodels` (for VIF)  
**Storage**: Local ephemeral storage on GitHub Actions runner (streamed datasets, no persistent DB)  
**Testing**: `pytest` (unit tests for feature extraction, integration tests for sweep logic, contract validation)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, ~7 GB RAM, ~14 GB disk, no GPU)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Feature extraction latency ≤ 1ms per sample; full sweep for 500 samples (Qwen) / 100 samples (Llama) ≤ 6 hours  
**Constraints**: Must run on CPU; must handle memory constraints via streaming; no unverified datasets; must not exceed 6h CI limit  
**Scale/Scope**: A representative subset of samples per dataset (GSM8K, HumanEval, Dolly-15k) for Qwen3-4B; A sample set for Llama-3-8B (due to compute constraints); 3 models; Two architectures (Qwen3-4B, Llama-3-8B). **Validation includes cross-architecture tests in both directions (Train Qwen->Test Llama AND Train Llama->Test Qwen).**

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; datasets fetched from canonical HF URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | Citations restricted to verified dataset URLs provided in spec; no external claims without primary source. |
| **III. Data Hygiene** | PASS | Raw data streamed/checked; derivations written to new files; PII scan enabled. |
| **IV. Single Source of Truth** | PASS | All results trace to `data/` rows and `code/` blocks; no hand-typed stats. |
| **V. Versioning Discipline** | PASS | **Mechanism**: A dedicated `update_state.py` script runs after each artifact generation, calculating content hashes (SHA-256) of all output files and updating `state/projects/PROJ-986-...yaml` with the `updated_at` timestamp and new hashes. This ensures the state file reflects the exact content of the artifacts. |
| **VI. Architecture-Agnostic Proxy Validation** | PASS | Evaluation explicitly reports metrics for both Qwen3-4B and Llama-3-8B; **Cross-architecture tests performed in both directions** (Train Qwen->Test Llama, Train Llama->Test Qwen) to validate robustness. |
| **VII. Zero-Overhead Inference Guarantee** | PASS | Latency measured against a low-latency threshold on -core CPU; policy models are non-neural (lightweight). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-blockpilot-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── sweep.py                 # Exhaustive block-size sweep (FR-001)
│   ├── features.py              # Static feature extraction (FR-002)
│   ├── train.py                 # Model training (FR-003) - includes VIF handling
│   ├── evaluate.py              # Generalization & correlation (FR-004, FR-006)
│   ├── utils/
│   │   ├── data_loader.py       # Streaming dataset loading
│   │   ├── metrics.py           # Latency, accuracy, correlation calc
│   │   └── collinearity.py      # VIF calculation and decorrelation
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Streamed dataset shards (temporary)
│   ├── processed/               # Feature vectors, ground truth labels
│   └── models/                  # Trained sklearn/xgboost artifacts
├── tests/
│   ├── contract/                # Schema validation tests
│   ├── integration/             # End-to-end sweep + train pipeline
│   └── unit/                    # Feature extraction logic tests
└── specs/
    └── 001-llmxive-blockpilot-extension/
        └── ...
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) chosen to minimize overhead and align with CPU-tractable, research-focused workflow. No separate frontend/backend required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed; no violations requiring justification. | N/A |

## Phase Plan

### Phase 0: Research & Feasibility
- **Goal**: Validate dataset availability, confirm feature extractability on CPU, and verify sweep feasibility.
- **Tasks**:
  - Confirm GSM8K/HumanEval/Dolly-15k URLs are accessible via `datasets.load_dataset`.
  - Test attention entropy extraction on a single sample with Qwen3-4B on CPU.
  - Run a mini-sweep (a small number of samples, 2 block sizes) to estimate runtime.
  - **Verify** that perplexity calculation for Llama-3-8B (100 samples) fits within time budget.
- **Output**: `research.md` with dataset strategy, compute feasibility, and risk assessment.

### Phase 1: Data Model & Contracts
- **Goal**: Define data schemas for inputs, outputs, and models.
- **Tasks**:
  - Define `FeatureVector` schema (prompt_length, mean_attention_entropy, hidden_state_norm).
  - Define `GroundTruth` schema (sample_id, block_sizes, acceptance_lengths, B_star).
  - Define `Prediction` schema (sample_id, predicted_B, actual_B, accuracy).
  - Define `ModelArtifact` schema (model_id, model_type, feature_importance, etc.).
  - Create YAML contracts for validation.
- **Output**: `data-model.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation
- **Goal**: Build the full pipeline: sweep → features → train → evaluate.
- **Tasks**:
  - Implement `sweep.py` with checkpoint/resume logic.
  - Implement `features.py` with NaN handling and latency measurement.
  - Implement `collinearity.py` to calculate VIF and perform residualization/PCA if VIF > 5.
  - Implement `train.py` to accept pre-processed features and train XGBoost/RF/DT (**Classification** models).
  - Implement `evaluate.py` to calculate **classification metrics** (Accuracy, F1) and **correlation with perplexity** (FR-006).
- **Output**: Executable `code/` scripts.

### Phase 3: Validation & Reporting
- **Goal**: Run full pipeline, validate against contracts, generate results.
- **Tasks**:
  - Execute on a representative set of samples (Qwen) and a representative set of samples (Llama) per dataset.
  - **Perform Cross-Architecture Tests**: Train on Qwen/Math -> Test on Llama/Code; Train on Llama/Math -> Test on Qwen/Code.
  - Verify latency ≤ 1ms.
  - Compute **exploratory** Accuracy, F1, generalization gap, and correlation coefficients (with perplexity).
  - Generate figures and paper-ready tables.
  - **Ensure** all metrics are labeled as "preliminary" or "exploratory" in the report.
  - **Report** metrics for **both** Qwen3-4B and Llama-3-8B architectures as required by Principle VI.
- **Output**: Final results, `paper/` draft, `research_review` submission.