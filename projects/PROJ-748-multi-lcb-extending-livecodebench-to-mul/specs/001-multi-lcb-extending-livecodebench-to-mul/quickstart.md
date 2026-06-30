# Quickstart: Multi-LCB Benchmarking Pipeline

## Prerequisites
- Python 3.11+
- Docker installed and running (for sandbox execution)
- Access to HuggingFace Hub (token required if dataset is private)
- GitHub Actions Free Tier runner (or local equivalent with sufficient RAM) for Stage 1; Larger runner for Stage 2.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-748-multi-lcb-extending-livecodebench-to-mul
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Configuration

Create a `.env` file in the project root:
```env
HF_TOKEN=your_huggingface_token
MODEL_NAME=meta-llama/Llama-3-8b-Instruct  # Example CPU-tractable model
TEMPERATURES=0.2,0.6,1.0
SAMPLE_SIZE=100  # Tasks per language for Stage 1 (CI)
RUN_MODE=stage1  # Options: stage1, stage2
```

## Execution Workflow

### Step 1: Download & Verify Data
```bash
python code/data/download.py
# Verifies checksums and pins dataset version
```

### Step 2: Preprocess & Filter
```bash
python code/data/preprocess.py --filter-contamination
# Removes tasks released after model cutoff
# Calculates and logs exclusion rate (SC-005)
```

### Step 3: Execute Benchmarks (Stage 1 or Stage 2)
```bash
python code/execution/runner.py --mode $RUN_MODE
# Runs Docker sandbox, generates execution_log.json
# Stage 1: Uses SAMPLE_SIZE
# Stage 2: Uses ALL tasks
```

### Step 4: Statistical Analysis
```bash
python code/analysis/pca.py       # LOO-PCA & Validity Check
python code/analysis/glmm.py       # GLMM with LOO_PC1 covariate
python code/analysis/correlation.py # Pearson & Baseline Test
python code/analysis/pairwise.py    # Wilcoxon/T-tests for Constitution VI
# Generates statistical_results.json
```

### Step 5: Visualization (FR-008)
```bash
python code/viz/plots.py
# Reads statistical_results.json
# Generates radar charts and heatmaps in `results/`
```

## Validation

Run the contract tests:
```bash
pytest tests/contract/
```

Run the integration tests (subset):
```bash
pytest tests/integration/
```

## Troubleshooting

- **Docker Pull Failures**: Ensure Docker daemon is running. Check disk space (images can be large).
- **Memory Errors**: Reduce `SAMPLE_SIZE` in `.env` for Stage 1.
- **Missing Language Support**: Verify Docker images for specific languages (e.g., Rust, C++) are available in the `code/execution/docker/` directory.
- **PCA Failure**: If KMO < 0.6, the system will automatically switch to simple average fallback.