# llmXive Follow-up: Extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

**Project ID**: PROJ-907-llmxive-follow-up-extending-rethinking-c

## Overview

This project investigates the feasibility of replacing dynamic cross-layer routing in Diffusion Transformers (SiT) with a static, canonical routing map derived from empirical analysis of dynamic routing weights. By tracing the routing behavior of a pre-trained SiT-XL model on ImageNet validation data, we derive a static approximation and benchmark its performance (FID) and efficiency (latency) against the original dynamic baseline.

### Key Objectives
1. **Trace Dynamic Routing**: Record routing weight matrices at every timestep for a subset of ImageNet validation images.
2. **Derive Canonical Map**: Cluster timesteps based on routing similarity to generate a static routing map or fallback to a global average.
3. **Benchmark Static Approximation**: Compare the static model against the dynamic baseline in terms of generation quality (FID) and inference latency.
4. **Statistical Validation**: Perform significance testing and sensitivity analysis on the derived map.

## Prerequisites

- **Python**: 3.10+
- **Hardware**: CPU (optimized) or GPU (CUDA 11.8+). This project includes CPU-optimized paths.
- **Disk Space**: ~15GB (for ImageNet validation set and model checkpoints)
- **RAM**: Minimum 16GB recommended for benchmarking; 7GB+ for tracing (batch size 1).

## Installation

1. **Clone the repository** and navigate to the project directory:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code
 ```

2. **Create a virtual environment** (optional but recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 # Install PyTorch CPU version first (if not using CUDA)
 pip install torch==2.3.0+cpu torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cpu

 # Install remaining dependencies
 pip install -r requirements.txt
 ```

4. **Configure environment variables**:
 Create a `.env` file in the project root (or copy from `.env.example` if provided) with the following defaults:
 ```ini
 TRACE_SET_SIZE=100
 BENCHMARK_SET_START=100
 RANDOM_SEED=42
 ```

## Project Structure

```text
code/
├── src/ # Core implementation modules
│ ├── model_loader.py # Load SiT-XL model
│ ├── data_loader.py # Real ImageNet data fetching (streaming)
│ ├── tracing.py # Dynamic routing trace execution
│ ├── clustering.py # Clustering logic for canonical map
│ ├── canonical_map.py # Derive and save static map
│ ├── static_model.py # Static routing model wrapper
│ ├── benchmark.py # Inference benchmarking (latency/FID)
│ ├── metrics.py # FID calculation (InceptionV3)
│ ├── stats_analysis.py # Statistical significance tests
│ ├── sensitivity.py # Threshold sensitivity sweep
│ └── utils.py # Helpers (batching, memory guard)
├── tests/ # Unit and integration tests
├── data/ # Generated data artifacts
│ ├── routing_cache/ # Intermediate routing tensors & cluster centers
│ ├── imagenet_trace/ # (Optional) Cached trace subsets
│ ├── imagenet_benchmark/ # (Optional) Cached benchmark subsets
│ └── results/ # Final logs, CSVs, JSON reports
├── docs/ # Documentation
│ ├── README.md # This file
│ ├── usage.md # Detailed usage instructions
│ ├── api.md # API reference (generated)
│ └── memory_report.md # Memory analysis report
└── requirements.txt # Python dependencies
```

## Usage

### 1. Trace Dynamic Routing (User Story 1)
Generates routing weight matrices and derives the canonical map.
```bash
python src/tracing.py
python src/clustering.py
python src/canonical_map.py
```
*Output*: `data/routing_cache/canonical_map.json`

### 2. Benchmark Static vs. Dynamic (User Story 2)
Compares the static approximation against the dynamic baseline.
```bash
python src/benchmark.py
```
*Output*: `data/results/benchmark_results.csv`, `data/results/benchmark_results.json`

### 3. Statistical & Sensitivity Analysis (User Story 3)
Performs significance testing and threshold sweeps.
```bash
python src/stats_analysis.py
python src/sensitivity.py
python src/final_report.py
```
*Output*: `data/results/statistical_analysis.json`, `data/results/sensitivity_sweep.json`, `data/results/final_report.json`

### 4. Memory Profiling
Analyzes memory usage from trace logs.
```bash
python src/analyze_memory.py # (If available) or review data/results/memory_profile_raw.jsonl
```

## Data Integrity & Reproducibility

- **Real Data Only**: All data is fetched directly from the HuggingFace `imagenet-1k` dataset using the `datasets` library in streaming mode. No synthetic data is generated or used as a fallback.
- **Data Hygiene**: The system logs the HuggingFace dataset version ID and SHA-256 checksums of downloaded shards to `data/results/tracing_log.jsonl` and `data/results/benchmark_results.json`.
- **Reproducibility**: Random seeds are controlled via the `RANDOM_SEED` environment variable. The trace set uses the first `N` validation images, and the benchmark set uses the subsequent `M` images to ensure disjointness.

## Running Tests

```bash
pytest tests/ -v
```

## License

This project is for research purposes. Please refer to the original SiT and Diffusers repositories for licensing information regarding the base models.

## Contributing

1. Ensure all new code passes `ruff check` and `black` formatting.
2. Write unit tests for new functionality in `tests/unit/`.
3. Update `docs/usage.md` if CLI arguments change.
4. Ensure data loaders do not contain synthetic fallbacks (fail loudly).