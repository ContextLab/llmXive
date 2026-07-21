# Compute Strategy: Streaming and GPU Offloading

This document outlines the computational strategies employed in the `PROJ-340` pipeline to handle large-scale metagenomic and sleep architecture datasets while adhering to strict resource constraints (CPU-only CI limits, memory caps) and preventing data fabrication.

## Overview

The pipeline is designed to scale from small synthetic validation sets to large real-world cohorts. To achieve this, it implements two primary scaling mechanisms:
1. **Streaming Data Ingestion**: For datasets that exceed available RAM (approx. >6GB estimated usage).
2. **GPU Offloading**: For computationally intensive models (e.g., ZINB) on large sample sizes when a GPU is available.

## 1. Streaming Data Strategy

### Trigger Conditions
Streaming mode is automatically activated when:
- The dataset size (estimated by `N_subjects × N_taxa × bytes_per_float`) exceeds the configured threshold (default: 6GB).
- The `--real-data` flag is set and the dataset source supports streaming (e.g., HuggingFace Datasets with `streaming=True`).
- The runner environment is detected as `ubuntu-latest` with limited memory (e.g., CI runners).

### Implementation Details
- **Mechanism**: The `code/ingest.py` module utilizes `datasets.load_dataset(..., streaming=True)` to iterate over data chunks rather than loading the entire dataset into memory.
- **Online Statistics**: Instead of storing the full matrix, the pipeline computes statistics (mean, variance, zero-proportion) incrementally as chunks are processed.
- **Memory Footprint**: Maintains a constant memory footprint regardless of total dataset size, limited only by the chunk size.

### Performance Characteristics
- **Latency**: Slightly higher per-sample latency due to I/O overhead and chunk processing compared to in-memory loading.
- **Throughput**: Optimized for throughput over raw speed; suitable for processing terabytes of data on standard hardware.
- **Fallback**: If streaming is not supported by the data source, the system raises `StreamingNotSupportedError` and halts, preventing silent fallback to synthetic data.

## 2. GPU Offloading Strategy

### Trigger Conditions
GPU offloading is triggered when:
- The selected correlation method is **ZINB/Hurdle** (Zero-Inflated Negative Binomial), which is computationally expensive.
- The dataset size exceeds 1,000 samples.
- The environment detects CUDA availability (`torch.cuda.is_available()` or similar).

### Implementation Details
- **Detection**: `code/analysis.py` checks for GPU availability during the method selection phase.
- **Error Handling**: If ZINB is required on a large dataset but no GPU is found, the pipeline raises `GPURequiredError`.
- **Workflow Integration**: The CI workflow (`.github/workflows/analysis.yml`) catches `GPURequiredError` and automatically re-triggers the job on a `kaggle-gpu` runner.

### Performance Characteristics
- **Speedup**: ZINB model fitting on large datasets can see a 10x-50x speedup on GPU compared to CPU.
- **Resource Usage**: Requires a runner with NVIDIA GPUs and appropriate drivers.
- **Cost**: Offloading to cloud GPU runners (e.g., Kaggle) incurs compute time costs but ensures the analysis completes within the 6-hour window.

## 3. Compute Feasibility Check

Before execution begins, `code/main.py` performs a feasibility check:
1. **Estimate RAM Usage**: Calculates expected memory based on schema and dataset metadata.
2. **Strategy Selection**:
 - If `Estimated RAM < 6GB`: Use standard in-memory loading.
 - If `Estimated RAM >= 6GB`: Switch to **Streaming Mode**.
3. **Logging**: Records the chosen strategy in `data/metadata/compute_strategy.json`.

## 4. Safety Constraints

### No Synthetic Fallback
Under no circumstances does the pipeline fall back to synthetic data if real data is requested and missing or too large to process without streaming.
- **Rule**: If `--real-data` is set and the fetch fails, the pipeline halts with `SystemExit`.
- **Rule**: If `--real-data` is set and streaming is required but unsupported, the pipeline halts with `StreamingNotSupportedError`.

### Fabrication Prevention
The `code/verify_data_integrity.py` script scans the `data/` directory post-execution to ensure no synthetic placeholders were generated during a failed real-data run.

## Examples

### Example 1: Small Dataset (In-Memory)
- **Dataset**: Synthetic validation set (N=100).
- **Strategy**: In-Memory Loading.
- **Outcome**: Fast execution, standard CPU usage.

### Example 2: Large Dataset (Streaming)
- **Dataset**: Real metagenomic cohort (N=5000).
- **Strategy**: Streaming Mode (via HuggingFace).
- **Outcome**: Execution proceeds on CPU-only runner; memory usage remains < 2GB.

### Example 3: Large Dataset + ZINB (GPU Offload)
- **Dataset**: Real metagenomic cohort (N=2000) with high zero-inflation.
- **Strategy**: Streaming + GPU Offload.
- **Outcome**:
 1. Pipeline detects ZINB requirement and large N.
 2. Detects no GPU on current runner.
 3. Raises `GPURequiredError`.
 4. CI re-runs on `kaggle-gpu`.
 5. Analysis completes with ZINB on GPU.

## Monitoring and Reporting

All compute decisions and outcomes are logged to:
- `data/metadata/compute_strategy.json`: Records the selected strategy (RAM vs. STREAMING).
- `data/results/timing_evidence.json`: Records execution times to verify the < 6-hour constraint.
- `data/results/streaming_performance_report.json` (from T063a): Detailed metrics on streaming efficiency.

## References
- **Task T058**: Implementation of streaming data loader.
- **Task T059**: Compute feasibility check logic.
- **Task T060**: GPU detection and error raising.
- **Task T061**: CI workflow for GPU offloading.
- **Task T062**: No-synthetic-fallback assertion.