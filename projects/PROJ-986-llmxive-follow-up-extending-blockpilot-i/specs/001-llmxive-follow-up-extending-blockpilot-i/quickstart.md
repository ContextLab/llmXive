# Quickstart: llmXive follow-up: extending "BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Spec"

## 1. Prerequisites

- Python 3.11+
- Git
- GitHub Actions free-tier runner (multiple vCPU, ~7 GB RAM)
- Hugging Face account (optional, for model access)

## 2. Installation

```bash
# Clone repository
git clone
cd llmxive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Running the Pipeline

### Step 1: Ground Truth Generation (Sweep)

```bash
python sweep.py --dataset gsmk --block-sizes 1,2,4,8,16,32 --samples 500 --seed 42
```

- **Output**: `data/processed/gsm8k_ground_truth.jsonl`

### Step 2: Feature Extraction

```bash
python features.py --dataset gsm8k --input data/processed/gsm8k_ground_truth.jsonl --output data/processed/gsm8k_features.jsonl
```

- **Output**: `data/processed/gsm8k_features.jsonl`

### Step 3: Model Training

```bash
python train.py --input data/processed/gsm8k_features.jsonl --target B_star --models xgboost,random_forest,decision_tree --split 0.8 --task classification
```

- **Output**: `data/models/gsm8k_xgboost.pkl`, `data/models/gsm8k_random_forest.pkl`, etc.

### Step 4: Evaluation

```bash
python evaluate.py --models data/models/ --test-data data/processed/humaneval_features.jsonl --metrics accuracy,f1,correlation,generalization
```

- **Output**: `data/processed/evaluation_results.json`

## 4. Validation

### Contract Validation

```bash
pytest tests/contract/
```

- Validates `FeatureVector`, `GroundTruth`, `Prediction` schemas.

### Integration Test

```bash
pytest tests/integration/
```

- Runs end-to-end sweep → train → evaluate on a representative subset of samples.

## 5. Expected Outputs

- **Ground Truth**: JSONL with `sample_id`, `B_star`, `acceptance_lengths`.
- **Features**: JSONL with `prompt_length`, `mean_attention_entropy`, `hidden_state_norm`.
- **Models**: Pickle files with trained classifiers.
- **Results**: JSON with Accuracy, F1, correlation, generalization gap.

## 6. Troubleshooting

- **OOM Error**: Reduce `--samples` to a lower magnitude.; ensure streaming is enabled.
- **NaN in Entropy**: Check `features.py` for NaN handling; sample excluded.
- **Timeout**: Reduce sample size; check CI logs for progress.

## 7. Next Steps

- Extend to CommonCrawl dataset.
- Add more block sizes (e.g., 64).
- Compare with neural policy baselines.