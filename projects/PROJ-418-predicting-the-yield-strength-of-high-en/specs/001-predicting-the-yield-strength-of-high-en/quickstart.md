# Quickstart: Predicting HEA Yield Strength

These steps assume a fresh GitHub Actions runner or a local Linux environment with Python 3.11.

## 1. Clone the repository
```bash
git clone 
cd PROJ-418-predicting-the-yield-strength-of-high-en
```

## 2. Set up the environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Prepare the dataset
If you have a **verified open HEA yield‑strength dataset** (e.g., a Zenodo archive with DOI `` containing experimentally measured `yield_strength` for single‑phase alloys), place the file in `data/hea_raw.jsonl`. The pipeline will validate the file against `contracts/dataset.schema.yaml`.  
If no such dataset is available, the pipeline will abort and indicate that a verified source is required.

## 4. Run the full pipeline
```bash
python -m src.pipeline.run \
  --seed 42 \
  --output-dir output/
```
The command will:
1. Load the verified HEA dataset from `data/hea_raw.jsonl`.  
2. Compute deterministic compositional descriptors.  
3. Perform power analysis and VIF handling.  
4. Train a Random Forest with 5‑fold CV.  
5. Evaluate on a held‑out test set and, if an independent external dataset is present, on that set as well.  
6. Compute permutation importance with Holm‑Bonferroni correction.  
7. Run three stability replicates.  
8. Write `output/report.md` and all JSON/YAML artifacts.

## 5. Inspect the report
```bash
less output/report.md
```
The report contains:
- Dataset statistics & checksum table  
- VIF summary  
- Power‑analysis justification  
- Model performance (R², Pearson *r*, bootstrap CI)  
- Descriptor‑target correlation table (training data)  
- Permutation importance with corrected *p*‑values  
- Stability ranking comparison across three seeds  
- Detailed provenance (content‑hashes, seeds, package versions) and measurement‑protocol documentation for primary and external datasets

## 6. Run the CI checks (optional)
```bash
pytest -q
ruff check src/ tests/
black --check src/ tests/
```
All checks must pass (≤ 5 `ruff` warnings, black formatting clean). The GitHub Actions workflow runs the same steps automatically on each push.
