# Quickstart: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Prerequisites

- Python 3.11+
- Git
- (Optional) Kaggle account for GPU offload (if CPU model is insufficient).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-881-llmxive-follow-up-extending-efficientrol
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Configure environment**:
    ```bash
    cp .env.example .env
    # Edit .env to set HF_TOKEN (if needed) and other config
    ```

## Execution Workflow

The pipeline is executed via the `main.py` entry point.

### Step 1: Data Generation (CPU)
Generates ground-truth sequences and labels.
```bash
python code/src/generation/generation.py --task gsm8k --limit 500 --streaming
python code/src/generation/generation.py --task minigrid --limit 500 --streaming
```

### Step 2: Entropy Extraction
Captures intermediate layer entropy.
```bash
python code/src/generation/instrument.py --input data/processed/sequences.jsonl --batch-size 50
```

### Step 3: Analysis
Fits GLMM and calculates metrics.
```bash
python code/src/analysis/models.py --input data/processed/merged_analysis.parquet --correction bh
```

### Step 4: Report Generation
Generates the final research report.
```bash
python code/src/analysis/report.py --input artifacts/reports/model_results.json --output artifacts/reports/final_report.md
```

## GPU Offload (Kaggle)

If the CPU run fails or requires a larger model:
1.  Push the code to a Kaggle notebook.
2.  Enable GPU in the notebook settings.
3.  The code automatically detects CUDA and switches to a quantized 7B model.
4.  Run the same commands with `--gpu` flag.

## Troubleshooting

- **OOM Errors**: Ensure `--batch-size` is set to 50 or lower. Check RAM usage with `htop`.
- **CUDA Errors**: Verify that the GPU escape hatch is triggered only when `CUDA_VISIBLE_DEVICES` is set.
- **Data Fetching**: If Hugging Face datasets fail, check network connectivity and `HF_TOKEN`.
