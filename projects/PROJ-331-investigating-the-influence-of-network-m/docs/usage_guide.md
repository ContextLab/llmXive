# Usage Guide: Network Motif Analysis Pipeline

This guide provides detailed instructions for using the pipeline, handling errors, and interpreting results.

## 1. Setup and Environment

### Dependencies
Ensure all dependencies from `requirements.txt` are installed:
```bash
pip install numpy scipy pandas networkx matplotlib seaborn nibabel requests reportlab tqdm joblib dipy statsmodels weasyprint
```

### Configuration
Before running the pipeline, verify `code/config.py`:
- `DATA_DIR`: Root directory for data storage.
- `HCP_ACCESS`: Whether to use S3 or local files.
- `SEED`: Random seed for reproducibility (default: 42).

## 2. Data Acquisition

{{claim:c_c234861e}} (Wikidata Q387749, https://www.wikidata.org/wiki/Q387749)
- **Streaming**: For large datasets, the pipeline streams data to avoid memory overflow.
- **Verification**: Run `scripts/verify_hcp_access.sh` to ensure connectivity.
- **Failure Handling**: If data cannot be fetched, the pipeline raises a `FileNotFoundError` or `ConnectionError`. **No synthetic data is generated.**

## 3. Processing Steps

### 3.1 Parcellation
Input: `.trk` or `.tck` streamlines, Schaefer atlas (`.nii.gz`).
Output: `data/processed/weighted_adjacency.npy`.
Method: Streamline counting between regions.

### 3.2 Binarization
Input: Weighted adjacency matrices.
Method: Compute median graph density across the cohort; threshold each subject's matrix at this value.
Output: `data/processed/canonical_binary_adj.npy`.

### 3.3 Functional Connectivity & Efficiency
Input: rs-fMRI data, binary adjacency.
Output: `data/processed/rsfc.npy`, `data/processed/global_efficiency.json`.
Method: Pearson correlation for rsFC; NetworkX `global_efficiency` for structural graph.

### 3.4 Motif Analysis
Input: Binary adjacency.
Method: Enumerate all 13 directed 3-node motifs. [UNRESOLVED-CLAIM: c_dc1bf47c — status=not_enough_info] Generate degree-preserving null models (Maslov-Sneppen). [UNRESOLVED-CLAIM: c_145cda20 — status=not_enough_info] Compute z-scores.
Output: `data/processed/motif_profiles.json`.
Timeout: 300s per subject (SC-002). Falls back to `igraph` if `networkx` exceeds limit.

## 4. Statistical Analysis

### 4.1 Correlation
- **Control Variable**: Global Node Degree.
- **Methods**: Partial Pearson and Spearman correlations.
- **Correction**: Bonferroni across all motifs.

### 4.2 Permutation Test
Run only for motifs with Bonferroni-corrected p < 0.05.
- **Null Hypothesis**: No correlation.
- **Iterations**: 1000+.

### 4.3 Power Analysis
Estimates minimum detectable effect size given N=50 and Bonferroni-adjusted alpha.

## 5. Reporting

The final report (`results/report.pdf`) includes:
- Scatter plots of motif z-score vs. rsFC strength.
- Statistical tables (r, p, corrected p).
- Methods section (extracted from `pipeline.log`).
- Sensitivity analysis (across z-thresholds 1.5, 2.0, 2.5).
- Disclaimer: "These findings are associational only and do not imply causation."

## 6. Troubleshooting

- **Timeout Errors**: If motif counting exceeds 300s, check `pipeline.log` for the "Timeout warning". The system attempts to switch to `igraph`. If that fails, the subject is skipped.
- **Data Missing**: Ensure `data/raw/.access_verified` exists. If not, run the verification script.
- **Zero Variance**: If a motif has zero variance across subjects, the report will state "insufficient variance" instead of a p-value.

## 7. Extending the Pipeline

- **New Metrics**: Add functions in `code/stats.py` and update `code/report.py` to visualize them.
- **New Motifs**: Modify `code/motifs.py` to support 4-node motifs (requires significant compute resources).
- **Custom Thresholds**: Adjust the `thresholds` list in `code/motifs.py` for sensitivity analysis.
