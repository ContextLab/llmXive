# Research: Reproduce & validate: WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

## 1. Problem Statement & Scope

The goal is to reproduce the WBench benchmark evaluation pipeline. The spec requires running the vendored code on a CPU-only CI runner. The critical challenge is that the original benchmark involves heavy video generation or large vision models which are infeasible on a 2-core, 7GB RAM runner.

**Scope Definition**:
- **In Scope**: Environment setup, dependency resolution, metric calculation logic, data aggregation, error handling, and structural validation of results.
- **Out of Scope (or Skipped)**: Generating new high-fidelity video sequences. The evaluation will focus on the *benchmark logic* (metrics) using **pre-existing video assets** from the verified WBench dataset. If an asset is missing, the case is skipped.

## 2. Dataset Strategy

The spec references the WBench dataset. We must verify the dataset contains the necessary variables for the sub-metrics.

### Verified Datasets
- **WBench (Parquet)**:
  - Source: `https://huggingface.co/datasets/meituan-longcat/WBench/resolve/main/splits/first_person.parquet`
  - Source: `https://huggingface.co/datasets/meituan-longcat/WBench-examples/resolve/main/hyworld1.5/meta.json`
  - **Verification**: These URLs are provided in the "Verified datasets" block. The parquet file is expected to contain columns for `prompt`, `interaction_sequence`, `video_path`, and `ground_truth` annotations required for metric calculation.
  - **Fit Check**: The dataset MUST contain `interaction_sequence` and `ground_truth`. If the parquet only contains metadata without video paths or interaction data, the plan will halt with a "Dataset Mismatch" error. We will **not** generate dummy data.

**Dataset Variable Fit**:
- **Required**: `prompt`, `interaction_sequence`, `expected_outcome`, `video_path`.
- **Status**: The verified WBench dataset is assumed to contain these fields. If `video_path` points to a missing file, the case is skipped. **No mock frames** are generated for consistency or physics metrics.

## 3. Technical Approach & Constraints

### Compute Feasibility Analysis
- **Baseline Calculation**: 289 cases * ~100 frames/case * 2s/frame (CPU optical flow/VLM inference) [deferred].
- **CI Constraint**: 6 hours max.
- **Conclusion**: Full 289-case run is **not feasible** on CI.
- **Strategy**: The CI pipeline will target a **subset of 50 cases** (representative sample) to complete within 6 hours. The full run is labeled 'Proxy Evaluation' and is intended for local execution on more powerful hardware.

### CPU-Only Execution Strategy
- **Libraries**:
  - `torch`: Install CPU-only wheel (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
  - `opencv-python`: Standard CPU build.
  - `scikit-learn`: Standard CPU build.
  - `transformers`: Load models in `device="cpu"` mode. **No model substitution**: We will use the original models specified in the paper. If they are too large, we will use **frame sampling** (e.g., 1 frame/sec) to reduce compute load.
- **Memory Management**:
  - Process data in chunks (batch size = 1).
  - Clear memory after each test case.
  - Limit concurrent processes to a minimal, single-threaded configuration.

### Metric Calculation Logic
- **Consistency & Physics**:
  - These metrics rely on optical flow or frame-difference analysis.
  - **Implementation**: Use `opencv` for optical flow (`cv2.calcOpticalFlowFarneback`) and frame differencing. These are CPU-tractable.
  - **Validity**: Cite standard computer vision techniques for motion consistency.
- **Quality & Adherence**:
  - Rely on pre-trained vision-language models (VLMs).
  - **Strategy**: Use the **original VLMs** from the paper. To fit CPU constraints, we will sample frames (e.g., at a reduced rate) rather than using the full video. If the original model is too large, the run is labeled 'Proxy Evaluation' and the variance is documented.

### Error Handling & Resilience
- **Timeouts**: Implement a `retry` decorator with exponential backoff (max 3 retries) for network-dependent steps (e.g., model loading from HuggingFace). **No retry for local video processing**.
- **Missing Data**: If a video file is missing or a metric requires a field that is `null`, log a warning and mark the metric as `null` (not crash).
- **Partial Results**: Ensure the `aggregator` writes results incrementally (append to CSV) so a crash doesn't lose all data.

## 4. Statistical & Methodological Considerations

- **Sample Size**: The target is a substantial number of cases, but the CI default is a subset to ensure feasibility.
- **Power Analysis**: Not applicable for a benchmark reproduction (descriptive statistics), but the plan ensures the subset is representative.
- **Causal Claims**: None. This is an evaluation of model performance, not a causal study.
- **Multiple Comparisons**: Not applicable for the benchmark scores themselves.
- **Variance Analysis**: Any deviation from the paper's values is documented with its cause (e.g., "Frame sampling used", "CPU precision variance"). No fixed tolerance is set as a pass/fail criterion; the focus is on understanding the deviation.

## 5. Decision Log & Rationale

| Decision | Rationale |
|----------|-----------|
| Use real video data only | Mocking video frames invalidates consistency/physics metrics (Construct Validity). |
| No model substitution | Substituting VLMs changes the metric definition. Original models must be used. |
| Frame sampling | Reduces CPU load for VLM inference without changing the model architecture. |
| Skip missing assets | Ensures data integrity. Generating dummy data would produce nonsensical scores. |
| Subset CI target | Ensures the time limit is met while maintaining metric validity. |

## 6. Reproducibility Variance Plan

- **Documentation**: Any deviation due to frame sampling or CPU approximation will be explicitly documented in the `final_results.csv` metadata or a separate `variance_report.md`.
- **Proxy Evaluation Label**: If the full dataset cannot be processed, the results are labeled 'Proxy Evaluation (Subset)' to distinguish from a full reproduction.