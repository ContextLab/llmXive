# Usage Guide

This document provides usage instructions for all scripts in the llmXive follow-up project.
Ensure you have completed the setup steps in `docs/README.md` before proceeding.

## Prerequisites

- Python 3.10+
- Dependencies installed via `pip install -r code/requirements.txt`
- Environment variables configured (see `.env` or `docs/README.md`):
 - `TRACE_SET_SIZE`: Number of images for tracing (default: 100)
 - `BENCHMARK_SET_START`: Start index for benchmark set (default: 100)
 - `BENCHMARK_SET_SIZE`: Number of images for benchmarking (default: 50)
 - `RANDOM_SEED`: Random seed for reproducibility (default: 42)

## Phase 1: Trace Dynamic Routing (User Story 1)

### 1.1 Run Tracing
Execute the tracing script to record routing weight matrices from the pre-trained SiT-XL model.

```bash
cd code
python src/tracing.py
```

**Outputs:**
- `data/routing_cache/*.npy`: Routing weight matrices for each image.
- `data/results/tracing_log.jsonl`: JSON lines log of progress and memory usage.
- `data/results/memory_profile_raw.jsonl`: Detailed memory profiles.
- `data/results/dataset_verification.json`: Dataset version and checksum logs.

**Notes:**
- Processes images one-by-one to stay within memory limits (<7GB RAM). [UNRESOLVED-CLAIM: c_9b51f73b — status=not_enough_info]
- Uses the first `TRACE_SET_SIZE` images from the ImageNet validation split.

### 1.2 Run Clustering Analysis
Analyze the traced routing tensors to identify clusters of timesteps and derive a canonical map.

```bash
cd code
python src/clustering.py
```

**Outputs:**
- `data/routing_cache/cluster_centers.json`: Cluster centers for each timestep.
- `data/results/null_hypothesis_flag.json`: Flag if clustering fails (silhouette < 0.25).
- Console output: Silhouette score.

### 1.3 Derive Canonical Map
Generate the static "Canonical Routing Map" from the clustering results.

```bash
cd code
python src/canonical_map.py
```

**Outputs:**
- `data/routing_cache/canonical_map.json`: The derived static routing weights.

---

## Phase 2: Benchmark Static vs. Dynamic (User Story 2)

### 2.1 Run Benchmark
Compare the performance (latency and FID) of the static routing model against the dynamic baseline.

```bash
cd code
python src/benchmark.py
```

**Outputs:**
- `data/results/benchmark_results.csv`: Detailed results in CSV format.
- `data/results/benchmark_results.json`: Detailed results in JSON format.

**Schema:**
- `timestamp`, `model_type` (dynamic/static), `seed`, `latency_s`, `fid_score`, `fid_degradation`

**Notes:**
- Uses a disjoint set of images starting at `BENCHMARK_SET_START`.
- Validates that the benchmark set does not overlap with the trace set.
- Reports high FID degradation as a valid negative result without halting.

---

## Phase 3: Statistical Significance & Sensitivity (User Story 3)

### 3.1 Statistical Analysis
Re-run the benchmark 5 times with different seeds to compute statistical significance.

```bash
cd code
python src/stats_analysis.py
```

**Outputs:**
- `data/results/statistical_analysis.json`: Mean/std of paired differences, bootstrap results, and limitations.

**Notes:**
- Re-initializes models for each seed to ensure independence.
- Uses non-parametric bootstrap (percentile method) for 95% confidence intervals. [UNRESOLVED-CLAIM: c_162d3f32 — status=not_enough_info]

### 3.2 Sensitivity Analysis
Sweep the clustering distance threshold to test robustness.

```bash
cd code
python src/sensitivity.py
```

**Outputs:**
- `data/results/sensitivity_sweep.json`: FID degradation range across thresholds {0.01, 0.05, 0.1}.

**Notes:**
- Re-runs derivation and benchmark logic for each threshold.
- Reports the min, max, and range of FID degradation.

### 3.3 Generate Final Report
Compile all results into a single final report.

```bash
cd code
python src/final_report.py
```

**Outputs:**
- `data/results/final_report.json`: Comprehensive summary including statistical and sensitivity results.

---

## Utilities

### Memory Report Generation
Parse memory logs to generate a summary report (Dependency: T039).

```bash
cd code
python src/memory_report.py
```

**Outputs:**
- `docs/memory_report.md`: Human-readable memory analysis.
- `data/results/memory_profile.json`: Structured memory statistics.

---

## Troubleshooting

- **Memory Errors:** Ensure `TRACE_SET_SIZE` and `BENCHMARK_SET_SIZE` are set appropriately for your hardware. The scripts default to small sizes to prevent OOM.
- **Data Fetch Errors:** If ImageNet data cannot be fetched, the script will raise an exception. Check your internet connection and HuggingFace access.
- **Null Hypothesis:** If clustering fails (silhouette < 0.25), the system defaults to a global average routing map. Check `data/results/null_hypothesis_flag.json` for details.