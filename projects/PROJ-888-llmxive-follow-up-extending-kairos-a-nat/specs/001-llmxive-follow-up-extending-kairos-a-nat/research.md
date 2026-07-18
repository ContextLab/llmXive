# Research: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Research Question

How does the minimum information density required for stable long-horizon forecasting in embodied agents scale as input modality shifts from continuous visual streams to sparse, discrete sensor streams, and what architectural properties are necessary to preserve error bounds under these constraints?

## Background & Hypothesis

### Background
The Kairos architecture utilizes a Hybrid Linear Temporal Attention mechanism designed for physical AI. While effective with continuous visual streams, its performance under sparse, discrete sensor inputs (simulating low-bandwidth edge devices) is unknown. The hypothesis is that there exists a non-linear "tipping point" in information density (bit-depth) below which the cumulative error growth rate explodes, rendering long-horizon forecasting unstable.

### Hypothesis
1. **H1**: There exists a critical quantization threshold (likely between 4-bit and 8-bit) where the Mean Squared Error (MSE) growth rate increases non-linearly.
2. **H2**: The Hybrid Linear Temporal Attention mechanism will maintain stability at 8-bit and 16-bit but degrade significantly at 4-bit compared to the continuous baseline.
3. **H3**: Statistical validation (paired t-test) will show a significant difference (p < 0.05) in error accumulation between the discrete (4-bit) and continuous modalities.

## Dataset Strategy

The study relies on the **LIBERO** benchmark dataset, which contains continuous RGB frames and proprioceptive states for embodied agents. Since no verified "JSON-serialized" dataset exists, the research pipeline must construct the discrete dataset from the raw HDF5 source.

### Verified Datasets
The following sources are verified for programmatic access and used exclusively:

| Dataset | Source URL | Usage |
|:--- |:--- |:--- |
| **LIBERO (HDF5)** | ` | Primary source for raw proprioceptive states and object positions. |
| **LIBERO (Parquet)** | ` | Alternative/Supplementary source for state vectors if HDF5 parsing fails. |

**Note**: No verified source exists for "JSON-serialized" or "CPU-only" datasets. The plan *must* generate the discrete JSON data from the raw LIBERO HDF5/Parquet sources using `code/quantize.py`. The hallucinated 'yuanty/LIBERO-fastwam' URL has been removed.

### Data Processing Plan
1. **Download**: Fetch raw HDF5/Parquet files from verified URLs.
2. **Schema Verification**: Programmatically compare the `state_vector` schema of HDF5 and Parquet sources. If they differ, abort with an error to prevent silent data corruption.
3. **Parse**: Extract proprioceptive states (positions, velocities) and collision flags.
4. **Sparsity Simulation**: Apply **temporal subsampling** (stride=2) and **random dropout** (20% rate) to simulate low-bandwidth transmission.
5. **Quantize**: Map continuous floats to discrete integers based on bit-depth (4-bit: 0-15, 8-bit: 0-255, 12-bit: 0-4095, 16-bit: 0-65535).
6. **Noise Injection**: Add Gaussian noise with a standard deviation within a low-to-moderate range to simulate sensor instability.
7. **Serialize**: Output as JSON-serialized state vectors to `data/processed/`.
8. **Ground Truth**: For evaluation, use the **clean** (noise-free) quantized state as the target to separate model error from sensor noise.

### Sample Size Definition
- **N (Episodes)**: 50 episodes per run (sourced from LIBERO-10 Documentation which lists ~400 total episodes).
- **Steps per Episode**: 200 steps.
- **Total Effective N**: [deferred] steps per run.
- **Runs**: 10 independent runs per quantization level.

## Model Strategy

### Architecture
- **Base**: Pre-trained Kairos Hybrid Linear Temporal Attention module.
- **Modification**: Replace visual embedding layers with a **fixed, untrained discrete projection layer**. This isolates the modality shift from architectural changes (FR-002).
- **Training**: CPU-only training on the discrete dataset.

### Computational Feasibility (CPU-First)
The study is designed for the GitHub Actions free-tier (a limited number of CPUs and memory).
- **Model Size**: The Kairos attention module is lightweight; the visual encoder is replaced by a small projection layer, reducing memory footprint.
- **Batch Size**: Dynamically adjusted to fit < 6GB RAM.
- **Precision**: `float32` (default CPU precision).
- **Training Time**: Target ≤ 4 hours for sampled dataset. Graceful exit at an appropriate duration.

**Decision/Rationale**:
- **CPU vs. GPU**: The method (Linear Temporal Attention on discrete vectors) is computationally light enough for CPU. No transformer fine-tuning or diffusion generation is required. The "GPU escape hatch" is **not** needed unless the pre-trained weights are incompatible with CPU (unlikely for PyTorch), but the plan assumes CPU-first execution.
- **Dataset Size**: The full LIBERO dataset may exceed RAM. The plan will sample N=50 episodes (200 steps each) to ensure feasibility while maintaining statistical power for the 10 independent runs.
- **Weight Fallback**: If pre-trained weights are missing, the system will **train a model from scratch** for 5 epochs on the continuous baseline to learn the temporal dependencies. This ensures the "stability of the mechanism" is tested, rather than testing random noise. Runs with this fallback are flagged as "Untrained" and excluded from final statistical analysis but recorded for pipeline reproducibility.

## Statistical Analysis Plan

### Metrics
- **Primary**: Mean Squared Error (MSE) between predicted and **clean** ground-truth discrete sequences.
- **Secondary**: Cumulative error growth rate over horizons **100, 250, and 500** steps (FR-004).
- **Normalization**: MSE normalized by state space dimensionality (Principle VII).
- **Entropy Check**: Verify that quantization bins capture sufficient information (entropy > threshold).

### Statistical Tests
- **Method**: Paired t-test or Wilcoxon signed-rank test (FR-005, Principle VII). **No Bayesian Hierarchical Models**.
- **Pairing**: Same **Episode ID** across modalities.
- **Variance Check**: Levene's test for equal variance. If variances are unequal, use Wilcoxon.
- **Runs**: 10 independent runs with different noise seeds per quantization level.
- **Significance**: p < 0.05.

### Sensitivity Analysis
- **Sweep**: Quantization levels **4, 8, 12, 16** bits (SC-005).
- **Output**: Error rate change and stability boundary identification.

## Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Model Weights** | High (Blocks US2/US3) | Fallback to **train-from-scratch** (5 epochs) on continuous baseline. Flag as "Untrained" and exclude from stats. |
| **RAM Exceeded** | High (Crash) | Streaming data; dynamic batch sizing; sample size reduction. |
| **Quantization Collapse** | Medium (Invalid Data) | Detect 1-bit degeneracy; flag run as "Invalid". |
| **Time Limit Exceeded** | Medium (Incomplete Results) | Checkpoint every epoch; graceful exit; report partial results. |
| **Schema Mismatch** | High (Parsing Error) | Programmatic schema verification in `download.py`. Abort if mismatch. |
| **Statistical Power** | Medium (False Negative) | N=50 episodes, 200 steps/episode, 10 runs. |
| **Noise Conflation** | Medium (Invalid Metric) | Evaluate against **clean** ground truth (noise removed). |
| **Variance Assumption** | Medium (Invalid Test) | Levene's test before t-test; fallback to Wilcoxon. |