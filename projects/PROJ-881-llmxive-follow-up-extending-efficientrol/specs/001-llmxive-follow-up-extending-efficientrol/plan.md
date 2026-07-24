# Implementation Plan: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

**Branch**: `001-entropy-validity-prediction` | **Date**: 2026-07-13 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-entropy-validity-prediction/spec.md`

## Summary

This project implements a research pipeline to determine if intermediate-layer Shannon entropy in transformer models predicts token validity in RL rollouts. The system will generate ground-truth sequences for GSM8K and MiniGrid tasks using a CPU-tractable base model, instrument the model to extract entropy values at every layer, and fit **Mixed-Effects Logistic Regression (GLMM)** (as the primary method) to test the correlation, with **Fixed-Effects Logistic Regression with Clustered Standard Errors** as the fallback if GLMM fails to converge. The plan strictly adheres to the 7GB RAM / CPU core constraints of the GitHub Actions free tier by streaming datasets and batching token processing.

**Critical Scientific Correction**: Validity labels are derived by matching generated tokens against the **dataset's ground-truth answer** (external to the the model), not the model's own output. This breaks the circularity of testing if entropy predicts the model's own greedy choice.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (v4.40+), `datasets` (v2.18+), `scikit-learn` (v1.4+), `statsmodels` (v0.14+), `pandas` (v2.2+), `pyyaml`, `pytest`, `linearmodels` (for GLMM).  
**Storage**: Local filesystem (`data/` for raw/processed parquet/JSONL), GitHub Actions ephemeral storage.  
**Testing**: `pytest` (unit, integration, contract).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM); Fallback to Kaggle GPU (sufficient VRAM) for model loading if CPU fails.  
**Project Type**: Research/Scientific Computing Pipeline.  
**Performance Goals**: Complete data generation and analysis for 1000 examples (500 per task) within 6 hours.
**Constraints**: Strict GB RAM limit during processing; no external API calls for data; deterministic reproducibility (fixed seeds).  
**Scale/Scope**: A balanced dataset comprising examples from both GSM8K and MiniGrid benchmarks.; A maximum sequence length will be employed to accommodate contextual requirements.; A variable number of intermediate layers per model..

### Model Selection & Memory Feasibility Analysis
- **Primary Model**: `TinyLlama-1.1B` (4-bit quantized).
  - **Memory Calculation**: 
    - Weights: ~MB at low-bit quantization.
    - Activations: Sequence length * multiple layers * (vocab_size * hidden_dim) overhead (estimated for 4-bit + KV cache).
    - Total: < 3.0 GB (well within 7GB RAM limit).
  - **Justification**: Sufficiently small for full forward pass with intermediate state extraction on CPU.
- **Fallback Model**: `Llama-2-7B` (4-bit quantized).
  - **Trigger**: Only if `TinyLlama-1.1B` fails to produce valid sequences or if fidelity thresholds are not met.
  - **Execution**: Auto-offloaded to Kaggle GPU if CPU OOM occurs.
- **CPU-First Strategy**: `TinyLlama-1.1B` is the **only** model intended for the primary run. The 7B model is a strict fallback, ensuring the 'CPU-First' strategy is the primary path, contradicting the 'Hardware-Agnostic' principle only if absolutely necessary.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds in `config.py` and `requirements.txt`. Data fetched from canonical HF URLs only. |
| **II. Verified Accuracy** | **PASS** | Research.md cites ONLY verified URLs from the input block. No fabricated dataset links. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw datasets in `data/` before processing. Derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | All statistical outputs (AUC, p-values) trace to specific CSV/Parquet rows in `data/processed/`. |
| **V. Versioning** | **PASS** | **Versioning Mechanism**: A `scripts/update_hashes.sh` script (invoked via pre-commit hook) calculates SHA-256 of `code/` and `data/` and updates `state/artifact_hashes.yaml` on every commit. |
| **VI. Hardware-Agnostic** | **PASS** | Methodology focuses on entropy-threshold correlation, not hardware latency. GPU escape hatch is transparent to the statistical logic. |
| **VII. Ground-Truth Dependency** | **PASS** | **GPU Escape Hatch Integrity**: The GPU run must use the *exact same* model weights (same HF commit hash) and quantization level as the CPU run. Validity labels are generated *only* after the full forward pass is complete, preventing drift. |

## Scientific Validity & Independence

**Critical Design Change**: To resolve circularity concerns (scientific_soundness-*), the "validity" label is **not** derived from the model's own greedy output.
- **Definition**: A token is "valid" if it matches the **dataset's ground-truth answer** (e.g., the `answer` field in GSM8K or the `ground_truth_path` in MiniGrid).
- **Implication**: The logistic regression tests if the model's internal entropy (predictor) predicts its ability to match an **external standard** (outcome).
- **Result**: The null hypothesis (no correlation) is no longer structurally impossible. The FDR correction is meaningful because p-values reflect genuine predictive power against an external standard.

## Project Structure

### Documentation (this feature)

```text
specs/001-entropy-validity-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── entropy_profile.schema.yaml
    └── output_schema.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-881-llmxive-follow-up-extending-efficientrol/
