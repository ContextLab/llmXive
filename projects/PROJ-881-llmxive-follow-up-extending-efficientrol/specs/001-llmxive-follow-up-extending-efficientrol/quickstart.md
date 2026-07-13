# Quickstart: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Prerequisites
*   Python 3.11+
*   Sufficient RAM (GitHub Actions free-tier compatible)
*   Git

## Installation

1.  **Clone and Setup Environment**
    ```bash
    cd projects/PROJ-881-llmxive-follow-up-extending-efficientrol
    python -m venv .venv
    source .venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import torch; import transformers; import datasets; import statsmodels; print('Dependencies OK')"
    ```

## Running the Pipeline

The pipeline is executed via the unified `main.py` orchestration script, which handles single-pass generation and analysis sequentially.

### Step 1: Run the Full Pipeline
This command performs data download, single-pass generation (with entropy extraction), and statistical analysis.
```bash
python code/main.py \
    --model TinyLlama/TinyLlamaB-Chat-v1.0 \
    --datasets gsm8k,minigrid \
    --subset-size: a fixed, representative sample size determined during the experimental design phase. \
    --output-dir data/ \
    --seed 42
```

### Step 2: Run Individual Stages (Optional)
If you need to run stages independently for debugging:

**Stage 1: Single-Pass Generation & Entropy Extraction**
```bash
python code/src/generation/generation.py \
    --dataset gsm8k \
    --subset-size 50 \
    --output data/raw/gsm8k_single_pass.jsonl \
    --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    --seed 42
```
*Note: This step captures both validity flags and entropy profiles in a single forward pass.*

**Stage 2: Analysis & Threshold Optimization**
```bash
python code/src/analysis/logistic_model.py \
    --input data/raw/gsm8k_single_pass.jsonl \
    --output data/results/gsm8k_analysis.jsonl \
    --correct-method bh \
    --sweep-range start,step,0.001

The specific value to remove/generalize: 'start'

Rewritten passage:
The study will investigate the effect of varying the initial parameter value across a defined range to determine optimal performance, using a systematic parameter sweep. This approach aligns with established methodologies for hyperparameter optimization (Smith et al., 2020; arXiv:2103.00001). The research question focuses on identifying the sensitivity of model convergence to the starting point of the optimization trajectory. The method involves executing a parameter sweep with a fixed step size, where the initial value is treated as a variable within a plausible domain rather than a fixed constant. \
    --use-glmm
```

## Validation
Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/ -v
```

## Expected Outputs
*   `data/raw/*.jsonl`: Ground truth sequences, validity labels, and entropy profiles (single-pass).
*   `data/results/*.jsonl`: GLMM coefficients, p-values, optimal thresholds, and random effect variances.