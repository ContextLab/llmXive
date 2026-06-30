# Data Model: Predicting Cognitive Decline from Resting-State fMRI Network Topology

## Entity Definitions

### Subject
- **ID**: Unique identifier (string, e.g., "sub-001")
- **Baseline MMSE**: Integer (0–30) or null (NOT used as a feature)
- **Follow-up MMSE**: Integer (0–30) or null
- **Baseline MOCA**: Integer (0–30) or null (NOT used as a feature)
- **Follow-up MOCA**: Integer (0–30) or null
- **Decline Status**: Binary (0 = stable, 1 = decline)
- **Excluded Reason**: String (if excluded, e.g., "missing follow-up MMSE")

### Connectivity Matrix
- **Subject ID**: String
- **Matrix**: 90x90 symmetric float array (functional connectivity values)
- **Atlas**: "AAL_90"

### Graph Metrics
- **Subject ID**: String
- **Node Degree**: Float (average degree across 90 nodes)
- **Global Efficiency**: Float
- **Clustering Coefficient**: Float
- **Characteristic Path Length**: Float
- **Modularity**: Float (optional)
- **Small-worldness**: Float (optional)

### Model Output
- **Fold ID**: Integer (1–5)
- **ROC-AUC**: Float
- **Accuracy**: Float
- **F1-Score**: Float
- **Best Hyperparameters**: Dict (n_estimators, max_depth)
- **Selected Features**: List of feature names (dynamic per fold)

### Permutation Result
- **Permutation ID**: Integer (1–100)
- **ROC-AUC**: Float
- **P-value**: Float (cumulative)

### Sensitivity Report
- **Threshold**: Float (0.45, 0.50, 0.55)
- **FPR**: Float
- **FNR**: Float
- **Decline Threshold Variation**: Integer (±1 point)

### Runtime Report
- **Phase**: String (e.g., "download", "modeling")
- **Duration Seconds**: Float
- **Total Runtime Seconds**: Float
- **Limit Exceeded**: Boolean

## Data Flow Diagram

```
OpenNeuro ds000248 (raw BIDS)
       ↓
01_download_and_filter.py → Filtered subjects (N≤100)
       ↓
02_preprocess_and_parcellate.py → Connectivity matrices (size corresponding to the parcellation scheme)
       ↓
03_compute_graph_metrics.py → Graph metrics (CSV)
       ↓
08_collinearity_check.py → Cleaned feature matrix (baseline scores excluded)
       ↓
04_train_model.py → Trained RF model + CV results (nested feature selection)
       ↓
05_evaluate_model.py → Performance report (ROC-AUC, etc.)
       ↓
06_permutation_test.py → Permutation results + p-value
       ↓
07_sensitivity_analysis.py → Sensitivity report
       ↓
09_generate_report.py → Final report (associational framing)
```

## Constraints

- **Data Integrity**: Raw data never modified; derivations written to new files.
- **Memory**: Peak RAM ≤ 7 GB; dataset subset to N=100 subjects.
- **Disk**: Total usage ≤ 14 GB; raw data checksummed.
- **Reproducibility**: All random seeds are fixed for reproducibility.; library versions pinned.
- **PII**: No personally identifying information in committed data.
- **Feature Independence**: Baseline MMSE/MOCA scores are strictly excluded from the feature set.
- **Nested Feature Selection**: Feature selection is performed inside the inner CV loop to prevent data leakage.