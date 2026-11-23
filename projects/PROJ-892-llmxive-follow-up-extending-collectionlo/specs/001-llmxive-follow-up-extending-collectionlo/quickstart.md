# Quickstart: Quantization Robustness of Multi-Effect LoRA Adapters

## Prerequisites
- Python 3.10+
- 16GB+ RAM (CPU mode)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Verify environment**:
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

## Running the Pipeline

### Step 1: Prepare Data (Synthesis or Download)
The pipeline will automatically attempt to download the CollectionLoRA adapter. If it fails, it will synthesize one.
```bash
python code/main.py --phase prepare
```
*This step generates `data/subspace_ranks.json` and downloads/creates the adapters.*

### Step 2: Generate Baseline (FP16)
```bash
python code/main.py --phase generate --level FP16
```
*Generates reference images and computes baseline CLIP scores.*

### Step 3: Generate Quantized Outputs
```bash
python code/main.py --phase generate --level INT8
python code/main.py --phase generate --level INT4
```
*Note: INT4 may be skipped if CPU quantization backend fails.*

### Step 4: Statistical Analysis
```bash
python code/main.py --phase analyze
```
*Runs Bayesian hierarchical model and outputs `data/analysis_results.json`.*

## Viewing Results

- **Raw Metrics**: `data/results.csv`
- **Statistical Summary**: `data/analysis_results.json`
- **Generated Images**: `data/generated/`
- **State/Hashes**: `state/artifacts.yaml`

## Troubleshooting

- **OOM Error**: If the process exits with code 137, the system logs "MemoryLimitExceeded" and skips the level. Reduce the number of seeds in `code/config.yaml`.
- **Quantization Failure**: If INT4 fails, check logs for "Backend Unavailable". The pipeline will proceed with INT8 and FP16 only.
- **Missing Adapter**: If the synthetic adapter fails to construct, verify that the 5 single-effect LoRA sources are accessible.
