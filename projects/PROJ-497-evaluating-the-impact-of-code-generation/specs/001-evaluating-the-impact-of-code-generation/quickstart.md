# Quickstart: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

## 1. Prerequisites

- **Python**: 3.11+
- **HuggingFace CLI**: `pip install huggingface_hub`
- **Bandit**: `pip install bandit`
- **Git**: For version control and reproducibility checks.
- **CPU/GPU**: CPU-only execution preferred; GPU available via Kaggle auto-offload if needed (though the pipeline is designed for CPU).

## 2. Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-497-evaluating-the-impact-of-code-generation
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Verify environment**:
   ```bash
   pytest tests/ --collect-only
   ```

## 3. Execution Workflow

### Step 1: Download Datasets
```bash
python code/generation/download_models.py
```
- Downloads HumanEval, MBPP datasets from verified HuggingFace sources.
- Stores in `data/raw/`.
- Generates checksums in `state/checksums.json`.

### Step 2: Generate Code Samples
```bash
python code/generation/generate_samples.py --seed 42 --models starcoder codegen --benchmarks humaneval mbpp
```
- Generates code samples for specified models and benchmarks.
- Validates samples against benchmark tests.
- Stores valid samples in `data/processed/valid_samples/`.
- **Note**: Iterates until ≥ 32 valid samples per model or 200 attempts exhausted.
- **Logs**: Invalid samples are logged for sensitivity analysis.

### Step 3: Run Static Analysis
```bash
python code/analysis/run_bandit.py --input data/processed/valid_samples/ --config code/.bandit.yaml
```
- Runs Bandit on all valid samples.
- Generates `data/processed/vulnerability_reports.csv`.

### Step 4: Calculate Metrics & Adjust for FPR
```bash
python code/reporting/validator_agent.py --sample-size 20 --output data/processed/validator_flags.csv
python code/analysis/calculate_metrics.py --input data/processed/vulnerability_reports.csv --flags data/processed/validator_flags.csv --output data/processed/fpr_metrics.json
python code/analysis/calculate_metrics.py --adjust --fpr-file data/processed/fpr_metrics.json
```
- Calculates raw and adjusted vulnerability counts.
- Applies False Positive Rate correction using the results of the manual audit.
- **Output**: `data/processed/fpr_metrics.json` (group-specific FPRs).

### Step 5: Statistical Analysis
```bash
python code/analysis/statistical_tests.py --input data/processed/vulnerability_counts.csv
```
- Runs ZINB regression (with fallback to permutation test).
- Applies Benjamini-Hochberg multiple-comparison correction.
- Outputs `data/processed/statistical_results.json`.

### Step 6: Generate Visualizations & Report
```bash
python code/reporting/generate_plots.py --input data/processed/statistical_results.json
python code/reporting/generate_report.py --input data/processed/statistical_results.json --fpr data/processed/fpr_metrics.json --images results/plots/
```
- Generates boxplots and bar charts in `results/plots/`.
- Generates `results/summary.md` with key statistics and image paths.
- **Constraint**: `summary.md` is generated *only* from `data/processed` and `results/plots`. No hardcoded values.

## 4. Verification & Reproducibility

### Checksum Verification
```bash
python code/utils/data_hygiene.py --verify
```
- Verifies SHA-256 checksums of all files in `data/`.

### Reproducibility Test
```bash
python code/utils/reproducibility.py --seed 42 --compare
```
- Runs the pipeline twice with the same seed.
- Compares outputs for identical floating-point values (≤ 1e-6 difference).
- Logs results to `state/reproducibility_logs/`.
- **Constraint**: Pipeline halts if outputs differ beyond tolerance.

### PII Scan
```bash
python code/utils/data_hygiene.py --scan-pii
```
- Scans all data and report files for PII.
- Logs results to `state/pii_scan.log`.
- **Constraint**: Pipeline halts if PII is detected.

### Test Execution
```bash
pytest tests/ -v --junitxml=state/test_results/junit.xml
```
- Runs all unit, integration, and contract tests.
- Logs results to `state/test_results/`.
- **Constraint**: Pipeline halts if any test fails.

## 5. Troubleshooting

- **Model Inference OOM**: If CPU inference fails, the system will auto-offload to Kaggle GPU (if configured). Ensure `KAGGLE_USERNAME` and `KAGGLE_KEY` are set. The pipeline is designed for CPU execution so this should not occur but is provided as a fallback.
- **ZINB Non-Convergence**: The system will automatically fall back to permutation test. Check logs for convergence status.
- **Insufficient Samples**: If < 64 valid samples, the system will flag as 'under-powered' and report power analysis results.
- **Bandit Errors**: Syntax errors in generated code are skipped and logged. Check `logs/bandit_errors.log`.

## 6. Output Artifacts

| Artifact | Location | Description |
| :--- | :--- | :--- |
| **Valid Samples** | `data/processed/valid_samples/` | Generated code files that passed benchmark tests. |
| **Vulnerability Counts** | `data/processed/vulnerability_counts.csv` | Raw and adjusted vulnerability counts per sample. |
| **FPR Metrics** | `data/processed/fpr_metrics.json` | False Positive Rate estimates from Reference-Validator. |
| **Statistical Results** | `data/processed/statistical_results.json` | ZINB/Permutation test results with p-values and effect sizes. |
| **Plots** | `results/plots/` | Boxplots and bar charts comparing vulnerability distributions. |
| **Summary Report** | `results/summary.md` | Final report with key statistics and image paths. |