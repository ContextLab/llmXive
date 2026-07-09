# Quickstart: Consciousness Bootstrapping

## Prerequisites

* Python 3.11+
* Git
* GitHub Account (for CI)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd PROJ-558-consciousness-bootstrapping-self-aware-a
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins `torch` to a CPU-only version to ensure compatibility with the GitHub Actions free-tier.*

4. **Download Datasets**:
 The `code/utils/data_loader.py` script handles downloads and updates `data/manifest.json` with checksums. Run:
 ```bash
 python -m code.utils.data_loader --download
 ```
 This will fetch the Pile (arXiv subset), GSM8K, and MMLU to `data/raw/`. It will also generate the teacher labels (if not present) and store them in `data/processed/`.

## Execution

### Step 1: Training

Run the training script for a single seed (e.g., seed 1):
```bash
python -m code.training.train --seed 1 --model-type recursive --epochs 1
```
*This will train the recursive model. To train the baseline, change `--model-type baseline`.*

### Step 2: Evaluation

Evaluate the trained model on GSM8K:
```bash
python -m code.evaluation.run_benchmarks --checkpoint artifacts/checkpoints/seed_1_recursive.pt --dataset gsm8k --num-paths 10
```
*This script validates the output JSON against `contracts/evaluation-schema.schema.yaml` before saving.*

### Step 3: Analysis

Run the statistical analysis across all seeds (assuming you have run training for seeds 1-5):
```bash
python -m code.analysis.stats --seeds 1,2,3,4,5 --metrics consistency,ece,roc_auc
```

## Reproducibility

To reproduce the full experiment:
```bash
# Run training for all seeds
for seed in 1 2 3 4 5; do
 python -m code.training.train --seed $seed --model-type recursive --epochs 1
 python -m code.training.train --seed $seed --model-type baseline --epochs 1
done

# Run evaluation
python -m code.evaluation.run_benchmarks --all-checkpoints --num-paths 10

# Run analysis
python -m code.analysis.stats --seeds 1,2,3,4,5

# Update state with checksums
sha256sum artifacts/checkpoints/*.pt artifacts/results/*.json > state/checksums.txt
# (In CI, this step updates the state YAML file automatically)
```

## Troubleshooting

* **OOM Error**: If you encounter "Out of Memory", reduce the `--context-length` in `config.py` or ensure `gradient_checkpointing` is enabled.
* **CUDA Error**: Ensure `torch` is installed as the CPU version (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
* **Contract Validation Error**: If `run_benchmarks.py` fails validation, check the output JSON against `contracts/evaluation-schema.schema.yaml` for missing fields or type mismatches.