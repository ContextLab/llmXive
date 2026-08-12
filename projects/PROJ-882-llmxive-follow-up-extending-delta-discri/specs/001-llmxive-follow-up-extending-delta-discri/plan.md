# Implementation Plan: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

**Branch**: `001-delta-static-approximation` | **Date**: 2026-07-14 | **Spec**: `specs/001-delta-static-approximation/spec.md`

## Summary

This feature implements a rigorous computational study to test the hypothesis that discriminative token credit assignment signals (DelTA Coefficients) derived from dynamic gradient backpropagation can be predicted using only static, external input features (n-grams, POS tags, semantic similarity from a *distinct* model) without access to the oracle model's internal hidden states. The plan executes a three-stage pipeline: () Oracle generation on a verified subset of GSM8K using a Llama-3 model (8B or 1B fallback) to create ground-truth DelTA Coefficients; (2) Static feature extraction using a distinct external model (MiniLM) to ensure strict independence; (3) Training a lightweight 2-layer MLP on CPU to predict these coefficients and evaluating via Spearman rank correlation and cluster-robust permutation tests.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `torch` (CPU-only), `scikit-learn`, `nltk`, `scipy`, `pandas`, `pyarrow`, `shap`, `sentence-transformers`  
**Storage**: Local filesystem (parquet/JSON) under `data/raw`, `data/processed`  
**Testing**: `pytest` for unit tests; integration tests via pipeline scripts  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Computational Research / Data Pipeline  
**Performance Goals**: Complete end-to-end pipeline within 6 hours; memory < 6GB RAM  
**Constraints**: No GPU access for Oracle/Training (CPU-only) OR auto-offload to Kaggle GPU with strict fallback protocol; strict separation of static features from oracle hidden states; variance check > 1e-9 on oracle output.  
**Scale/Scope**: Subset of GSM8K (min 500 examples, seed=42); A substantial volume of tokens processed.

> **Compute Feasibility Note & Model Fallback Protocol**: The DelTA oracle step (gradient backprop) on Llama models is computationally intensive and physically infeasible on 16GB VRAM (Kaggle) due to gradient memory overhead.
> 1.  **Primary Attempt**: Run Llama-3-8B with 4-bit quantization on Kaggle GPU.
> 2.  **Fallback**: If the 8B run fails (OOM or Timeout), the pipeline **MUST** automatically switch to **Llama-3-1B** (or similar <1B model) which fits within 16GB VRAM for full backprop.
> 3.  **Hypothesis Reframing**: The study tests the "static vs. emergent" hypothesis on small-to-medium LLMs. If 8B fails, results are reported for 1B with a clear note on the model size limitation. The 500-example dataset size is **hard** and maintained regardless of model fallback.
> 4.  **Static Features**: Feature extraction and MLP training are explicitly designed for CPU.
> 5.  **Quantization Validation**: The quantization strategy (fixed-bit) is fixed. If the quantization alters gradient magnitudes significantly compared to full precision, this will be reported as a limitation, ensuring the "Oracle" is not assumed stable if it isn't.

> **Spec Amendment Note**: The source spec (FR-003) requires "cosine similarity on the Llama-3-8B last-layer embedding space". However, using the *same* model for both the Oracle (DelTA) and the Feature Extractor (semantic similarity) creates a tautological correlation (circular validation), invalidating the hypothesis test of "emergent vs. static" properties. To satisfy the **Static-Input Independence** principle (Constitution Principle VI) and ensure scientific soundness, this plan **deviates** from the literal text of FR-003 to use a **distinct, frozen external model** (`sentence-transformers/all-MiniLM-L6-v2`) for semantic similarity. This resolves the construct validity failure by ensuring the predictor measures a different semantic space than the oracle, making the "emergent" hypothesis testable. This deviation is a necessary scientific correction.

## Constitution Check

The plan adheres to the following principles from `constitution.md`:

1.  **I. Reproducibility**: All random seeds are pinned. The GSM8K dataset is fetched from the canonical HuggingFace source (`openai/gsm8k`). The pipeline is scripted to run end-to-end.
2.  **II. Verified Accuracy**: Citations to the DelTA paper, GSM8K dataset, and the external embedding model (`sentence-transformers/all-MiniLM-L6-v2`) are restricted to verified sources.
3.  **III. Data Hygiene**: Raw data (`data/raw/gsm8k_verified.parquet`) is immutable. Derived data (`data/processed/delta_coefficients.json`, `static_features.parquet`) are new files with checksums.
4.  **IV. Single Source of Truth**: All metrics (Spearman correlation, p-values) are computed by `code/eval/metrics.py` and written to JSON, never hand-typed. No fabricated or simulated metrics are used.
5.  **V. Versioning**: Artifacts are versioned by content hash.
6.  **VI. Static-Input Independence**: The plan explicitly forbids using oracle hidden states for feature extraction (FR-003). Features are strictly external (n-grams, POS, **external model** similarity). The deviation from FR-003's literal text is documented as a necessary correction to ensure this independence.
7.  **VII. Oracle Ground-Truth**: The DelTA coefficients are generated via real-time gradient backpropagation on the specified LLM (or fallback), not simulated.

## Project Structure

### Documentation

```text
specs/001-delta-static-approximation/
├── plan.md              # This file
├── research.md          # Research phase output
├── data-model.md        # Data schema and model definitions
├── quickstart.md        # Execution guide
└── contracts/
    ├── oracle_output.schema.yaml
    ├── static_features.schema.yaml
    └── predictions.schema.yaml
```

