# Quickstart: Counterfactual Inspector Agent

## 1. Prerequisites

- Python 3.11+
- Git
- A GitHub account (for CI/CD)
- Access to HuggingFace (for datasets)

## 2. Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-follow-up
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

4. **Verify installation**:
 ```bash
 python -c "import pandas; import scipy; print('Dependencies OK')"
 ```

## 3. Running the Pipeline

### 3.1 Single Dataset Analysis

To run the Counterfactual Inspector on a single dataset (e.g., `synthetic_text_to_sql`):

```bash
python code/main.py --dataset "https://huggingface.co/datasets/gretelai/synthetic_text_to_sql/resolve/main/synthetic_text_to_sql_test.snappy.parquet" --output output/story.json
```

**Expected Output**:
- `output/story.json`: Contains the integrated story with baseline and counterfactuals.
- Console logs: Progress updates, warnings (e.g., "Low Power", "No counterfactuals found").

### 3.2 Batch Analysis (50 Datasets)

To run the evaluation on all verified datasets:

```bash
python code/main.py --batch --output output/batch_results.json
```

This will:
1. Load each dataset from the `research.md` "Verified datasets" list (expanded to 50).
2. Generate baseline (Standard & Random) and counterfactual narratives.
3. Compute evaluation metrics (SC-001 to SC-004).
4. Save results to `output/batch_results.json`.

### 3.3 Running Tests

```bash
pytest tests/ -v
```

- **Unit Tests**: Verify statistical logic, imputation, and query generation.
- **Integration Tests**: Verify end-to-end pipeline flow.
- **Contract Tests**: Verify JSON schema compliance.

## 4. Reproducibility

- **Random Seeds**: Set in `code/config.py` (default: a configurable seed).
- **Data Checksums**: Verified at runtime; mismatches raise an error.
- **Version Pinning**: All dependencies in `requirements.txt`.

## 5. Troubleshooting

| Issue | Solution |
|-------|----------|
| **Dataset not found** | Verify URL in `research.md` and network access. |
| **Low Power Warning** | Dataset has $n < 30$. Results are flagged; interpret with caution. |
| **No Counterfactuals Found** | Data may be consistent with baseline. System logs "None" (expected behavior). |
| **LLM Timeout** | Check `code/config.py` for timeout settings; reduce model size or use API. |
| **Memory Error** | Subset data (e.g., `--rows 5000`) or increase RAM limit. |

## 6. Next Steps

- **Extend Datasets**: Add new verified datasets to `research.md` and `data/loader.py`.
- **Tune Thresholds**: Adjust correlation/p-value thresholds in `narrative/inspector.py`.
- **Improve Rubric**: Refine expert scoring logic in `evaluation/rubric.py`.
