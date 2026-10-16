# Quickstart: 001-static-dynamic-gap-analysis

This guide walks you through reproducing the full analysis on a fresh GitHub Actions runner (or local Linux environment). No GPU is required.

## 1. Clone the Repository & Install Dependencies
```bash
git clone <repo-url>
cd llmxive-project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins pycg, clang, scikit-learn, etc.
```

## 2. Verify Dataset Access (optional)
```bash
python - <<'PY'
from datasets import load_dataset
ds = load_dataset('OpenHands/SWE-Gym-code-search', split='train', streaming=True)
print(next(iter(ds))['patch_id'])
PY
```
If the command prints a `patch_id` without error, the dataset is reachable.

## 3. Run a **dry‑run** to confirm directory creation
```bash
python src/cli/run_pipeline.py \
  --dry-run \
  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet \
  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl \
  --output_dir $(pwd)/output \
  --seed 42
```
The dry‑run performs **Phase 0 – Environment Setup** only: it creates the required directory tree

```
output/
├── interim/
├── features/
├── models/
└── reports/
```

and writes a minimal `output/reports/dry_run_success.yaml` indicating success.  
You can verify the directories exist with:

```bash
ls -R output | grep -E 'interim|features|models|reports'
```

## 4. Run the Full Pipeline
```bash
python src/cli/run_pipeline.py \
  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet \
  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl \
  --output_dir $(pwd)/output \
  --seed 42
```
The script will:
1. **Download** and checksum the two datasets.  
2. **Extract** static CFG/CG JSON files (Phase 2).  
3. **Compute** feature vectors (including `patch_size` and `lines_changed`) (Phase 3).  
4. **Train** Random Forest & Logistic Regression models (Phase 4).  
5. **Evaluate** and produce ROC/AUC, precision/recall (Phase 4).  
6. **Run** Wald test and error‑case mining (Phase 5‑6).  
7. **Summarize** runtime & memory usage (Phase 7).  

All artifacts appear under `output/`:
- `output/interim/` – per‑patch graph JSONs  
- `output/features/static_features.csv`  
- `output/models/` – `rf.pkl`, `lr.pkl`  
- `output/reports/` – `evaluation.csv`, `roc_curve.png`, `wald_test.csv`, `error_cases.csv`, `taxonomy_validation.yaml`, `performance.yaml`, `final_report.md`, **`ingestion_mode.yaml`** (always written, indicating `full` or `sampled` mode)  

## 5. Inspect the Final Report
```bash
less output/reports/final_report.md
```
The markdown includes:
- AUC vs. random baseline (SC‑001)  
- Divergence rate (FP + FN / parsable patches) (SC‑002)  
- Error‑category distribution (SC‑003)  
- Wald test p‑values (SC‑005)  
- Runtime & memory summary (SC‑004)  
- Taxonomy validation precision/recall (addresses methodology‑af888ec0)  

## 6. Run Contract Tests (optional)
```bash
pytest -q tests/contract
```
The test suite validates that every generated file conforms to the schemas defined in `specs/*-static-dynamic-gap-analysis/contracts/`.

## 7. Run with a Sample (if memory exceeds limits)
```bash
python src/cli/run_pipeline.py \
  ... \
  --sample_fraction 0.1   # 10 % stratified sample, seed fixed
```
The pipeline will automatically note the reduced statistical power in the report (methodology‑fa2760db) and still write `reports/ingestion_mode.yaml` with `mode: sampled`.
