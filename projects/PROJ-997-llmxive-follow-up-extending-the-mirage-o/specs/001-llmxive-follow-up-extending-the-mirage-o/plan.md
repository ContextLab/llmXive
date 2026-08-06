# Implementation Plan: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Branch**: `001-llmxive-mipu-gap-bounds` | **Date**: 2026-08-06 | **Spec**: [link]

## Summary

This feature implements a hardware-grounded validation framework to quantify the "policy gap" (KL divergence) between full-precision LLM training signals and quantized inference outputs. The system extracts training-side features (**gradient norms** and **local curvature** via Hutchinson's estimator) from a pre-trained model (e.g., Llama-3-8B) using a verified dataset of prompts. These features are paired with ground-truth divergence measurements obtained via CPU-based quantized engines (`llama.cpp` for INT4/INT8, ONNX Runtime/`llama.cpp` for FP8). A lightweight regression model (Kernel Ridge Regression) is trained to predict this gap, aiming to replace expensive synchronous hardware checks with a fast analytical bound. The plan strictly adheres to the project constitution's requirement for hardware-grounded validation and non-circular feature independence.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `llama-cpp-python` (for CPU quantized inference), `scikit-learn` (KRR), `datasets`, `pandas`, `numpy`, `torch` (CPU-only mode), `pytest`, `einops`  
**Storage**: Local `data/` directory (Parquet/CSV), `code/` for scripts  
**Testing**: `pytest` (unit tests for data extraction, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Complete dataset generation + model training within 6 hours on CPU; latency reduction target ≥90% for proxy vs. sync.  
**Constraints**: Max constrained RAM, limited disk capacity, no local GPU. Quantized models must fit in RAM (e.g., low-bit/8-bit 8B model).  
**Scale/Scope**: Sample size limited by compute budget (target n ≥ 300 samples for statistical power).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file:*

1.  **Reproducibility (NON-NEGOTIABLE)**: ✅ **PASS**. The plan mandates pinned seeds, explicit `requirements.txt`, and deterministic data fetching from canonical verified dataset sources (`datasets.load_dataset('gsm8k', 'main')` and `datasets.load_dataset('HuggingFaceH4/ultrachat_200k')`). All artifacts will be checksummed.
2.  **Verified Accuracy**: ✅ **PASS**. The plan uses ONLY datasets listed in the "Verified Datasets" block in `research.md`. No unverified datasets are used as primary sources.
3.  **Data Hygiene**: ✅ **PASS**. Raw data is preserved; derivatives are written to new files with checksums. No PII will be committed.
4.  **Single Source of Truth**: ✅ **PASS**. The `data-model.md` defines the schema; all statistics in the final report will trace back to specific rows in the generated Parquet files.
5.  **Versioning Discipline**: ✅ **PASS**. The plan includes a content-hash strategy for artifacts and updates the `state` YAML timestamp upon completion.
6.  **Hardware-Grounded Validation**: ✅ **PASS**. The core methodology explicitly uses `llama.cpp` and CPU-based inference to generate ground-truth KL divergence, avoiding simulated noise models.
7.  **Non-Circular Feature-Target Independence**: ✅ **PASS**. Features (gradient norms, curvature) are extracted from the full-precision model state *only* (forward/backward passes), while the target (KL divergence) is measured independently by the quantized engine. No data leakage is planned.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-mipu-gap-bounds/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── training_sample.schema.yaml
│   └── gap_prediction_result.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── models/              # Regression models (KRR)
├── services/
│   ├── feature_extractor.py   # Extracts gradient norms and curvature
│   ├── quantized_inference.py # Wraps llama.cpp for INT4/INT8/FP8
│   └── gap_calculator.py      # Computes KL divergence
├── cli/                 # Entry points for pipeline stages
└── lib/                 # utilities (streaming, checksums)

tests/
├── contract/            # Validates against schema.yaml
├── integration/         # End-to-end pipeline tests
└── unit/                # Feature extraction, KL calc tests

data/
├── raw/                 # Downloaded parquet shards (streamed)
├── processed/           # Generated training_sample.parquet
└── models/              # Trained KRR artifacts
```

**Structure Decision**: A single-project structure is chosen to minimize overhead for a research pipeline. The `services/` directory separates concerns (feature extraction vs. inference) to enforce the "Non-Circular Feature-Target Independence" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CPU-only Quantized Inference Engine | Required by Constitution Principle VI (Hardware-Grounded Validation) to measure true KL divergence. | Simulated noise models or theoretical bounds are rejected as they violate the "Hardware-Grounded" requirement and lack empirical validity. |
| Streaming Data Loading | Required to handle datasets larger than a moderate memory footprint on the GitHub Actions runner. | Loading full datasets into memory would cause OOM errors and fail the compute feasibility constraint. |
| Kernel Ridge Regression (KRR) | Chosen for interpretability and robustness on small datasets (n ~ 300-1000). | Deep learning predictors (MLPs) are overkill for this tabular task and risk overfitting on small samples; KRR provides a stable baseline. |
| Gradient Norms & Curvature (Hutchinson) | Required by FR-001/FR-002 to capture training-side signals. | 'Logits magnitude' was rejected as a sole proxy because it fails to capture the full training dynamics required by the spec. Hutchinson's estimator is used for curvature as it is O() memory and CPU-feasible. |

## Phased Execution Plan

### Phase 0: Research & Feasibility
- **Goal**: Verify dataset availability and confirm variable alignment.
- **Steps**:
  1.  Inspect verified dataset schemas (from `research.md`) to confirm presence of prompts and reasoning labels (for GSM8K subset).
  2.  Validate `llama.cpp` binary compatibility for `ubuntu-latest` runner.
  3.  Define the exact set of quantization levels (INT4, INT8, FP8) and their mapping to the verified datasets.
- **Output**: `research.md`, updated `plan.md`.

### Phase 1: Data Model & Contracts
- **Goal**: Define strict schemas for data ingestion and model output.
- **Steps**:
  1.  Define `TrainingSample` schema (inputs, gradient norms, local curvature, quantized logits, KL, ground truth answer).
  2.  Define `GapPredictionResult` schema (predicted gap, actual gap, error metrics).
  3.  Generate `contracts/*.schema.yaml` files.
- **Output**: `data-model.md`, `quickstart.md`, `contracts/`.

### Phase 2: Implementation (Data Generation)
- **Goal**: Generate the hardware-grounded dataset.
- **Steps**:
  1.  Implement `feature_extractor.py`: Load full-precision model, extract **gradient norms** (L2 norm of gradients w.r.t. inputs) and **local curvature** (via Hutchinson's estimator) for a sample of prompts from the **verified datasets** (GSM8K for reasoning subset, Ultrachat for general prompts).
  2.  Implement `quantized_inference.py`: Run `llama.cpp` (or equivalent) on the same prompts in INT4, INT8, FP8 modes.
  3.  Implement `gap_calculator.py`: Compute KL divergence between full-precision and quantized outputs.
  4.  Stream and aggregate results into `data/processed/training_sample.parquet`.
- **Output**: `data/processed/training_sample.parquet`.

### Phase 3: Implementation (Model Training)
- **Goal**: Train the Gap Predictor.
- **Steps**:
  1.  Load `training_sample.parquet`.
  2.  Split data (train/val/test) with fixed seed.
  3.  Train Kernel Ridge Regression model using a **fixed hyperparameter grid** (e.g., alpha=[0.1, 1.0, 10.0], gamma=[0.01, 0.1, 1.0]) to ensure reproducibility and avoid overfitting.
  4.  Evaluate correlation (r) and MAE against test set.
- **Output**: Trained model artifact, evaluation metrics.

### Phase 4: Validation & Reporting
- **Goal**: Verify bounds and statistical significance.
- **Steps**:
  1.  **Static RL Simulation**: Simulate the MIPU loop over the test set.
      - Define **Environment**: The test set of prompts (specifically the GSM8K subset for reasoning scores).
      - Define **Baseline Policy**: A policy that accepts [deferred] of samples (or uses a fixed threshold). Calculate **Baseline Acceptance Rate** ([deferred] or fixed).
      - Define **Proxy Policy**: Accept sample if `predicted_gap < threshold` (threshold swept:, 0.1, 0.2). Calculate **Proxy Acceptance Rate**.
      - Define **Reward**: 1 if model's final answer (from full-precision) matches `ground_truth_answer` (from GSM8K), 0 otherwise. Calculate **Final Score** for both policies.
  2.  **Bound Verification**: Calculate the percentage of samples where `|predicted - actual| < 0.1` for each quantization level (INT4, INT8, FP8). This verifies the proxy's accuracy against the hardware ground truth.
  3.  **Latency Instrumentation**: Measure the time taken for the proxy check (KRR prediction) vs. the full hardware sync (actual quantized inference time) for each sample. Calculate latency reduction.
  4.  **Statistical Comparison**: Perform paired t-test on **Acceptance Rates** (Proxy vs. Baseline) and **Final Scores** (Proxy vs. Baseline). Apply Bonferroni correction.
  5.  **Collinearity Handling**: Compute Variance Inflation Factor (VIF) for gradient norms and local curvature to acknowledge and report collinearity.
- **Output**: Final research report, updated `state` YAML.

## Compute Feasibility Strategy

- **CPU-First**: The entire pipeline (feature extraction, quantized inference, model training) is designed to run on the GitHub Actions CPU runner.
  - **Quantized Inference**: `llama.cpp` is used in CPU mode. The model will be loaded in low-bit quantization to fit within available RAM.
  - **Data Streaming**: Datasets are streamed (`streaming=True`) to avoid memory overflow.
  - **Model Training**: Kernel Ridge Regression is computationally light (O(N^) depending on solver, but N is limited to a moderate range of samples.).
  - **Feature Extraction**: Gradient norms and curvature (Hutchinson) are computed via vector-Jacobian products (constant memory overhead relative to full Hessian).
- **GPU Escape Hatch**: Not required for this specific plan as the quantized inference is feasible on CPU. If `llama.cpp` CPU inference proves too slow (>6h), the plan will scale down the sample size (n=100) to meet the time constraint, as per SC-005. No GPU offload is planned for the regression model itself.

## Risk Mitigation

- **Risk**: `llama.cpp` fails to load a specific quantization format on the runner.
  - **Mitigation**: Implement robust error handling in `quantized_inference.py` to log errors, skip the sample, and continue processing. The dataset will be marked with a `processing_status` flag.
- **Risk**: Zero-divergence cases (numerical identity).
  - **Mitigation**: Add a small epsilon to KL calculation to prevent division-by-zero errors. Handle zero-divergence cases explicitly in the analysis (e.g., log them as "stable" samples).
- **Risk**: Dataset lacks required variables (e.g., no prompts or answers).
  - **Mitigation**: The plan uses a verified dataset (GSM8K for reasoning, Ultrachat for general) or a fixed set of hardcoded prompts. If neither is available, the plan will fail gracefully rather than using unverified data.
- **Risk**: Overfitting due to small sample size.
  - **Mitigation**: Phase 3 uses a fixed, small hyperparameter grid and a simple train/val split to minimize overfitting risk.

## Methodological Notes

- **Gradient Norms Definition**: Computed as the L2 norm of the gradients of the loss w.r.t. the input embeddings.
- **Curvature Proxy**: Full Hessian trace is infeasible. The plan uses **Hutchinson's estimator** (random projection method) to approximate local curvature. This is computationally tractable (O(1) memory) and provides a valid proxy for activation sensitivity.
- **Static RL Simulation**: The "small-scale RL task" is simulated by applying the proxy policy to the static dataset. The "acceptance rate" and "final score" are calculated deterministically over the test set, satisfying the spec's requirement for a policy loop comparison. The Baseline Acceptance Rate is defined as the maximum possible rate (or a fixed threshold) to allow for a valid paired t-test.