### Source Code

```text
code/
├── data/
│   ├── download_gsm8k.py       # FR-001: Download and filter GSM8K
│   ├── extract_features.py     # FR-003: Static feature extraction (uses MiniLM)
├── models/
│   ├── generate_oracle.py      # FR-002: DelTA Oracle generation (8B -> 1B fallback)
│   ├── train.py                # FR-004: MLP training
│   ├── predict.py              # FR-005: Generate predictions
├── eval/
│   └── metrics.py              # FR-005, FR-006, FR-008: Evaluation
├── lib/
│   └── delta_utils.py          # DelTA algorithm implementation
└── main.py                     # Orchestrator

data/
├── raw/
│   └── gsm8k_verified.parquet  # Clean dataset
└── processed/
    ├── delta_coefficients.json # Oracle output
    ├── static_features.parquet # Feature matrix
    ├── mlp_model.pt            # Trained model
    └── predictions.json        # Model outputs

tests/
├── unit/
│   └── test_metrics.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single-project structure chosen to minimize overhead for a research pipeline. All scripts are executable entry points.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Model Fallback (8B -> 1B) | 8B backprop exceeds 16GB VRAM. | A smaller model (1B) is the only feasible path to get *real* gradients on the free-tier GPU. |
| External Embedding Model (MiniLM) | FR-003 (amended) allows external models to ensure independence. | Using the oracle model for features creates circularity. MiniLM provides a distinct semantic space. |
| Cluster-Robust Permutation | Tokens are not independent. | Simple token-level permutation inflates p-values. Cluster-robust preserves example-level structure. |
| Feature Mapping (Sliding Window) | N-grams are aggregate. | Token-level alignment requires a sliding window centered on the target token, with counts normalized by window size. |
| Permutation Importance | SHAP is too heavy for CPU. | Permutation Importance is lightweight and sufficient to distinguish between 'signal is emergent' and 'features are poor proxies'. |

## Phase Order & Data Flow

1.  **Phase 1: Data Acquisition** (`download_gsm8k.py`)
    *   Download GSM8K from HuggingFace.
    *   Filter for verified solutions.
    *   **Assert count > 500** (stratified by length).
    *   Output: `data/raw/gsm8k_verified.parquet`.

2.  **Phase 2: Oracle Generation** (`generate_oracle.py`)
    *   Load Llama-3-8B (CPU or GPU offload).
    *   **Fallback**: If 8B fails, switch to Llama-3-1B.
    *   Run DelTA backprop on the subset.
    *   **Validate variance > 1e-9** against `contracts/oracle_output.schema.yaml` (specifically the `delta_coefficient` field).
    *   **Abort** if variance <= 1e-9 (Error E-002) to ensure the target variable is non-trivial.
    *   Output: `data/processed/delta_coefficients.json`.

3.  **Phase 3: Feature Extraction** (`extract_features.py`)
    *   **Token-Level Mapping**:
        *   **N-grams**: Sliding window of size 3 centered on target token. Count frequency of each unique n-gram string within the window, normalized by window size.
        *   **POS**: Per-token tag.
        *   **Semantic Similarity**: Cosine similarity between target token context and reference set, computed using **sentence-transformers/all-MiniLM-L6-v2** (external model).
    *   Output: `data/processed/static_features.parquet`.

4.  **Phase 4: Model Training** (`train.py`)
    *   Train a multi-layer perceptron on CPU.
    *   Save model.
    *   Output: `data/processed/mlp_model.pt`.

5.  **Phase 5: Evaluation** (`eval/metrics.py`)
    *   Predict on test set.
    *   Compute Spearman correlation.
    *   Run **Cluster-Robust Permutation Test** (shuffling entire examples, 1000 iterations).
    *   Compute feature importance (**Permutation Importance** chosen for CPU efficiency over SHAP).
    *   **Classification Logic**:
        *   If `rho > 0.1` and `p < 0.05` -> **"Signal is Predictable"**.
        *   If `rho < 0.1` AND `mean_importance < 0.01` -> **"features are poor proxies"**.
        *   If `rho < 0.1` AND `mean_importance > 0.05` -> **"signal is emergent (or non-linear)"**.
    *   Output: `data/processed/predictions.json` and metrics report.

## Data Availability & Compute

*   **Dataset**: GSM8K is open, directly downloadable via `datasets.load_dataset("openai/gsm8k", "main")`. No gated access.
*   **Compute**: The pipeline is designed for CPU-first execution. The Oracle step is the only GPU-intensive task. If the CPU run fails, the execution stage auto-offloads to Kaggle GPU. The fallback to Llama-3-1B ensures the Oracle step completes with real data if 8B is infeasible.
*   **Feasibility**: All steps are designed to fit within the -hour time limit and 7GB RAM constraint. The dataset size is maintained regardless of the model fallback.

## Limitations

*   **Model Size**: If 8B fails, results are reported for 1B. The hypothesis is tested on "small-to-medium LLMs" rather than strictly 8B.
*   **Feature Set**: The static features are limited to n-grams, POS, and simple semantic similarity. More complex syntactic parsers or external knowledge graphs were excluded to maintain the "static" constraint and CPU feasibility.
*   **Dataset Bias**: GSM8K is a specific domain (math word problems). Results may not generalize to open-ended generation.
*   **External Model**: Using MiniLM for features means the semantic space is approximated, not identical to the oracle's, which is a deliberate choice to ensure independence.
*   **Quantization**: If the 8B run requires quantization, the gradient magnitudes may differ from full precision. This limitation will be reported.
