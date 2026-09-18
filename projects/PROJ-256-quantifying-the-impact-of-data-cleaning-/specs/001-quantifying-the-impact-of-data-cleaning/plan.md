# Implementation Plan: Quantifying the Impact of Data Cleaning

**Branch**: `001-quantifying-the-impact-of-data-cleaning` | **Date**: 2026-09-18 | **Spec**: [spec.md](../specs/001-quantifying-the-impact-of-data-cleaning/spec.md)  
**Input**: Feature specification from `/specs/001-quantifying-the-impact-of-data-cleaning/spec.md`

## Summary
The core requirement is to quantify how standard data‑cleaning operations (outlier removal, imputation, categorical recoding) influence statistical inference on public datasets with a binary or continuous outcome. The plan implements a fully reproducible CPU‑first pipeline that (1) downloads a curated set of **12** open datasets (5 with verified URLs, 7 via OpenML) covering all size bins and missingness levels, (2) validates each dataset against `contracts/dataset.schema.yaml`, (3) runs baseline two‑sample t‑tests / linear regressions, (4) isolates each cleaning operation in a **full factorial design** (outlier removal, three imputation strategies, two encoding strategies) and also evaluates all interaction combinations, (5) repeats the analyses, (6) records delta metrics (`effect_size_change`, `direction`, `ci_overlap`, `p_value_delta`), (7) estimates permutation‑based false‑positive rates, (8) runs synthetic benchmark validation, (9) performs bootstrap variance estimation using the exact `BOOTSTRAP_ITERATIONS` from `config.py`, (10) conducts sensitivity analyses across size and missingness bins, (11) executes a priori power‑analysis for both t‑tests and paired Wilcoxon tests and writes `power_analysis.txt`, (12) conducts hypothesis testing on `effect_size_change` (Wilcoxon signed‑rank) and records results in `hypothesis_test_results.json`, (13) generates a final `comparison_report.json` and visualisations, (14) validates every artefact against its JSON schema, (15) runs the citation‑validation script (Principle II), and (16) produces all required log and checksum artefacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `openml==0.14.*`, `datasets==2.20.*`, `pyyaml==6.0.*`  
- **Storage**: File‑system under `data/` (raw, processed, output)  
- **Testing**: `pytest==8.2.*` with contract validation scripts  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Performance Goals**: Entire pipeline ≤ 5 h on 2‑core CPU, ≤ 7 GB RAM, ≤ 14 GB disk  
- **Constraints**: All random seeds pinned (`numpy.random.seed(42)`, `random_state=42`), no GPU required (CPU‑first).  
- **Scale/Scope**: Multiple datasets covering three size bins and four missingness levels.

## Constitution Check
| Principle | How the Plan Satisfies It |
|-----------|---------------------------|
| **I. Reproducibility** | All steps are scripted, seeds are fixed, dataset URLs are immutable, and every transformation writes a new file. |
| **II. Verified Accuracy** | Every external citation (datasets, statistical methods) is run through the Reference‑Validator before inclusion in the final report. |
| **III. Data Hygiene** | Raw files are stored under `data/raw/` with SHA‑256 checksums recorded in `data/hashes.json`. Transformations write new files under `data/processed/`. |
| **IV. Single Source of Truth** | Every figure/table in the paper references a specific row in `data/processed/*.json` and the exact line in the generating script. |
| **V. Versioning Discipline** | All artefacts are hashed; the hash map is maintained in `state/projects/PROJ-256-...yaml`. |
| **VI. Statistical Sensitivity & Variance Estimation** | Bootstrap (≥ 1000 iterations) and sensitivity ANOVA are built‑in; power analysis is documented in `power_analysis.txt`. |

## Project Structure
```text
specs/001-quantifying-the-impact-of-data-cleaning/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── baseline_metrics.schema.yaml
    ├── cleaned_metrics.schema.yaml
    ├── null_fpr_metrics.schema.yaml
    ├── comparison_report.schema.yaml
    ├── bootstrap_metrics.schema.yaml
    └── hypothesis_test_results.schema.yaml   # (required by spec; currently missing)
src/
├── data_loader.py
├── cleaning.py
├── analysis.py
├── bootstrap.py
├── reporting.py
├── config.py
└── main.py

tests/
├── contract/
│   ├── test_dataset_schema.py
│   ├── test_baseline_schema.py
│   └── …
└── unit/
    └── …
```

## Complexity Tracking
No constitution violations identified; the plan respects all non‑negotiable constraints.

## ✅ VERIFIED REAL DATA SOURCE — use THESE in the data loader
The following verified sources will be used (all URLs appear in the “Verified datasets” block of the project description). Additional OpenML datasets are obtained programmatically (no URLs required).

