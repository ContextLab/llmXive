# Quickstart: llmXive follow-up: extending "LoopCoder-v2"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (token for gated models if required, though CodeLlama-7b-Instruct-hf is public)
- (Optional) Kaggle account for GPU offload (handled automatically by runtime)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## CPU Validation Mode (N=50)

Run a small-scale validation to verify the pipeline logic without requiring GPU resources.

1. **Configure**:
   Edit `code/config.json` to set `max_samples = 50`, `max_mbpp_samples = 50`, and `device = "cpu"`.

2. **Run Entropy & Convergence**:
   ```bash
   python code/src/entropy.py --mode validation
   python code/src/inference.py --mode validation
   ```

3. **Run Router & Robustness**:
   ```bash
   python code/src/router.py
   python code/src/robustness.py
   ```

4. **Verify Outputs**:
   Check `data/processed/` for `entropy_results.csv`, `convergence_results_core.csv`, `router_model.pkl`.

## GPU Full Analysis Mode

Run the full scientific analysis on the complete dataset.

1. **Configure**:
   Edit `code/config.json` to set `max_samples = null` (full dataset), `max_mbpp_samples = 500`, and `device = "cuda"`.
   Ensure `load_in_8bit = true` to fit 7B model in VRAM.

2. **Run Pipeline**:
   ```bash
   python code/src/entropy.py --mode full
   python code/src/inference.py --mode full
   python code/src/router.py
   python code/src/robustness.py
   ```

3. **GPU Offload (Automatic)**:
   If running on GitHub Actions, the runtime detects CUDA requirements and offloads to Kaggle. No manual intervention needed.

4. **Verify Outputs**:
   Check `data/processed/` for all CSVs, JSONs, and model artifacts.

## Troubleshooting

- **Memory Error**: Ensure `load_in_8bit` is enabled. If VRAM > 16GB, reduce `max_samples`.
- **Dataset Download Fail**: Verify internet access and HuggingFace token.
- **AST Clustering Error**: Ensure `ast` module is available (Python standard lib).