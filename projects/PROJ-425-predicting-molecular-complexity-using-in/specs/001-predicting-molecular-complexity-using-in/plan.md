# Implementation Plan: Predicting Molecular Complexity Using Information Theory

**Branch**: `001-predict-molecular-complexity` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-molecular-complexity/spec.md`
**Input**: Feature specification from `specs/001-predicting-molecular-complexity/spec.md`

## Summary

This feature implements an observational study to determine if information-theoretic molecular complexity metrics (Shannon entropy of vertex degrees and Lempel-Ziv compression length of canonical SMILES) correlate with established chemical properties (Synthetic Accessibility Score and QED). The implementation uses a CPU-only pipeline: fetching a stratified random sample from a verified HuggingFace PubChem dataset, computing metrics using RDKit, performing Pearson and Spearman correlation analysis with bootstrap resampling for stability, and applying multiple-comparison corrections. All results are framed as associational.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `rdkit` (v2023.09+), `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `datasets`  
**Storage**: Local CSV/Parquet files in `data/`, JSON/HTML reports in `reports/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier: limited CPU resources, 7GB RAM, no GPU)  
**Project Type**: Data analysis / CLI script  
**Performance Goals**: Complete full analysis (download, compute, bootstrap, plot) in ≤ 45 minutes; peak memory ≤ 4 GB.  
**Constraints**: No GPU usage; chunked processing required for initial dataset load; strict retry logic and per-molecule timeouts for robustness.  
**Scale/Scope**: Stratified random sample of a large number of molecules from the verified M dataset to ensure chemical diversity and tractability.

> **Note on Dataset Strategy**: The spec mentions "PubChem CID -5000". Directly querying the PubChem API for [deferred] individual CIDs with retry logic on a CI runner poses a high risk of rate-limiting failures and timeout. Furthermore, the verified HuggingFace dataset (`sagawa/pubchemm-canonicalized`) does not contain a contiguous range of CIDs 1-5000. To ensure **representativeness** and **reproducibility**, the plan adopts a **stratified random sample** from the verified dataset. This addresses the selection bias concern of early CIDs and ensures the sample reflects general chemical space. The analysis will filter the dataset to a representative sample of [deferred] valid entries.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. Data source is a fixed HuggingFace dataset URL. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Dataset URL sourced from verified list. **Reference-Validator Agent** will verify this citation before execution. RDKit implementations of SA/QED are standard. |
| **III. Data Hygiene** | **PASS** | Raw dataset downloaded to `data/` with **checksum computed and recorded** in `state/`. Derived metrics saved as new files. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All stats in `reports/` generated directly from `code/` output. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts (data, code, reports) will be hashed. State file updated on changes. |
| **VI. Computational Graph Integrity** | **PASS** | Graph conversions (SMILES -> Mol -> Adjacency) strictly use RDKit. **Raw SMILES and computed LZ length are stored side-by-side** in `data/processed/metrics.csv` for verification. |
| **VII. Statistical Validation Rigor** | **PASS** | A sufficient number of bootstrap iterations implemented. Confidence interval calculated. Multiple-comparison correction (Bonferroni) applied. Spearman correlation included for robustness. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-425-predicting-molecular-complexity-using-in/
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, hyperparameters
│   ├── download.py          # Dataset loading logic (with chunking & retry)
│   ├── metrics.py           # Entropy, LZ, SA, QED computation (with timeout)
│   ├── analysis.py          # Correlation, bootstrap, correction, collinearity
│   ├── viz.py               # Plot generation
│   └── main.py              # Orchestration script
├── data/
│   ├── raw/                 # Downloaded parquet/csv
│   └── processed/           # Metrics CSV
├── reports/
│   ├── stats.json           # Correlation results
│   └── figures/             # Scatter plots
├── tests/
│   ├── unit/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/`) selected. The workflow is linear (Download -> Compute -> Analyze -> Plot), making a modular library structure unnecessary. All logic resides in `code/` for simplicity and reproducibility on CI.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Chunked Processing** | Spec requires ≤ 4 GB RAM. Loading the full large-scale dataset

The research question and method remain as originally planned, consistent with prior work [Citation]. (even for filtering) might exceed limits if not chunked. | Loading the full dataset without chunking would crash the 7GB runner. Chunking is used during the initial load/filter phase. |
| **Bootstrap Resampling** | Spec requires A sufficient number of iterations for CI. | Single-point correlation is insufficient for "Statistical Robustness" (US-2). |
| **Multiple-Comparison Correction** | Spec requires control of family-wise error rate. | Uncorrected p-values increase false positive risk (SC-004). |
| **Per-Molecule Timeout** | Spec requires a bounded time limit to prevent hangs on complex molecules.. | Without a timeout, a single hanging molecule could stall the entire CI job. |
| **Stratified Sampling** | Spec requires representativeness; CID 1-5000 is biased. | Sequential sampling from the 10M dataset does not guarantee CID 1-5000 and introduces bias. Stratified sampling ensures diversity. |
| **Collinearity Handling** | Entropy and LZ are highly correlated. | Treating them as independent joint predictors leads to unstable estimates. They are analyzed as distinct definitions of complexity. |


## Computational Task Ordering

1. **Dataset Verification**: Reference-Validator verifies the HuggingFace dataset URL.
2. **Download & Checksum**: `download.py` loads the dataset in chunks, computes a checksum, and records it in `state/`.
3. **Sampling**: A stratified random sample of [deferred] molecules is extracted.
4. **Metric Computation**: `metrics.py` computes Entropy, LZ, SA, QED with a A timeout per molecule is applied.. Invalid/timeout entries are logged and skipped.
5. **Analysis**: `analysis.py` performs Pearson and Spearman correlations, bootstrap resampling, and multiple-comparison correction. Collinearity (VIF) is checked.
6. **Visualization**: `viz.py` generates scatter plots.
7. **Reporting**: Final JSON and HTML reports are generated.

## Risk Mitigation

- **API Rate Limits**: Mitigated by using a verified HuggingFace dataset instead of direct API calls.
- **Molecule Hangs**: Mitigated by a s timeout per molecule in `metrics.py`.
- **Memory Overflows**: Mitigated by chunked loading and immediate sampling to [deferred] rows.
- **Statistical Bias**: Mitigated by stratified random sampling and partial correlation controlling for molecular size.
- **Circular Validation**: Mitigated by framing the study as testing *incremental* predictive power and acknowledging the topological overlap with SA.