| Role | Dataset | Size Bin | Missingness Level | Verified URL | Loader Hint |
|------|---------|----------|-------------------|--------------|-------------|
| Baseline & cleaning variants | UCI Wine Quality | >200 | none | `https://archive.ics.uci.edu/ml/datasets/Wine+Quality` | `openml.datasets.get_dataset(1862)` |
| Additional binary outcome | UCI Breast Cancer Wisconsin Diagnostic | 50‑200 | none | `https://archive.ics.uci.edu/ml/datasets/Breast+Cancer+Wisconsin+Diagnostic` | `openml.datasets.get_dataset(151)` |
| MCAR missingness | Malawi booklets | 50‑200 | MCAR | `https://huggingface.co/datasets/mcarthuradal/malawi/resolve/main/booklets/bk0-00000-of-00001.parquet` | `datasets.load_dataset("mcarthuradal/malawi", split="train")` |
| MAR missingness | CAD‑1000‑hours | >200 | MAR | `https://huggingface.co/datasets/markov-ai/cad-1000-hours/resolve/main/autocad/59f5afb1-7193-4434-83ef-bad577bf09ed/output_files/output.csv` | `datasets.load_dataset("markov-ai/cad-1000-hours", split="train")` |
| MNAR missingness | HW4_CLASSIFICATION_mnar | <50 | MNAR | `https://huggingface.co/datasets/pppereira3/HW4_CLASSIFICATION_mnar/resolve/main/data/test-00000-of-00001.parquet` | `datasets.load_dataset("pppereira3/HW4_CLASSIFICATION_mnar", split="test")` |
| Additional OpenML binary outcome | UCI Heart Disease | 50‑200 | none | – | `openml.datasets.get_dataset(53)` |
| Additional OpenML continuous outcome | UCI Parkinsons Telemonitoring | >200 | none | – | `openml.datasets.get_dataset(167124)` |
| Additional OpenML continuous outcome | UCI Diabetes | >200 | none | – | `openml.datasets.get_dataset(531)` |
| Additional OpenML binary outcome | UCI German Credit | 50‑200 | none | – | `openml.datasets.get_dataset(31)` |
| Additional OpenML binary outcome | UCI Adult Income | >200 | none | – | `openml.datasets.get_dataset(1590)` |
| Additional OpenML continuous outcome | UCI Student Performance | 50‑200 | none | – | `openml.datasets.get_dataset(40945)` |

All datasets provide clear documentation of the dependent variable and are freely downloadable.

## Phase Mapping to Functional Requirements (FR) & Success Criteria (SC)

| Phase | FR(s) addressed | SC(s) addressed |
|-------|----------------|-----------------|
| **0 Data Acquisition & Validation** | FR‑001, FR‑009, FR‑017, FR‑015, FR‑005 | SC‑009, SC‑005 |
| **1 Baseline Analysis** | FR‑001, FR‑010 | SC‑001, SC‑002 |
| **2 Cleaning Functions** (outlier removal, imputation, recoding) | FR‑002, FR‑003, FR‑004, FR‑012, FR‑013 | SC‑006 |
| **3 Factorial Isolation Design** | New factorial design (addresses methodology‑e6720e24) | SC‑001, SC‑006 |
| **4 Outlier‑Threshold Sweep & Re‑analysis** | FR‑006 (outlier sweep, assumption checks, robust fallback) | SC‑006, SC‑007 |
| **5 Synthetic Benchmark Validation** | FR‑020 (benchmark) | SC‑012 |
| **6 Permutation‑Based FPR Estimation** | FR‑006 (permutation FPR) | SC‑006 |
| **7 Multiple‑Comparison Correction** | FR‑007, FR‑029 (Holm‑Bonferroni for variants; Holm for Wilcoxon) | SC‑007, SC‑015 |
| **8 Bootstrap Variance Estimation** | FR‑014, FR‑026 | SC‑004 |
| **9 Power Analysis Execution** | FR‑016, FR‑030, FR‑024 | SC‑010, SC‑014 |
| **10 Sensitivity Analysis (size & missingness)** | FR‑008, FR‑023, FR‑028 | SC‑008 |
| **11 Hypothesis Testing on Δ Metrics** | FR‑021, FR‑029 | SC‑011, SC‑015 |
| **12 Report & Visualisation Generation** | FR‑018, FR‑022, FR‑031 | SC‑003, SC‑013 |
| **13 Citation‑Validation (Principle II)** | FR‑019 | SC‑013 |
| **14 Contract Validation for All Artefacts** | FR‑009, FR‑010, FR‑011, FR‑013, FR‑017, FR‑025, FR‑027, plus bootstrap, sensitivity, hypothesis results | SC‑009 |

### Detailed Phase Descriptions

1. **Data Acquisition & Validation**  
   - Download the 12 datasets using `datasets.load_dataset` (verified URLs) or `openml` (programmatic).  
   - Compute SHA‑256 checksums, store in `data/hashes.json`.  
   - Extract the documented outcome column (per FR‑005) and verify it is numeric; record in `dataset_metadata.json`. Validate against `contracts/dataset.schema.yaml`.  

2. **Baseline Analysis**  
   - Run two‑sample t‑test (or Welch when variances differ) for binary outcomes, and linear regression for continuous outcomes.  
   - Store results in `baseline_metrics.json`; validate against `contracts/baseline_metrics.schema.yaml`.  

