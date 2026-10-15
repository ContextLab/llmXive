# Quickstart: 001-static-dynamic-gap-analysis

This guide walks you through reproducing the full analysis on a fresh GitHub Actions runner (or local Linux environment). No GPU is required.

## 1. Clone the Repository & Install Dependencies
```bash
git clone https://github.com/your-org/llmxive-project.git
cd llmxive-project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins pycg, clang, scikit-learn, etc.
```

## 2. Verify Dataset Access (optional)
```bash
python -c "from datasets import load_dataset; ds = load_dataset('OpenHands/SWE-Gym-code-search', split='train', streaming=True); print(next(iter(ds))['patch_id'])"
```
If the command prints a `patch_id` without error, the dataset is reachable.

## 3. Run the Full Pipeline
```bash
python src/cli/run_pipeline.py \
  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet \
  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl \
  --output_dir $(pwd)/output \
  --seed 42
```
The script will:
1. Download and checksum the two datasets.
2. Extract static CFG/CG JSON files.
3. Compute feature vectors.
4. Train Random Forest & Logistic Regression models.
5. Evaluate and produce ROC/AUC, precision/recall.
6. Run Wald test and error‑case mining.
7. Summarize runtime & memory usage.

All artifacts appear under `output/`:
- `output/interim/` – per‑patch graph JSONs  
- `output/features/static_features.csv`  
- `output/models/` – `rf.pkl`, `lr.pkl`  
- `output/reports/` – `evaluation.csv`, `roc_curve.png`, `wald_test.csv`, `error_cases.csv`, `performance.yaml`, `final_report.md`

## 4. Inspect the Final Report
```bash
less output/reports/final_report.md
```
The markdown includes:
- AUC vs. random baseline (SC‑001)  
- Divergence rate (SC‑002)  
- Error‑category distribution (SC‑003)  
- Wald test p‑values (SC‑005)  
- Runtime & memory summary (SC‑004)

## 5. Run Contract Tests (optional)
```bash
pytest -q tests/contract
```
The test suite validates that every generated file conforms to the schemas defined in `specs/001-static-dynamic-gap-analysis/contracts/`.

## 6. Re‑run with a Sample (if memory exceeds limits)
```bash
python src/cli/run_pipeline.py \
  ... \
  --sample_fraction 0.1   # 10 % stratified sample, seed fixed
```
The pipeline will automatically note the reduced statistical power in the report.

---
