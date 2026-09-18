# Quickstart: Context Fidelity vs. Model Scaling Trade-offs

## Prerequisites

- **Python**: 3.11+
- **RAM**: 7GB+ (for 7B model Q4_K_M)
- **Disk**: 14GB+ (for dataset and model weights)
- **Dependencies**: `pip install -r requirements.txt`

## 1. Environment Setup

```bash
# Clone and setup
cd projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify dependencies
python -c "import datasets, transformers, statsmodels, pandas, sentence_transformers; print('OK')"

# Verify __init__.py files exist in all Python directories
find . -type d -name "__pycache__" -prune -o -type f -name "*.py" -print | xargs dirname | sort -u | while read dir; do
  if [ ! -f "$dir/__init__.py" ]; then
    echo "Missing __init__.py in $dir"
    touch "$dir/__init__.py"
  fi
done
```

## 2. Data Preparation (Phase 1)

This step fetches the dataset, filters for complexity, and records checksums.

```bash
# Run the loader script
python loader.py --output data/filtered/swe_bench_v1.parquet --min-lines 500

# Verify checksums are recorded in state file
cat ../../state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml
```

**Expected Output**:
- `data/filtered/swe_bench_v1.parquet` created.
- `state/...yaml` updated with SHA256 hashes.
- Log: "Filtered X instances (Y% of original) with >500 relevant lines (Hybrid IR-Seeding)."

## 3. Execution (Phase 2)

Run the baseline and high-fidelity strategies.

### 3.1 Baseline Run (1B Model)
```bash
python experiments/run_baseline.py --model 1B --strategy baseline --output data/intermediate/baseline_run.jsonl
```

### 3.2 High-Fidelity Strategies (1B Model)
```bash
# TF-IDF
python experiments/run_strategies.py --model 1B --strategy tfidf --output data/intermediate/hf_run_1b_tfidf.jsonl
# Heuristic Keyword-Proxy (formerly Diff-Aware)
python experiments/run_strategies.py --model 1B --strategy diff_aware --output data/intermediate/hf_run_1b_diff.jsonl
# Summarization
python experiments/run_strategies.py --model 1B --strategy summarization --output data/intermediate/hf_run_1b_summ.jsonl
```

### 3.3 Scaling Run (7B Model)
*Note: This requires Q4_K_M quantization. Ensure enough RAM.*
```bash
# Baseline 7B
python experiments/run_scaling.py --model 7B --strategy baseline --output data/intermediate/hf_run_7b_baseline.jsonl
# High-Fidelity 7B (optional, if time permits)
python experiments/run_scaling.py --model 7B --strategy tfidf --output data/intermediate/hf_run_7b_tfidf.jsonl
```

**Timeout Handling**: If an instance exceeds 60 minutes, it is logged as "timeout" and skipped. If total runtime exceeds 72 hours, the run terminates.

## 4. Analysis (Phase 3)

### 4.1 Failure Classification
```bash
python analysis/failure_classifier.py --input data/intermediate/*.jsonl --output data/intermediate/classified_results.jsonl
```

### 4.2 Aggregation
```bash
python analysis/metrics.py --input data/intermediate/classified_results.jsonl --output data/results.csv
```

### 4.3 GLM Analysis (Firth Correction)
```bash
python analysis/glm_analyzer.py --input data/results.csv --output data/glm_results.json
```

**Expected Output**:
- `data/glm_results.json`: Contains coefficients, p-values, and interaction term significance (OR with 95% CI).
- Log: "Interaction effect OR: X.XX (95% CI: [Y.YY, Z.ZZ])."

## 5. Verification

Run the contract tests to ensure data integrity:

```bash
pytest tests/contract/ -v
```

**Checklist**:
- [ ] `data/results.csv` exists and has correct columns.
- [ ] `state/...yaml` contains checksums for all data artifacts (Parquet, JSONL, CSV).
- [ ] GLM analysis converged (no "separation" warnings, or Firth correction applied).
- [ ] All 4 strategies and 2 models are represented in `results.csv`.
- [ ] `__init__.py` files exist in all Python directories.

## 6. Troubleshooting

- **OOM Error (7B Model)**: Ensure `Q4_K_M` quantization is active. If still failing, reduce batch size in `config.py`.
- **No Instances > 500 Lines**: Check `loader.py` static analysis logic; verify `min-lines` parameter.
- **GLM Convergence Failure**: The `glm_analyzer.py` automatically switches to Firth correction; check logs for "Firth correction applied". If Firth is unavailable, the study will report "Separation Risk".
- **Missing __init__.py**: Run the setup script in Section 1 to create missing `__init__.py` files.