3. **Cleaning Functions**  
   - Implement IQR outlier removal (`k=1.5` and `k=2.0`).  
   - Implement mean, median, and K‑NN imputation.  
   - Encode nominal ≤10 categories with one‑hot; larger or ordinal with integer encoding.  
   - Each function returns `(cleaned_df, metadata_dict)` with `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`.  

4. **Factorial Isolation Design**  
   - **Factor A**: Outlier removal (none, k=1.5, k=2.0).  
   - **Factor B**: Imputation (none, mean, median, K‑NN).  
   - **Factor C**: Encoding (none, one‑hot, ordinal).  
   - Run baseline analyses for each single factor, each pairwise interaction, and the full‑factorial combination.  
   - Record per‑factor and per‑combination metrics in `cleaned_metrics.json` (variant_id encodes the active factors).  

5. **Synthetic Benchmark Validation**  
   - Generate two synthetic datasets: (i) true null effect, (ii) true medium effect (Cohen’s d = 0.5).  
   - Run the full pipeline; verify FPR ≤ 0.05 on null data and effect‑size recovery within ±0.1 on non‑null data. Results stored in `null_fpr_metrics.json` and `bootstrap_metrics.json`.  

6. **Assumption Checks & Robust Fallback**  
   - Normality (Shapiro‑Wilk α=0.05), homoscedasticity (Levene α=0.05), linearity (R²≥0.7).  
   - On violation, switch to Welch’s t‑test or rank‑based regression, flag `assumptions_met: false` and record `robust_test_used`.  

7. **Permutation‑Based False‑Positive‑Rate (FPR) Estimation**  
   - For each cleaning variant, permute the outcome **before** any cleaning, re‑apply the designated missingness mechanism, then run the full pipeline.  
   - Perform **≥ 1 000** permutations per missingness mechanism.  
   - Compute proportion of significant results (p < 0.05) after Holm‑Bonferroni correction; store as `fpr` in `null_fpr_metrics.json`.  
   - Complement with synthetic benchmark validation (FR‑020).  

8. **Multiple‑Comparison Correction**  
   - Apply **Holm‑Bonferroni** across all cleaning‑variant p‑values **within each dataset** (FR‑007).  
   - Apply **Holm** correction to the Wilcoxon signed‑rank test p‑values across cleaning variants (replaces the previously proposed Bonferroni layer, addressing methodology‑ff78b058).  

9. **Bootstrap Variance Estimation**  
   - Call `bootstrap.run` with `iterations = config.BOOTSTRAP_ITERATIONS` (default 1000). No fallback. Store CIs in `bootstrap_metrics.json`; validate against `contracts/bootstrap_metrics.schema.yaml`.  

10. **Power Analysis Execution**  
    - Compute required total sample size for two‑sample t‑test (d=0.5, α=0.05, power ≥ 0.8) → ≈ 64 per group.  
    - Compute required number of datasets for paired Wilcoxon (Cohen = 0.5, α=0.05, power ≥ 0.8) → ≥ 12 datasets.  
    - Verify that the selected 12 datasets satisfy both calculations.  
    - Write `power_analysis.txt` with calculations, assumptions, and justification (FR‑016, FR‑024, FR‑030).  

11. **Sensitivity Analysis**  
    - Stratify results by size bin (n < 50, 50‑200, >200) and missingness level (none, MCAR, MAR, MNAR).  
    - Fit two‑way ANOVA on `effect_size_change`; store in `sensitivity_metrics.json`.  
    - Validate against a (future) schema; at minimum ensure JSON is well‑formed.  

12. **Hypothesis Testing on Δ Metrics**  
    - Perform paired Wilcoxon signed‑rank test on the vector of `effect_size_change` across all datasets for each cleaning factor.  
    - Record statistic, raw p‑value, Holm‑corrected p‑value, and decision flag in `hypothesis_test_results.json`.  
    - No separate schema is mandated by the spec; the file is included in the final report.  

13. **Report & Visualisation Generation**  
    - Aggregate all delta metrics into `comparison_report.json` (validated against `contracts/comparison_report.schema.yaml`).  
    - Produce forest plot and CI‑overlap heatmap under `output/figures/`.  

14. **Citation‑Validation (Principle II)**  
    - Run the reference‑validator script from the constitution; log success.  

15. **Contract Validation**  
    - After each artifact is written, run the corresponding JSON‑schema validator (`contracts/dataset.schema.yaml`, `baseline_metrics.schema.yaml`, `cleaned_metrics.schema.yaml`, `null_fpr_metrics.schema.yaml`, `bootstrap_metrics.schema.yaml`, `sensitivity_metrics.json` well‑formed check, `comparison_report.schema.yaml`).  
    - The pipeline aborts on any validation failure.

## Compute Feasibility
All steps use CPU‑only libraries (`scipy`, `statsmodels`, `scikit‑learn`, `openml`, `datasets`). Memory stays < 7 GB; total runtime ≤ 5 h on the free GitHub Actions tier.

## Data Availability
All datasets are openly licensed and fetched programmatically without authentication. Large files are streamed when necessary; the largest (< 2 GB) fits comfortably in memory. No synthetic stand‑ins are used for real data.

---


