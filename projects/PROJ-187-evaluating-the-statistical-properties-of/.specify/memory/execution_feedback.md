# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- outputs/metrics/metric_results.json: metric is null/NaN ([1].real_mean, [1].synth_mean, [1].mean_diff, [1].real_var…) — not a real measurement

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: outputs/metrics/metric_results.json: metric is null/NaN ([1].real_mean, [1].synth_mean, [1].mean_diff, [1].real_var…) — not a real measurement; 1 command(s) failed: python -m pytest -q tests/contract (rc=1)

## Failing / missing run-book commands

- python -m pytest -q tests/contract -> rc=1
E                                                                        [100%]
==================================== ERRORS ====================================
_________________ ERROR at setup of test_metric_results_schema _________________

    @pytest.fixture(scope="module")
    def schema():
        if not SCHEMA_YAML.is_file():
>           pytest.fail(f"Schema file not found: {SCHEMA_YAML}")
E           Failed: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/specs/001-statistical-fidelity/contracts/metric_results.schema.yaml

tests/contract/test_metric_schema.py:43: Failed
=========================== short test summary info ============================
ERROR tests/contract/test_metric_schema.py::test_metric_results_schema - Fail...
1 error in 0.29s



## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **6** real records with fields: dataset_name, source_database, download_url, num_rows, num_columns, feature_names, target_column, categorical_features, numeric_features, missing_value_handling, default_train_test_split.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml

# Load benchmark datasets from OpenML
datasets = [
  openml.datasets.get_dataset(1590),  # Adult
  openml.datasets.get_dataset(29),    # Credit Card Fraud Detection
  openml.datasets.get_dataset(1596),  # Covertype
  openml.datasets.get_dataset(23512), # Higgs
  openml.datasets.get_dataset(1478),  # HAR
  openml.datasets.get_dataset(44235)  # Credit Card Fraud Classification
]

records = []
for ds in datasets:
  X, y, categorical_mask, attribute_names = ds.get_data(target=ds.default_target_attribute)
  num_rows = X.shape[0]
  num_cols = X.shape[1]
  categorical_features = [attribute_names[i] for i in range(len(attribute_names)) if categorical_mask[i]]
  numeric_features = [attribute_names[i] for i in range(len(attribute_names)) if not categorical_mask[i]]
  records.append({
    'dataset_name': ds.name,
    'source_database': 'OpenML',
    'download_url': f'https://www.openml.org/d/{ds.id}',
    'num_rows': num_rows,
    'num_columns': num_cols,
    'feature_names': attribute_names,
    'target_column': ds.default_target_attribute,
    'categorical_features': categorical_features,
    'numeric_features': numeric_features,
    'missing_value_handling': 'check_missing' if X.isnull().sum().sum() > 0 else 'none',
    'default_train_test_split': None
  })

print(f'RECORDS={len(records)}')
print('FIELDS=dataset_name,source_database,download_url,num_rows,num_columns,feature_names,target_column,categorical_features,numeric_features,missing_value_handling,default_train_test_split')
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
