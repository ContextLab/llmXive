# Implementation Plan: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

**Branch**: `001-delta-static-approximation` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-delta-discri/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-delta-discri/spec.md`

## Summary

This feature implements a rigorous three-stage pipeline to test the hypothesis: "How much of the dynamic DelTA signal is recoverable from static input features?"
1.  **Oracle Generation**: Compute ground-truth DelTA coefficients for a stratified subset of the GSM8K dataset using the Llama-3-1B model via dynamic gradient backpropagation.
2.  **Upper Bound Oracle**: Train a "perfect" predictor using the oracle model's hidden states to establish the theoretical maximum predictability (the ceiling). This controls for domain mismatch between the gradient space and static feature space.
3.  **Static Approximation**: Train a lightweight 2-layer MLP on CPU to predict coefficients using only external static features (n-grams, POS tags, semantic similarity via MiniLM).
4.  **Evaluation**: Compare the Static Model's performance against the Upper Bound Oracle.
    -   **Emergent Signal**: Static Model (Low Correlation) AND Upper Bound Oracle (High Correlation).
    -   **Poor Proxies**: Static Model (Low Correlation) AND Upper Bound Oracle (Low Correlation).
    -   **Significant**: Static Model (High Correlation).
    -   Includes Confidence Intervals (Bootstrap) and an Example-Level Permutation Test.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `datasets`, `transformers`, `torch` (CPU/MPS), `scikit-learn`, `sentence-transformers`, `pandas`, `pyarrow`, `spacy`, `numpy`
**Storage**: Local filesystem (`data/raw`, `data/processed`) in Parquet/JSON formats.
**Testing**: `pytest` for unit tests; `bash` scripts for end-to-end pipeline validation.
**Target Platform**: GitHub Actions Free Tier (2 CPU, 7GB RAM) for feature extraction, training, and evaluation. **Kaggle GPU (standard VRAM capacity)** is a **mandatory fallback** for the Oracle step only (auto-offload on OOM/Timeout).
**Project Type**: Research pipeline / CLI tool
**Performance Goals**: End-to-end pipeline < 6 hours; Memory footprint < 7GB RAM during training; Oracle step < 4 hours (on GPU) or < 6 hours (on CPU if feasible).
**Constraints**: No circularity (static features must not use oracle hidden states); No access-gated data (GSM8K only); All seeds pinned.
**Scale/Scope**: Subset of GSM8K (a representative sample for Oracle, full feature set for training).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file:*

- **I. Reproducibility**: **PASS**. Plan mandates pinned seeds (a fixed value), explicit dataset versioning (`openai/gsm8k`), and isolated virtualenv. Scripts will be idempotent.
- **II. Verified Accuracy**: **PASS**. Plan cites only verified GSM8K sources. All external citations (DelTA paper, MiniLM) will be validated by the Reference-Validator.
- **III. Data Hygiene**: **PASS**. Raw data (`gsm8k_verified.parquet`) will be checksummed. Derived data (coefficients, features) will be written to new files with derivation logs.
- **IV. Single Source of Truth**: **PASS**. All metrics (correlation, p-value, CI, classification) will be read from `data/processed/metrics.json` and traced to `code/eval/metrics.py`.
- **V. Versioning Discipline**: **PASS**. Content hashes for `data/` artifacts will be recorded in the state YAML.
- **VI. Static-Input Independence Validation**: **PASS**. The plan explicitly forbids using oracle hidden states for the *Static Model*, but allows them for the *Upper Bound Oracle* (control).
- **VII. Oracle Ground-Truth Generation**: **PASS**. Plan requires real-time gradient backpropagation on Llama-3-1B for the Oracle step, with variance checks (`> 1e-9`).
    - *Note on Model Version*: Principle VII cites "Llama-3-8B" as an example. This plan implements **Llama-3-1B** to meet compute feasibility constraints on the free tier. This is a valid subset for the hypothesis test, but the Constitution should be updated if 8B becomes a hard requirement.

## Project Structure

### Documentation (this feature)

```text
specs/001-delta-static-approximation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── delta_oracle.schema.yaml       # Flat token-level output
│   ├── oracle_output.schema.yaml      # Nested summary output
│   ├── feature_output.schema.yaml
│   ├── static_features.schema.yaml
│   ├── predictions.schema.yaml
│   └── metrics_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download_gsm8k.py       # Downloads and filters GSM8K
│   └── cache.py                # Local caching utilities
├── oracle/
│   ├── generate_oracle.py      # Computes DelTA coefficients via backprop
│   ├── generate_upper_bound.py # Computes Upper Bound predictions (using hidden states)
│   └── delta_engine.py         # Core DelTA logic
├── features/
│   ├── extract_features.py     # Extracts n-grams, POS, semantic similarity
│   └── embedding_utils.py      # MiniLM integration
├── models/
│   ├── train.py                # Trains 2-layer MLP (Static & Upper Bound)
│   ├── predict.py              # Generates predictions
│   └── model_arch.py           # MLP definition
├── eval/
│   ├── metrics.py              # Spearman, Kendall, Permutation Test, CI
│   └── importance.py           # Permutation Importance (Upper Bound only)
├── utils/
│   ├── logging.py              # Structured logging
│   └── seeds.py                # Global seed management
└── main_pipeline.py            # Orchestrator (download -> oracle -> features -> train -> eval)

