# Quickstart: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face (optional, for model weights)
- (Optional) Kaggle account for GPU offload (auto-detected by runner).

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-881-llmxive-follow-up-extending-efficientrol
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Environment Configuration**
    Create `.env` in the project root:
    ```bash
    HF_TOKEN=your_token_here
    RANDOM_SEED=42
    MAX_EXAMPLES_PER_TASK=500
    ```

## Execution Workflow

### Step 1: Data Download & Checksumming
```bash
python code/src/data/download.py --task gsm8k --task minigrid
# Verifies checksums against known hashes (commit hash from HF dataset card metadata)
```

### Step 2: Ground Truth Generation
```bash
python code/src/generation/generation.py --task gsm8k --model tinyllama-1.1b-4bit
python code/src/generation/generation.py --task minigrid --model tinyllama-1.1b-4bit
# Outputs: data/processed/generation_baseline.jsonl
# Note: Validity labels are derived from external dataset ground truth.
# Constraint: Full autoregressive forward pass, temperature=0.0.
```

### Step 3: Entropy Extraction
```bash
python code/src/utils/entropy_calc.py --input data/processed/generation_baseline.jsonl --batch-size 50
# Outputs: data/processed/entropy_profiles.jsonl
# Note: Input is raw logits; softmax applied internally; probabilities clamped.
# Output format adheres to entropy_profile.schema.yaml.
```

### Step 4: Analysis & Modeling
```bash
python code/src/analysis/glmm_fit.py --input data/processed/merged_data.parquet
# Outputs: data/processed/results.json (AUC, p-values, thresholds, fdr_verified)
# Note: Primary method is GLMM; Clustered SE is fallback if GLMM fails.
# Note: FDR is explicitly compared against alpha=0.05.
```

## Verification

Run the test suite to ensure contract compliance:
```bash
pytest tests/ -v
```

## Troubleshooting

- **OOM Error**: If `MemoryError` occurs, the system automatically reduces batch size. If it persists, the runner will attempt to offload to the GPU escape hatch (Kaggle).
- **Missing Ground Truth**: Ensure `ground_truth` field is present in the downloaded dataset. If ambiguous (MiniGrid), the system labels a token as valid if it matches *any* known path from the dataset.
- **Convergence Failure**: If GLMM fails to converge, the system automatically falls back to Clustered SE results.
