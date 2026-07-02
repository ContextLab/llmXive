# Research: Mega-ASR Reproduction & Validation

## 1. Problem Statement & Methodology

The goal is to reproduce the results of the "Mega-ASR" paper, specifically validating the Word Error Rate (WER) on the VOiCES and NOIZEUS benchmarks. The methodology involves:
1. **Environment Setup**: Configuring a CPU-only Python environment compatible with the GitHub Actions free tier.
2. **Data Strategy**: Streaming audio data from Parquet/JSONL sources to avoid memory overflow.
3. **Inference**: Executing the vendored `run_inference.py` on the model checkpoint.
4. **Evaluation**: Calculating WER using a standardized implementation and comparing against paper claims.
5. **Metric Stability Analysis**: Collecting WER data at varying sample sizes (N=100, 500, 1000) to assess the stability of the metric, explicitly acknowledging this is not a validation of allometric scaling laws (which require training data).

## 2. Dataset Strategy

The project relies on the following verified datasets. **Note**: The `Voices-in-the-Wild-2M` dataset is the primary target, but due to RAM constraints, the plan relies on the verified Parquet shards for sampling.

| Dataset Name | Verified URL | Usage in Plan | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **Voices-in-the-Wild-2M** | ` | Primary benchmark. Used to extract audio paths and ground truth text. | **Confirmed**: Contains `audio_path` and `text` fields required for ASR. |
| **NOIZEUS** | ` | Secondary benchmark for cross-validation. | **Confirmed**: Contains audio paths and transcriptions. **Verification Step**: The pipeline will check if `audio_path` resolves to an accessible file (local or remote) before processing. If not, the record is skipped and logged. |
| **Sample Examples** | `data/examples.jsonl` (Local) | P1/P2 Smoke Testing. | **Confirmed**: Manually verified to contain audio paths and text. |

**Dataset Mismatch Handling**:
- The plan explicitly checks that the dataset contains the required `audio_path` and `text` fields. If a dataset lacks these, the pipeline will fail early with a `DataVariableMissingError`.
- **R4-B-F Benchmark**: The plan will attempt to filter the `Voices-in-the-Wild-2M` dataset for the specific `R4-B-F` distortion condition. If this subset is not present in the accessible shards, the pipeline will report "R4-B-F Not Found in Subset" rather than skipping silently, ensuring transparency.

## 3. Computational Feasibility & Constraints

### Hardware Constraints
- **CPU**: 2 Cores (Free-tier GitHub Actions).
- **RAM**: ~7 GB.
- **Disk**: ~14 GB.
- **Time Limit**: 6 hours.

### Strategy for Feasibility
1. **No GPU**: The model will be loaded with `torch.device("cpu")`. No CUDA calls will be made.
2. **Batching**: The `data_loader.py` will implement a generator-based approach, loading only `N` samples (e.g., 50-100) into memory at a time for inference, writing results immediately to disk to free RAM.
3. **Model Size**: The plan assumes the "Mega-ASR" checkpoint is small enough to fit in 7GB RAM. If the checkpoint is >4GB, the plan includes a fallback to **Mega-ASR-Lite** (the smaller baseline model explicitly identified in the repo's README), explicitly noting the switch in the report to maintain research validity.
4. **Audio Processing**: Audio files will be decoded on-the-fly using `librosa` or `torchaudio` and immediately converted to tensors, avoiding the storage of raw audio waveforms in RAM.

### Metric Stability Analysis (Reframed from Allometric Scaling)
The reviewer questioned the scaling law (accuracy vs. compute).
- **Approach**: The plan will run inference on three distinct sample sizes (N=100, N=500, N=1000) to measure the **stability** of the WER metric.
- **Metric**: Report WER and confidence interval (via bootstrapping) for each sample size.
- **Rationale**: This addresses the reviewer's request for data points while acknowledging that test-set size does not equate to compute scaling. The results will be framed as "Metric Stability Analysis" rather than "Scaling Law Validation."

## 4. Statistical Rigor & Validation

### WER Calculation
- **Method**: Levenshtein distance (standard edit distance).
- **Library**: `jiwer` (Python library for speech metrics).
- **Rationale**: `jiwer` is the standard for ASR evaluation and is lightweight (CPU-friendly).
- **Handling Mismatches**: If prediction length differs from ground truth, the metric handles tokenization alignment gracefully.

### Reproducibility Tolerance & Confidence Intervals
- **Target**: WER within ±1.5% of the paper's reported value.
- **Statistical Validity**: To account for sampling variance, the plan will calculate **95% Confidence Intervals** for the WER using bootstrapping (1000 resamples).
- **Comparison**: The paper's reported WER will be compared against the confidence interval of the sampled result. If the paper's value falls within the CI, the reproduction is considered successful. This prevents false negatives due to small sample sizes.

### Missing Data Handling
- If the full `Voices-in-the-Wild-2M` dataset cannot be accessed or is too large, the plan will use the verified Parquet shards to create a **stratified random sample**.
- The sample will be labeled as "Sampled Subset" in all reports to maintain scientific integrity.

## 5. Risk Assessment

| Risk | Impact | Mitigation Strategy |
|:--- |:--- |:--- |
| **Model too large for RAM** | Critical (Job fails) | Fallback to **Mega-ASR-Lite**; explicit error logging. |
| **Inference too slow** | High (Timeout) | Reduce sample size; optimize batch size; skip non-critical benchmarks. |
| **Dataset variable mismatch** | High (Invalid results) | Pre-flight validation script checks for `audio_path` and `text` fields; path resolution check for NOIZEUS. |
| **Paper claims unverifiable** | Medium (No conclusion) | Report "Unable to verify" with detailed logs of environment and data used. |
