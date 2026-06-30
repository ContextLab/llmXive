# Research: MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

## Dataset Strategy

The MulTaBench benchmark relies on a collection of multiple multimodal datasets. For this reproduction, a reduced subset is selected to ensure feasibility on the free-tier CI runner.

**Selected Subset**:
- **Text-Tabular**: `BIN_TEXT_FAKE_JOB_POSTING` (Binary classification, text features).
- **Image-Tabular**: `MUL_IMAGE_CIFAR10` (Classification, image + tabular features).

**Rationale & Representativeness Strategy**:
- **Selection Logic**: These two datasets are chosen as **canonical minimal representatives** of their respective modalities (text and image) to validate the *pipeline logic* of the MulTaBench codebase.
- **Representativeness Limitation**: We explicitly acknowledge that validating the general claim "tuning improves performance" across a 40-dataset suite with only 2 datasets is statistically impossible. Therefore, the scope of this reproduction is **downgraded** from "General Validation" to "Subset-Specific Validation". The final output will state that results are indicative of the specific subset and do not support generalization to the full benchmark suite.
- **Dataset Rejection**: `MUL_IMAGE_CBIS_DDSM` was explicitly rejected due to the risk of medical imaging preprocessing constraints and access issues. `MUL_IMAGE_CIFAR10` is selected as a standard, lightweight alternative guaranteed to be loadable via the standard registry.

**Registry Verification**:
- **Action**: Before execution, the plan explicitly queries `multabench.datasets.all_datasets`.
- **Abort Condition**: If `BIN_TEXT_FAKE_JOB_POSTING` or `MUL_IMAGE_CIFAR10` are not present in the registry, the run will abort with a clear error message: "Required datasets not found in MulTaBench registry. Execution aborted."
- **Constraint**: No fabricated URLs will be used. If a dataset is missing, the run will not proceed.

## Model Strategy

**Baseline Models**:
- **LightGBM**: A gradient boosting framework (primary baseline).
- **TabPFNv2**: A transformer-based tabular model (secondary baseline, subject to memory constraints).
- **Fallback**: LightGBM (if TabPFNv2 fails due to OOM or timeout).

**Configurations**:
- **Frozen**: Embeddings are pre-trained and frozen during the downstream task (`requires_grad=False` for backbone weights).
- **Tuned**: Embeddings are fine-tuned on the downstream task (`requires_grad=True` for backbone weights).

**Verification Mechanism**:
- **Operational Difference**: To ensure the "tuned" configuration is not trivial, the plan includes a verification step. Before the training loop begins, the code will assert that `backbone.weight.requires_grad` is `True` for the "tuned" configuration and `False` for the "frozen" configuration. If this assertion fails, the run will log a fatal error and skip the model.

**CPU Feasibility & Memory Profiling**:
- **TabPFNv2 Complexity**: TabPFN has O(N^2) or O(N^3) complexity. Running on a 2 vCPU/7GB RAM runner is high-risk.
- **Profiling Strategy**:
  1. **Dry-Run**: Execute a single forward/backward pass with `batch_size=1` for TabPFNv2 on the target dataset.
  2. **Measurement**: Record peak RSS memory usage (`peak_rss`).
  3. **Decision**:
     - If `peak_rss > 6GB`: Skip TabPFNv2 for this dataset immediately (Fallback to LightGBM).
     - If `peak_rss <= 6GB`: Calculate `max_batch_size = floor(0.8 * 6GB / peak_rss)`. If `max_batch_size < 1`, skip.
- **Fallback**: If TabPFNv2 fails or is skipped, the system logs a warning and proceeds with LightGBM for that dataset-model pair.

## Statistical Rigor & Validation

**Statistical Test Strategy**:
- **Unit of Analysis**: The effective sample size is **N=2** (two datasets). A t-test on cross-validation folds is statistically invalid because folds are not independent datasets.
- **Method**: We will perform a **Directional Consistency Check** (Sign Test) on the dataset-level deltas.
  - Calculate `delta = performance_tuned - performance_frozen` for each dataset.
  - Count the number of positive deltas.
  - **Result Interpretation**:
    - If both deltas are positive: "Directional consistency observed in this subset."
    - If mixed or negative: "Directional consistency not observed in this subset."
- **Limitation Statement**: The final report will explicitly state: "With N=2 datasets, this result is indicative only and does not support a general statistical claim of 'tuning improves performance' across the full benchmark suite."

**Causal Inference**:
- The study is observational (benchmarking). Claims are framed as "tuning improves performance in this specific subset" rather than causal effects.

## Execution Plan

1. **Environment Initialization**:
   - Clone `external/MulTaBench`.
   - Install dependencies in a virtual environment.
   - Run `init.sh` or equivalent to verify the dataset registry.

2. **Pre-flight Verification**:
   - List available datasets via `multabench.datasets.all_datasets`.
   - **Abort** if `BIN_TEXT_FAKE_JOB_POSTING` or `MUL_IMAGE_CIFAR10` are missing.

3. **Configuration & Profiling**:
   - Create `config_subset.yaml`.
   - Run memory profiling dry-run for TabPFNv2.
   - Adjust batch size or skip TabPFNv2 based on profiling results.

4. **Execution**:
   - Run `benchmark.py --config config_subset.yaml`.
   - Monitor for CUDA errors; if detected, force `device='cpu'`.
   - **Verify** `requires_grad` status before training.
   - Monitor for memory errors; if detected, trigger fallback to LightGBM.

5. **Validation**:
   - Check for output files: `results_subset.csv`.
   - Validate metrics: Accuracy/AUC/MSE in [0, 1] or plausible range.
   - Perform Directional Consistency Check.
   - Compare tuned vs. frozen metrics.

## Decision/Rationale

- **Reduced Scale**: The full benchmark is infeasible on free-tier CI. A subset is necessary to prove the pipeline works.
- **CPU-Only**: The free-tier runner has no GPU. All models must be configured for CPU.
- **Graceful Degradation**: Dataset downloads may fail. The system must skip failed datasets to ensure the run completes (FR-004).
- **Dataset Selection**: Replaced medical imaging dataset with CIFAR10 to ensure standard loading and avoid access issues.
- **Statistical Method**: Replaced simple directional check with a Sign Test on dataset-level deltas and explicitly downgraded the scope of the claim to "subset-specific".
- **Fallback Strategy**: Added LightGBM fallback and concrete memory profiling to prevent OOM failures with TabPFNv2.
- **Verification Mechanism**: Added explicit `requires_grad` assertion to ensure the "tuned" configuration is functionally distinct from "frozen".
