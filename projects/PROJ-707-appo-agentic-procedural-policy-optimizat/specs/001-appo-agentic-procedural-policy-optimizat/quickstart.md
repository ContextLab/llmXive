# Quickstart: APPO: Agentic Procedural Policy Optimization

## Prerequisites
- Python 3.11+
- 7GB+ RAM (Recommended: 8GB+ for safety)
- Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-707-appo-agentic-procedural-policy-optimizat/code
    pip install -r requirements.txt
    ```

2.  **Download Model**:
    Ensure a quantized Llama 3.1 8B (GGUF) is available or download via:
    ```bash
    # Example using huggingface-cli (adjust for specific GGUF repo)
    huggingface-cli download TheBloke/Llama-3.1-8B-GGUF llama-3.1-8b.Q4_K_M.gguf --local-dir ./models
    ```

3.  **Verify Datasets**:
    The code will automatically download MATH, HotpotQA, and WebShop from HuggingFace on first run. Ensure internet access.

## Running the Baseline (No-Score)

Execute 5 seeds for the baseline configuration:
```bash
python cli/train.py --config baseline --seeds 0 1 2 3 4 --benchmark MATH
```

## Running the Default APPO

Execute 5 seeds for the Score-Default configuration:
```bash
python cli/train.py --config default --seeds 0 1 2 3 4 --benchmark MATH
```

## Running Ablation (Optional)

Run a subset of the ablation grid (recommended for CI):
```bash
python cli/train.py --config ablation --grid-limit 4 --seeds 0 --benchmark MATH
```

## Analyzing Results

Generate the statistical report (Kaplan-Meier):
```bash
python cli/analyze.py --input results/training_logs.csv --output results/summary_report.md
```

## Troubleshooting

- **OOM Error**: If you see "Memory Limit Exceeded", ensure you are using a 4-bit quantized model (GGUF) and not the full FP16 model.
- **Timeout**: If the job exceeds 6 hours, check `max_steps` in the config. Reduce `max_steps` to 50,000 for CI testing.
- **Dataset Missing**: If HotpotQA/WebShop fail to load, the code will fallback to MATH only and log a warning.
