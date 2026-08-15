# Research: Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance

## Executive Summary

This research plan addresses the hypothesis that higher soil microbiome diversity correlates with reduced plant disease incidence. The methodology relies on secondary data analysis of 16S rRNA amplicon sequencing and plant disease records. A critical finding of the research phase is the **absence of a verified open-source dataset** that simultaneously contains matched 16S rRNA data and plant disease incidence records with sufficient metadata (GPS, Date) for joining.

**Revised Strategy**: The implementation strategy is a **Data Availability Gate**:
1.  **Primary Path**: Attempt to join available OTU data with available Disease data using metadata.
2.  **Gate**: If the join yields < 30 samples or if Disease data is missing, the pipeline **HALTS** and generates a `verification_report.json` documenting the missing variables.
3.  **No Synthetic Data**: The plan explicitly **DOES NOT** generate synthetic disease incidence labels for the research analysis. Synthetic data is only used for unit testing the code logic (separate from the research pipeline).

## Dataset Strategy

### Verified Datasets (Cited Sources)

The following datasets are the **only** sources used, as per the "Verified datasets" block.

| Dataset Type | Source Name | Verified URL / Loader | Status | Variables Available |
| :--- | :--- | :--- | :--- | :--- |
| **OTU/ASV Tables** | `bio-ontology-research-group/otu-taxa-paper-artifacts` | `datasets.load_dataset("bio-ontology-research-group/otu-taxa-paper-artifacts")` | **Available** | OTU/ASV tables, Taxonomy, Metadata (if present) |
| **OTU/ASV Tables** | `otuzucbit/turkishloyd` | `datasets.load_dataset("otuzucbit/turkishloyd")` | **Available** | Parquet data (likely metadata/labels) |
| **OTU/ASV Tables** | `kali-ai/otus` | `datasets.load_dataset("kali-ai/otus")` | **Available** | JSON OTU data |
| **Disease Incidence** | **N/A** | **NO verified source found** | **MISSING** | **No dataset with matched disease incidence + GPS/Date exists in the verified list.** |
| **GPS/Location** | `Nazarko/2D_GPS_Accelerometer` | `datasets.load_dataset("Nazarko/2D_GPS_Accelerometer")` | **Available** | GPS coordinates (Accelerometer data, not soil) |
| **Climate/Env** | `GPS-Lab/ClimateIQA` | `datasets.load_dataset("GPS-Lab/ClimateIQA")` | **Available** | Climate QA (not disease) |

**Critical Decision**: The spec requires matching `OTU` data with `Disease Incidence` data. The verified list contains **OTU** sources but **NO** disease incidence source.
-   **Action**: The code will download the OTU data. It will attempt to download any disease data from the "Verified" list (none exist).
-   **Result**: The join will fail.
-   **Mitigation**: The pipeline will trigger the `[MISSING_VARIABLE: disease_incidence]` flag (FR-008). The pipeline will **HALT** and generate a `verification_report.json`. No statistical models will be run on synthetic data.

**Proxy Variable Rejection**: The plan explicitly rejects using proxy variables (e.g., climate) to generate disease incidence labels. Such an approach would confound the analysis and invalidate the biological hypothesis.

### Data Acquisition Plan

1.  **Download OTU Data**: Use `datasets.load_dataset("bio-ontology-research-group/otu-taxa-paper-artifacts")` to retrieve the OTU table.
2.  **Download Disease Data**: Attempt to find a source. Since none is verified, log `MISSING_VARIABLE`.
3.  **Matching**: Attempt to join on GPS/Date. Since Disease data is missing, this step will fail.
4.  **Gate**: If join fails, generate `verification_report.json` and halt.

## Statistical Methodology

### Model Specification
-   **Response**: Disease Incidence (Proportion 0-1). **Required**.
-   **Predictor**: Alpha Diversity (Shannon, Simpson, Faith's PD).
-   **Random Effects**: Plant Species (if available), Geographic Region (if available).
-   **Model Type**: Binomial Generalized Linear Mixed-Effects Model (GLMM) or Beta Regression.
-   **Correction**: Benjamini-Hochberg (FDR) for multiple comparisons (FR-010).

**Constraint**: If `disease_incidence` is missing, the model is **NOT** run. The pipeline halts.

### Power Analysis (FR-015)
-   **Alpha**: 0.05 (Verified: Wikipedia).
-   **Target Power**: 0.80.
-   **Effect Size**: 0.1 (Small to Medium).
-   **Calculation**: Use `pwr` or `statsmodels` power analysis. If N < required, report power limitation. If data is missing, report 'Insufficient Data'.
-   **Note**: Power analysis is conditional on data availability. If data is missing, the analysis is skipped.

### Robustness Checks
-   **Permutation Tests**: 10,000 permutations to validate correlation significance.
-   **Stratification**: If multiple crop types exist (unlikely in fallback), stratify analysis.
-   **Collinearity**: Check VIF if multiple diversity metrics are used.

## Ethical & Reproducibility Considerations

-   **Causal Claims**: All findings will be framed as **associational** (FR-009).
-   **Data Fabrication**: No real disease data is fabricated. Synthetic labels are **NOT** used for the research analysis.
-   **Reproducibility**: All seeds pinned. All code in `code/analysis/`.