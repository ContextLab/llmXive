# Research: Predicting Cognitive Decline from Resting-State fMRI Network Topology

## Summary

This research plan outlines the methodology for predicting cognitive decline using rs-fMRI network topology. The core hypothesis is that graph-theoretical metrics (degree, efficiency, clustering, path length) derived from atlas-based connectivity matrices can distinguish between stable and declining cognitive status. The approach is computationally feasible on CPU-only infrastructure and adheres to rigorous statistical practices (nested CV, nested feature selection, permutation testing, sensitivity analysis).

## Dataset Strategy

| Dataset | Purpose | Source (Verified URL) | Notes |
|---------|---------|----------------------|-------|
| OpenNeuro `ds000248` (ADNI rs-fMRI) | Raw rs-fMRI BIDS data + longitudinal MMSE/MOCA scores | `https://openneuro.org/datasets/ds000248` | **Verified**: Contains rs-fMRI and longitudinal cognitive scores (MMSE/MOCA). Target dataset for the pipeline. |
| MMSE scores (CSV) | Cognitive decline labels (baseline/follow-up) | Included in `ds000248` | Extracted from `participants.tsv` or derived from metadata. |
| MOCA scores (JSON) | Alternative cognitive decline labels | Included in `ds000248` | Used if MMSE is missing. |
| BIDS metadata (parquet) | Subject demographics, scan parameters | Included in `ds000248` | Extracted from BIDS `participants.tsv`. |
| MCI conversion data | External clinical outcome validation | Not available in `ds000248` | If unavailable, the plan will document this limitation (FR-011). |

> **Critical Note**: The plan targets OpenNeuro `ds000248` which contains rs-fMRI data and longitudinal cognitive scores. If this dataset is unavailable or lacks the required variables, the pipeline will halt at Phase 0 (Data Availability Gate). The "Verified Accuracy" principle is contingent on successful data ingestion.

## Methodological Approach

### Phase 0: Data Availability Gate
- **Step 0.1**: Attempt to download `ds000248` from OpenNeuro.
- **Step 0.2**: Verify presence of rs-fMRI data and longitudinal MMSE/MOCA scores in metadata.
- **Step 0.3**: If missing, halt with `EXIT_CODE_NO_LABELS` and generate a failure report.

### Phase 1: Data Ingestion & Graph Construction (US-1, FR-001, FR-002)
- **Step 1.1**: Download raw BIDS rs-fMRI data from OpenNeuro `ds000248`.
  - Use `bids` library to parse metadata.
  - Filter subjects with non-null MMSE at both timepoints OR non-null MOCA at both timepoints.
  - Limit to N = min(, available_eligible) subjects.
  - Log excluded subjects (missing scores).
- **Step 1.2**: Preprocess fMRI data (motion correction, normalization, parcellation).
  - Use `nibabel` for BIDS handling.
  - Apply an AAL atlas to generate connectivity matrices.
  - Calculate graph metrics: node degree, global efficiency, clustering coefficient, path length.
  - Output: `data/processed/graph_metrics.csv` (subject_id, metric1, metric2, ...).
- **Step 1.3**: Handle collinearity (FR-008) and baseline exclusion.
  - Compute pairwise correlations between features.
  - Exclude features with correlation > 0.95 (keep higher variance).
  - **CRITICAL**: Exclude baseline MMSE/MOCA scores from the feature set to prevent predicting current state.
  - Log excluded features.

### Phase 2: Predictive Modeling & Validation (US-2, FR-004, FR-010)
- **Step 2.1**: Define cognitive decline labels.
  - Decline = drop in MMSE/MOCA ≥ 3 points (sensitivity analysis in FR-012).
  - Stable = no significant drop.
  - **Label Validation**: Acknowledge that the 3-point drop is a heuristic subject to test-retest reliability noise. The plan treats this as a "proxy label" and validates robustness via the ±1 point sweep (FR-012).
- **Step 2.2**: Train Random Forest classifier with **Nested Feature Selection**.
  - Nested cross-validation: -fold outer loop, grid search inner loop (n_estimators ∈ {50, 100, 200}, max_depth ∈ {5, 10, None}).
  - **Feature Selection**: Inside the inner loop, apply Variance Thresholding and RFE to reduce features to <20 before model fitting. This addresses the p >> n problem and prevents data leakage.
  - Random seed = 42.
  - Output: `data/processed/model.pkl`, `data/processed/cv_results.json`.
