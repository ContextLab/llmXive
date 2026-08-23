# Quickstart: Quantization Robustness of Multi-Effect LoRA Adapters

## Prerequisites

- Python 3.10+
- 16GB+ RAM (recommended for smooth CPU execution)
- GitHub Actions Runner (or local machine with equivalent resources)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## Configuration

1. Edit `code/config.yaml` to define your prompts, seeds, and model paths.
2. Ensure the `adapter` path points to a valid multi-effect LoRA adapter (safetensors).

## Running the Pipeline

1. **Baseline Generation (FP16)**:
   ```bash
   python code/main.py --phase baseline
   ```
   This generates a set of images and computes baseline metrics.

2. **Quantization and Generation (INT8, INT4)**:
   ```bash
   ./code/wrapper.sh python code/main.py --phase quantize
   ```
   **Note**: The `wrapper.sh` script handles OOM detection (Exit Code 137) and skips the affected level gracefully.

3. **Analysis**:
   ```bash
   python code/main.py --phase analysis
   ```
   This runs the Bayesian hierarchical model and correlation analysis.

## Output

- **Results**: `data/results.csv` (aggregated metrics)
- **Analysis**: `data/analysis_results.json` (statistical outputs)
- **Subspace Ranks**: `data/subspace_ranks.json`
- **State**: `state/project.yaml` (hashes and versioning)

## Troubleshooting

- **Memory Error**: If the runner runs out of RAM, the `wrapper.sh` script will detect the out-of-memory exit code and skip the current quantization level. If the entire job exceeds 7GB, the experiment is aborted with 'MemoryLimitExceeded'.
- **Quantization Failure**: If `torch.ao.quantization.dynamic_quant` fails, check the logs for "Backend Unavailable" and ensure `backend='dynamic'` is supported.
- **Model Loading**: Ensure the adapter file is a valid `safetensors` file and contains the expected keys.