├── data/
│   ├── raw/               # Downloaded datasets (checksummed)
│   └── processed/         # Entropy profiles, validity labels, merged data
├── code/
│   ├── src/
│   │   ├── config.py      # Environment loading, seed pinning
│   │   ├── data/
│   │   │   ├── download.py # HF dataset fetching with streaming
│   │   │   └── preprocessing.py # Batching, memory backoff, merging
│   │   ├── generation/
│   │   │   ├── generation.py # Baseline generation (full forward pass)
│   │   │   └── validity.py   # Ground truth labeling logic
│   │   ├── utils/
│   │   │   ├── entropy_calc.py # Shannon entropy calculation (logits -> entropy)
│   │   │   └── validators.py   # Schema validation helpers (Dynamically loads contracts/*.yaml)
│   │   └── analysis/
│   │       ├── glmm_fit.py     # Mixed-Effects Logistic Regression (Primary)
│   │       └── sensitivity.py  # Threshold sweep & FDR correction
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── requirements.txt
└── state/
    └── artifact_hashes.yaml
```

**Structure Decision**: Single project structure focused on `code/` and `data/` separation. The `src/` hierarchy isolates data ingestion, generation, and analysis to prevent circular dependencies and enforce the "Data First" execution order required by the spec.

**Contracts & Validation Linkage**:
The `code/src/utils/validators.py` module MUST dynamically load the schema definitions from the `contracts/` directory at runtime using `yaml.safe_load`. The `contracts/` directory is the single source of truth for all data validation logic. The plan mandates that no schema is hard-coded in Python; all structure definitions are externalized in `contracts/*.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Logistic Regression (GLMM)** | Spec FR-004 requires handling nested data (tokens within sequences). GLMM is the statistically valid method for this structure. | Standard Logistic Regression was rejected as it ignores clustering, leading to biased standard errors. Clustered SE is the fallback if GLMM fails to converge. |
| **GPU Escape Hatch (Kaggle)** | Some base models (e.g., Llama-2-7B quantized) exceed 7GB RAM even with CPU optimization. | Pure CPU execution was rejected for 7B models as it would OOM on the free runner. The escape hatch ensures real data processing without fabrication. |
| **Streaming Data Loading** | Datasets can exceed RAM limits if fully loaded. | Loading entire datasets into memory was rejected to ensure compliance with the 7GB RAM constraint for large sequence lengths. |

## Statistical Power & Convergence Strategy

- **Primary Method**: **Mixed-Effects Logistic Regression (GLMM)** with random intercepts for `sequence_id` and fixed effects for `entropy` and `layer_index`.
  - **Justification**: Handles nested data (tokens within sequences) without biasing standard errors.
  - **Layer Handling**: Layer Index used as a **continuous fixed effect** (not pooled) to preserve the "decay" hypothesis.
- **Secondary/Exploratory Method**: Fixed-Effects Logistic Regression with Clustered Standard Errors (SE) at the sequence level.
  - **Trigger**: Only if the primary GLMM fails to converge (Hessian not positive definite) or shows singular fit.
  - **Fallback**: If GLMM fails, report Clustered SE results as the primary finding with explicit caveats.
- **Power Limitation**: Explicitly acknowledge that N=1000 examples (500 per task) may limit the ability to detect small effect sizes in the GLMM, but sufficient for moderate effects.

## Implementation Phases

### Phase 1: Data Ingestion
- **Goal**: Download a representative sample of examples per task (GSM8K, MiniGrid).
- **Constraint**: **FR-001: 500 examples per task** (Total 1000).
- **Module**: `code/src/data/download.py`.
- **Action**: 
  1. **Directory Setup**: Create `data/raw/` and `data/processed/` directories.
  2. **Stream & Sample**: Stream from `openai/gsm8k` (split: test) and `minari/babyai-go-to-door`. Sample 500 examples per task.
  3. **Checksum Verification**: Compare the downloaded dataset's `dataset_info.json` commit hash against the expected hash from the HuggingFace dataset card metadata.
- **Output**: `data/raw/gsm8k.parquet`, `data/raw/minigrid.parquet`.

### Phase 2: Generation
- **Goal**: Generate sequences using `TinyLlama-1.1B` (4-bit).
- **Constraint**: **FR-002: Full Autoregressive Forward Pass, Temperature=0.0**.
- **Module**: `code/src/generation/generation.py`.
- **Action**: 
  1. Load model with 4-bit quantization.
  2. Perform **full autoregressive forward pass** for each prompt.
  3. Record token IDs and the full generated sequence.
- **Output**: `data/processed/generation_baseline.jsonl`.

### Phase 3: Entropy Extraction
- **Goal**: Capture layer-wise probabilities and calculate entropy.
- **Constraint**: **FR-003: Layer-wise Probability Capture**; **FR-007: 50-token batches**.
- **Module**: `code/src/utils/entropy_calc.py`.
- **Action**: 
  1. **Input**: Raw logits from the model.
  2. **Process**: Apply softmax internally, clamp probabilities to $1e-9$ to prevent log(0), then calculate Shannon entropy ($-\sum p \log p$).
  3. **Batching**: Process in batches of **50 tokens** (not examples) to manage VRAM/RAM during inference.
  4. **Output Format**: Write records adhering to `entropy_profile.schema.yaml` immediately to disk after each batch.
- **Output**: `data/processed/entropy_profiles.jsonl`.

### Phase 4: Statistical Analysis
- **Goal**: Fit GLMM, calculate thresholds, apply FDR.
- **Constraint**: **FR-004: GLMM**; **FR-006: Benjamini-Hochberg**; **SC-003: Minimize Weighted Error**; **SC-005: FDR Verification**.
- **Module**: `code/src/analysis/glmm_fit.py`, `code/src/analysis/sensitivity.py`.
- **Action**:
  1. **Merge**: Join `TokenSequence` and `EntropyProfile` on `prompt_id` and `token_index` using an **inner join**.
  2. **Fit**: Fit Mixed-Effects Logistic Regression (GLMM). If convergence fails, fall back to Clustered SE.
  3. **Correction**: Apply Benjamini-Hochberg correction to p-values of the entropy coefficient across layers/tasks. Input: list of p-values (sorted). Output: list of corrected p-values.
  4. **Verification**: Compare resulting FDR against nominal alpha (0.05). Set `fdr_verified` to `True` if FDR < 0.05, else `False`.
  5. **Threshold**: Identify entropy threshold minimizing weighted error (FPR + FNR).
- **Output**: `data/processed/results.json` (adhering to `analysis_result.schema.yaml`).

## Contracts & Validation

The plan mandates that all intermediate and final data files adhere to the following schemas:
- `entropy_profile.schema.yaml`: For raw entropy extraction output.
- `dataset.schema.yaml`: For merged dataset records.
- `analysis_result.schema.yaml`: For final regression results.
- `output_schema.schema.yaml`: For the final analysis output.

The `validators.py` module will dynamically load these schema files from the `contracts/` directory to validate data at runtime.

## Compute Feasibility

### CPU-First Strategy
- **Data Processing**: Streaming `datasets` library ensures RAM usage stays under a manageable threshold.
- **Token Batching**: Token processing is batched in groups of 50 tokens (FR-007) to manage memory during forward passes.
- **Example Streaming**: Dataset examples are streamed one-by-one or in small chunks to avoid loading the full dataset into RAM.
- **Model Choice**: Primary model is `TinyLlama-1.1B` (4-bit quantized). Memory calculation: ~0.6GB (weights) + ~2GB (activations) < 7GB RAM.

### GPU Escape Hatch
- **Trigger**: If the CPU run fails with `OOM` (Out of Memory) during model loading or forward pass.
- **Configuration**: Kaggle free tier (16GB VRAM).
- **Scaling**: Model loaded with `load_in_8bit=True` or `device_map="auto"`; sequences processed in smaller batches if VRAM is constrained.
- **Rationale**: This ensures the *real* computation runs on appropriate hardware without fabricating a CPU approximation for GPU-bound tasks.

## Decision Rationale

1.  **GLMM over Clustered SE**: The spec (FR-004) and research question demand handling nested data (tokens within sequences). GLMM is the statistically valid primary approach. Clustered SE is the fallback if GLMM fails to converge due to sample size limitations.
2.  **Streaming over Full Load**: The 7GB RAM limit makes loading full datasets + model states impossible. Streaming is the only viable path for real data.
3.  **Benjamini-Hochberg**: With multiple layers and tasks tested, family-wise error rate control is mandatory. BH is preferred over Bonferroni for power retention in exploratory research.
4.  **External Ground Truth**: Validity is defined by matching the dataset's answer, not the model's output. This breaks the circularity and ensures the statistical test is meaningful.
5.  **Token-Batching vs Example-Streaming**: Distinction is made between processing 50 tokens at a time for inference (to manage VRAM) and streaming examples for data loading (to manage RAM). This resolves the ambiguity in batch definitions.