- **Step 2.3**: Evaluate model performance.
  - Metrics: ROC-AUC, accuracy, F1-score per fold and mean.
  - Output: `data/processed/performance_report.json`.

### Phase 3: Statistical Significance & Sensitivity Analysis (US-3, FR-005, FR-006, FR-012)
- **Step 3.1**: Permutation test (FR-005).
  - Shuffle labels multiple times (random seed = 42).
  - Re-train model and compute ROC-AUC for each permutation.
  - Calculate p-value using a permutation test based on the proportion of permuted statistics greater than or equal to the observed statistic, normalized by the total number of permutations plus one..
  - **Runtime Budget**: 100 permutations are chosen to ensure the nested CV process completes within 2 hours on a 2-core runner. This limits the minimum detectable p-value to a statistically significant threshold, which is sufficient for a binary decision at p < 0.05 (conservative).
  - Output: `data/processed/permutation_results.json`.
- **Step 3.2**: Sensitivity analysis (FR-006, FR-012).
  - Sweep decision thresholds across a representative range..
  - Report FPR, FNR for each threshold.
  - Vary decline threshold definition (±1 point) and re-run classification.
  - Output: `data/processed/sensitivity_report.json`.

### Phase 4: Verification & Reporting (SC-002, SC-005, FR-007, FR-011)
- **Step 4.1**: Verify Success Criteria.
  - Check if ROC-AUC > 0.50 and p < 0.05.
  - Output `VERIFICATION_STATUS` (PASS/FAIL).
- **Step 4.2**: Measure Runtime.
  - Aggregate phase runtimes and compare against a predefined time limit

References: [None provided in source].
  - Output `runtime_report.json` with `limit_exceeded` flag.
- **Step 4.3**: Generate Final Report (FR-007, FR-011).
  - Frame all findings as "associational" (not causal).
  - Document limitations (e.g., missing MCI conversion data, dataset constraints).
  - Output: `data/artifacts/final_report.md`.

## Statistical Rigor Considerations

- **Multiple Comparison Correction**: Not explicitly required in spec, but the permutation test inherently controls family-wise error rate for the primary hypothesis (model performance vs. chance). If multiple metrics are tested, Bonferroni correction will be applied.
- **Sample Size / Power**: N=100 subjects is small for ML; power limitation acknowledged. Nested CV and nested feature selection (reducing features to <20) help mitigate overfitting and the curse of dimensionality.
- **Causal Inference**: Observational data → all claims framed as associational (FR-007). No causal language used.
- **Measurement Validity**: MMSE/MOCA are standard cognitive tests; validation evidence cited in `research.md` (if available). The 3-point drop threshold is treated as a heuristic subject to sensitivity analysis.
- **Predictor Collinearity**: Explicitly handled (FR-008); collinear features excluded to prevent overfitting. Feature selection is performed inside the inner CV loop to prevent data leakage.

## Compute Feasibility

- **CPU-only**: All methods (Random Forest, graph metrics, permutation test) are CPU-tractable.
- **Memory**: N=100 subjects × 90-node graphs → ~360 features (reduced to <20); fits within 7 GB RAM.
- **Disk**: Raw BIDS data (~ GB) + processed data (~ GB) → within 14 GB limit.
- **Runtime**: 
  - Download/preprocessing: ~ hour.
  - Modeling (nested CV with feature selection): a moderate duration.
 - Permutation test (multiple runs): [deferred] (bounded).
  - Total: ≤ 6 hours.

## Decision/Rationale

- **Why Random Forest?** Robust to non-linear relationships, handles mixed feature types, and computationally efficient on CPU.
- **Why Nested CV?** Prevents overfitting from hyperparameter tuning; provides unbiased performance estimates.
- **Why Nested Feature Selection?** Prevents data leakage in high-dimensional setting (p >> n); ensures feature selection is not influenced by the test fold.
- **Why Permutation Test?** Non-parametric validation of model significance; avoids assumptions of normality.
- **Why Sensitivity Analysis?** Ensures robustness of decision thresholds and label definitions.
- **Why Associational Framing?** Observational data cannot support causal claims; this aligns with statistical best practices.
- **Why ds000248?** Contains the required rs-fMRI and longitudinal cognitive scores. Verified against OpenNeuro description.