data/
├── raw/
│   └── gsm8k_verified.parquet  # Cleaned GSM8K subset
└── processed/
    ├── delta_coefficients.json # Oracle outputs (Flat, governed by delta_oracle.schema.yaml)
    ├── upper_bound_predictions.json # Upper Bound model outputs
    ├── static_features.parquet # Feature vectors
    ├── mlp_model_static.pt     # Trained Static Model
    ├── mlp_model_upper.pt      # Trained Upper Bound Model
    ├── predictions.json        # Static Model outputs
    └── metrics.json            # Final results
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`oracle`, `features`, `models`, `eval`) to ensure clear separation of concerns. The `generate_upper_bound.py` script is added to explicitly implement the control experiment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Upper Bound Oracle** | Required to distinguish "Emergent Signal" from "Poor Proxies". Without it, a low correlation is ambiguous. | A simple Permutation Importance check on a failed model is circular and invalid (see Methodology concerns). |
| GPU Escape Hatch (Kaggle) | The DelTA oracle step requires gradient backpropagation through a large-scale parameter model, which is computationally prohibitive on the 2-core CPU runner within 6 hours. | Running on CPU would likely exceed the 6-hour limit or fail due to OOM. The plan explicitly uses the Kaggle GPU escape hatch for this specific step as a mandatory fallback. |
| Two-Stage Pipeline | Separating Oracle generation from Static Training is required to prevent data leakage and ensure the independence of the validation metric (Constitution Principle VI). | A joint training approach would violate the "Static-Input Independence" principle by potentially leaking oracle states into the feature set. |
| Permutation Test (1000 iters) | Required to establish statistical significance (p < 0.05) against the null hypothesis that correlation is due to chance. | A simple p-value from `scipy` assumes normality which may not hold for rank correlations on small subsets; permutation is more robust. |
| Confidence Intervals | Required to account for power limitations in the sample size.. | A point estimate alone is insufficient to distinguish "true zero" from "underpowered detection". |

## Implementation Phases

### Phase 1: Data Preparation & Oracle Generation

1.  **1.1 Download & Filter**:
    -   Download `openai/gsm8k` (main split).
    -   Filter for verified correct solutions.
    -   Stratify by solution length.
    -   Select subset (seed=42, target 500, min 10).
    -   Save to `data/raw/gsm8k_verified.parquet`.
2.  **1.2 Oracle Generation & Validation**:
    -   Run DelTA on Llama-3-1B for the subset.
    -   **Validation**: Compute variance of coefficients.
    -   **Abort Logic**: If `variance <= 1e-9`, raise `ERR_TRIVIAL_TARGET` and exit.
    -   Save to `data/processed/delta_coefficients.json` (Flat format, `delta_oracle.schema.yaml`).
    -   *GPU Fallback*: If CPU run fails (OOM/Timeout), auto-retry on Kaggle GPU.
3.  **1.3 Static Feature Extraction**:
    -   Extract n-grams, POS, and MiniLM semantic similarity.
    -   Ensure NO hidden states from Llama-3-1B are used.
    -   Save to `data/processed/static_features.parquet`.

### Phase 2: Model Training

1.  **2.1 Static Model Training**:
    -   Train a multi-layer perceptron (ReLU, a moderate number of hidden units) on static features.
    -   Save to `data/processed/mlp_model_static.pt`.
2.  **2.2 Upper Bound Oracle Training**:
    -   Extract hidden states from Llama-3-1B for the same tokens.
    -   Train a 2-layer MLP (same architecture) on hidden states.
    -   Save to `data/processed/mlp_model_upper.pt`.
    -   *Note*: This is the control experiment.

### Phase 3: Evaluation & Reporting

1.  **3.1 Prediction Generation**:
    -   Generate predictions for both models on the test set.
    -   Save to `data/processed/predictions.json` (Static) and `upper_bound_predictions.json`.
2.  **3.2 Statistical Testing**:
    -   Compute Spearman and **Kendall's Tau** correlations for both models.
    -   Compute **Confidence Intervals** via Bootstrap (1000 iters).
    -   Perform **Example-Level Permutation Test** (shuffle entire examples, not tokens) a sufficient number of times for the Static Model.
3.  **3.3 Classification Logic**:
    -   **Emergent Signal**: Static Correlation (Low/Not Significant) AND Upper Bound Correlation (High/Significant).
    -   **Poor Proxies**: Static Correlation (Low/Not Significant) AND Upper Bound Correlation (Low/Not Significant).
    -   **Significant**: Static Correlation (High/Significant).
    -   *Note*: This logic supersedes the flawed "Permutation Importance < 0.01" rule in the spec (FR-008), which is now updated to reflect this correct logic.
4.  **3.4 Reporting**:
    -   Generate `data/processed/metrics.json`.
    -   **Mandatory Framing**: Explicitly state in the report that all findings are **associational**, not causal (FR-007).
    -   Include CI ranges, p-values, and the `causal_disclaimer` field.

### Phase 4: Verification

1.  **4.1 Unit Tests**: Verify variance check, permutation logic, and schema compliance.
2.  **4.2 Integration Test**: Run full pipeline end-to-end.

## Spec Alignment Note

-   **FR-008 & Edge Cases Conflict**: The original spec text (FR-008, Edge Cases) mandated using "Permutation Importance < 0.01" to distinguish "emergent" vs "poor proxies". This plan implements a **superior methodology** (Upper Bound Oracle comparison) that resolves the circular logic identified by the review panel.
-   **Resolution**: The spec (`spec.md`) has been **updated** to reflect this new classification logic. The "Permutation Importance" rule has been removed from the spec text and replaced with the Upper Bound comparison logic.
-   **FR-007**: The spec has been updated to explicitly require the `causal_disclaimer` field in the output metrics.