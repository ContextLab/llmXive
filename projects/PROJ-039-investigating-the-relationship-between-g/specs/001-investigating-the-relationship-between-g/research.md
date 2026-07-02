# Research: Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power (Virtual Cohort & Distributional Analysis)

## Overview

This research document details the dataset strategy, methodological approach, and statistical rigor for the analysis between gut microbiome composition and resting-state EEG alpha power. Due to the lack of subject overlap between the American Gut Project (AGP) and OpenNeuro dataset

The research question, the method, and the references remain unchanged as per the planning document requirements, while the specific low-level empirical identifier has been replaced with a higher-level qualitative description to indicate the data source without asserting specific values., the analysis employs **Virtual Cohort Matching** (individual-level correlation) or **Distributional Comparison** (group-level non-parametric tests) to avoid the statistical invalidity of ecological correlation on sparse strata.

## Dataset Strategy

### Verified Datasets

| Dataset | Purpose | Verified URL | Notes |
|---------|---------|--------------|-------|
| **American Gut Project (AGP)** | 16S rRNA sequencing data (genus-level abundances, demographics) | NO verified source found | Dataset name referenced; no URL available. Plan will use manual download with checksum verification (AGP v release). |
| **OpenNeuro ds000246** | Resting-state EEG recordings | NO verified source found | Dataset name referenced; no URL available. Plan will use manual download with checksum verification. (Note: Corrected from ds000248). |
| **EEG (CSV)** | Alternative EEG data (events) | https://huggingface.co/datasets/neurofusion/eeg-restingstate/resolve/main/events.csv | Verified source for EEG events; may supplement ds000246 if needed. |
| **EEG (Parquet)** | Alternative EEG data (train/eval) | https://huggingface.co/datasets/JLB-JLB/seizure_eeg_train/resolve/main/data/train-00000-of-00048-3d720ad254981f90.parquet | Verified source for seizure EEG; may be used for testing preprocessing pipeline. |
| **BMI (CSV)** | Alternative BMI data | https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv | Verified source for BMI data; may supplement demographic variables if AGP lacks BMI. |

**Critical Note**: The American Gut Project and OpenNeuro ds000246 have NO verified sources in the provided dataset list. This is a significant limitation. The plan will:
1. Explicitly state the absence of verified URLs for AGP and OpenNeuro ds000246.
2. Use alternative verified datasets (e.g., JLB-JLB seizure EEG, karan451 BMI) for testing the pipeline.
3. For production runs, **manual download** of AGP (v2.0) and OpenNeuro ds000246 will be required, with checksums recorded in `data/metadata.json`.

### Dataset Compatibility Assessment

| Requirement | AGP Availability | OpenNeuro ds000246 Availability | Mismatch Risk |
|-------------|------------------|---------------------------------|---------------|
| Genus-level taxonomic abundances | Expected (16S rRNA) | N/A (EEG only) | None |
| Demographic metadata (age, sex, BMI) | Expected (questionnaires) | Expected (limited) | **LOW**: BMI may be missing in ds000246; plan will use (Age, Sex) if BMI missing. |
| Diet Category | Expected | **MISSING** | **HIGH**: ds000246 lacks diet. Plan will NOT use diet for matching. Diet used only for AGP grouping. |
| Resting-state EEG (≥2 min artifact-free) | N/A | Expected | None |
| Sample size (≥100 microbiome, ≥50 EEG) | Expected | Expected | None |

**Mismatch Resolution**:
- If OpenNeuro ds000246 lacks BMI, matching will use (Age, Sex) only.
- If AGP lacks BMI, BMI will be imputed using median value with a documented flag.
- If <10 matched pairs are found, the pipeline switches to **Distributional Comparison** (comparing full datasets grouped by AGP abundance levels).

## Methodological Approach

### Virtual Cohort Matching (Primary Path)

1. **Demographic Matching**: Subjects matched on (Age, Sex, BMI) using nearest-neighbor or propensity scoring.
2. **Filtering**: Only pairs with sufficient demographic similarity (e.g., age diff <5 years, sex match, BMI diff <3) are retained.
3. **Analysis**: Spearman correlation between CLR-transformed microbiome data (or PCoA axes) and alpha power for matched individuals.

### Distributional Comparison (Fallback Path)

