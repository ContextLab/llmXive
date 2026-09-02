# Quickstart: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Prerequisites
- Python 3.11+
- `pip`
- `git`

## 1. Clone and Setup
```bash
git clone <repo-url>
cd projects/PROJ-372-assessing-sensitivity-regression-coefficients
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pre-commit install
```

## 2. Configuration
Ensure `src/utils/config.py` contains:
- `RANDOM_SEED`: 42 (or your chosen seed).
- `TIERS`: [10, 25, 50, 75, 90].
- `SUBSETS_PER_TIER`: 200.
- `CONVERGENCE_THRESHOLD`: 0.05.

## 3. Running the Pipeline
Execute the full pipeline:
```bash
python src/cli.py run
```
This will:
1.  Download datasets from verified URLs.
2.  Profile them for OLS violations (including severity classification).
3.  Generate subsets and fit OLS models.
4.  **Verify convergence** (halt if SE > 5%).
5.  Run the **Stratified Group Comparison**.
6.  **Generate stability curves** (Coefficient SD vs. Subset Size) and save to `artifacts/figures/`.
7.  Output artifacts to `artifacts/`.

## 4. Verifying Results
Check the convergence log:
```bash
cat artifacts/convergence/convergence.log
```
Inspect the stratified analysis results:
```bash
python -c "import json; print(json.dumps(json.load(open('artifacts/stratified_analysis/results.json')), indent=2))"
```
View stability curves (if generated):
```bash
ls artifacts/figures/
```

## 5. Testing
Run unit and integration tests:
```bash
pytest tests/unit -v
pytest tests/integration -v
```
Run contract tests (schema validation):
```bash
pytest tests/contract -v
```

## 6. Troubleshooting
- **OOM Error**: If memory exceeds 7GB, the script will automatically switch to streaming mode or sample a smaller subset (logged in `convergence.log`).
- **Missing Dataset**: If a verified URL is unreachable, the script skips that dataset and logs an error.
- **Convergence Failure**: If SE of SD > 5%, the script **HALTS** and logs a critical error. Do not proceed until the threshold is met or the dataset is replaced.
- **Stratified Analysis**: If no datasets fall into a severity group, that group will be skipped in the comparison.