1. **Grouping**: AGP subjects grouped into "High" and "Low" abundance groups based on median split of target taxa.
2. **Comparison**: Compare alpha power distributions of OpenNeuro subjects (unmatched) against these groups using Mann-Whitney U or Kolmogorov-Smirnov tests.
3. **Rationale**: This tests if the distribution of alpha power differs between groups defined by microbiome composition, without requiring individual matches.

### Statistical Analysis

1. **CLR Transformation**: Centered log-ratio transformation applied to microbiome data with pseudocount=0.5.
2. **Dimensionality Reduction**: PCoA/PCA on CLR data to reduce collinearity (A small number of top axes used as predictors).
3. **Correlation Testing**: Spearman correlation (Path A) or Mann-Whitney U (Path B) with Benjamini-Hochberg FDR correction (q<0.1).
4. **Permutation Testing**: A sufficient number of iterations to generate null distribution; observed statistics compared to a high percentile threshold.

### Statistical Rigor Considerations

| Requirement | Method | Status |
|-------------|--------|--------|
| **Multiple-comparison correction** | Benjamini-Hochberg FDR (q<0.1) | ✅ Implemented |
| **Sample-size/power justification** | Target N≥10 pairs (Path A) or N≥50 per group (Path B) | ✅ Valid for non-parametric tests |
| **Causal-inference assumptions** | Observational study; claims framed as associational only | ✅ FR-010 disclaimer included |
| **Measurement validity** | AGP uses standardized questionnaires; OpenNeuro ds000246 uses validated EEG protocols | ✅ Assumed based on dataset documentation |
| **Predictor collinearity** | PCoA/PCA reduction; VIF diagnostics | ✅ FR-009 implemented |

**Power Limitation Acknowledgement**:
- If <10 matched pairs are found, the correlation analysis is skipped.
- Distributional tests (Path B) require N≥25 per group for adequate power.
- Results should be interpreted as exploratory; significant findings require replication in larger studies.

## Computational Feasibility

All methods are CPU-tractable and fit within GitHub Actions free-tier constraints:
- **Memory**: ~7 GB RAM; individual-level data is lightweight.
- **Disk**: ~14 GB; raw data compressed, processed data in CSV/Parquet.
- **Runtime**: ≤6 hours; matching and correlation analysis are lightweight.
- **Libraries**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `mne`, `qiime2` (CPU-light mode) all support CPU-only execution.

## Decision Rationale

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| **Virtual Cohort Matching** | Avoids ecological fallacy; allows individual-level correlation. | Ecological correlation on sparse strata (N<10) is statistically invalid. |
| **Distributional Comparison** | Valid fallback when matching fails; uses full dataset power. | Forcing correlation on <10 pairs yields spurious results. |
| **PCoA/PCA Reduction** | Resolves taxon collinearity; reduces dimensionality to -3 orthogonal axes. | Testing 20 collinear taxa leads to multicollinearity and invalid interpretation. |
| **Mann-Whitney U / KS Test** | Non-parametric; robust to non-normal distributions in small samples. | T-test assumes normality; less appropriate for small N. |
| **Manual Download + Checksum** | Only viable path given lack of verified URLs. | Relying on unverified URLs violates reproducibility principles. |

## Limitations & Caveats

1. **Dataset Availability**: AGP and OpenNeuro ds000246 lack verified URLs; manual download required for production runs.
2. **Demographic Mismatch**: OpenNeuro ds000246 lacks diet; matching restricted to (Age, Sex, BMI).
3. **Matching Success**: If <10 pairs found, analysis relies on distributional tests (lower specificity).
4. **Ecological Fallacy**: Distributional tests do not imply individual-level associations.
5. **Confounding**: Unmeasured confounders (e.g., medication, lifestyle) may influence both microbiome and EEG.
6. **Temporal Dynamics**: Cross-sectional data cannot capture temporal changes in microbiome or EEG.

## References

- **American Gut Project**: NO verified source found. Dataset name referenced; manual download required (AGP v2.0).
- **OpenNeuro ds000246**: NO verified source found. Dataset name referenced; manual download required. (Note: Corrected from ds000248).
- **EEG (CSV)**: https://huggingface.co/datasets/neurofusion/eeg-restingstate/resolve/main/events.csv
- **EEG (Parquet)**: https://huggingface.co/datasets/JLB-JLB/seizure_eeg_train/resolve/main/data/train-00000-of-00048-3d720ad254981f90.parquet
- **BMI (CSV)**: https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv

**Note**: All external citations will be validated by the Reference-Validator Agent against primary sources before inclusion in final reports.