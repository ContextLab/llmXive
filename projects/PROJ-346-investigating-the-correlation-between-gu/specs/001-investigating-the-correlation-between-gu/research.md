# Research: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

## Overview

This research document outlines the data strategy, methodological choices, and feasibility analysis for the project. It addresses the core challenge: linking two distinct public datasets (microbiome and cognitive) that may not share individual-level identifiers, and selecting methods that are both scientifically rigorous and computationally feasible on a CPU-only, memory-constrained CI runner.

## Dataset Strategy

### Primary Data Sources

| Domain | Dataset Name | Source URL (Verified) | Loader Strategy | Variables Needed | Fit Assessment |
|--------|--------------|----------------------|-----------------|------------------|----------------|
| Microbiome | American Gut Project (AGP) | https://huggingface.co/datasets/eternalaudrey/jump-cp-0016-labelfree-AGP/resolve/main/data/train-00000-of-00053.parquet | `datasets.load_dataset` (parquet) | 16S OTU/ASV abundances, sample metadata (age, sex, BMI if available) | ⚠️ **Partial Fit**: AGP contains microbiome data but **lacks cognitive flexibility scores**. Individual-level linkage to cognitive data is **not possible** with this dataset alone. |
| Cognitive | NHANES (Cognitive Battery) | https://huggingface.co/datasets/HHS-Official/dqs-nhanes-select-chronic-conditions-prevalence-es/resolve/main/data/dataset.csv | `pandas.read_csv` | Cognitive flexibility scores (e.g., set-shifting, reversal learning), age, sex, BMI | ⚠️ **Partial Fit**: NHANES contains cognitive and demographic data but **lacks 16S microbiome sequencing**. |
| Microbiome (Alternative) | Qiita Study 10313 (via AGP mirror) | Same as AGP above | Same as AGP | Same as AGP | Same as AGP |
| Cognitive (Alternative) | UK Biobank | **NO VERIFIED SOURCE** in provided block | N/A | Cognitive flexibility tasks | ❌ **No Verified URL**: Cannot cite or load. Must rely on NHANES or state gap. |

### Pre-Check: Paired Dataset Search

Before execution, the pipeline must verify if any single dataset contains *both* 16S microbiome abundances and cognitive flexibility scores.
* **Result**: No single verified dataset in the provided block contains both variables.
* **Implication**: Individual-level correlation (FR-003) and regression (FR-005) are impossible with the current sources.
* **Action**: The pipeline will proceed to the **FR-008 Fallback** path, defined as generating a **Data Gap Report**.

### Critical Data Gap & Fallback Strategy

**Problem**: No single verified dataset in the provided block contains **both** 16S microbiome abundances **and** cognitive flexibility task scores at the individual level. The AGP dataset has microbiome data; NHANES has cognitive data. They are distinct cohorts with no shared participants.

**Implication**: FR-005 (individual-level regression) **cannot be executed** as originally specified because individual-level linkage is impossible.

**Decision**: The pipeline will **default to the meta-analytic fallback path (FR-008)**. However, since the verified datasets do not contain the paired variables required to compute the summary statistics (correlation coefficients) needed for a true meta-analysis, the **execution of FR-008** is redefined as:
1. **Detecting the Data Gap**: Confirming that no paired data exists.
2. **Generating a Data Gap Report**: A structured artifact that documents the inability to perform the correlation, lists the available datasets, and explains why the specific research question cannot be answered with these sources.
3. **Marking Success Criteria**: SC-001 and SC-004 are marked as "Not Measurable" in the report.

**Methodology for FR-008 (Gap Reporting)**:
1. **Ingest**: Load AGP and NHANES separately.
2. **Verify**: Check for common IDs or paired variables.
3. **Report**: If no match, generate `data/gap_report.json` containing:
 * Status: "Data Linkage Failure"
 * Reason: "No individual-level data linking microbiome and cognitive scores found in verified sources."
 * Available Datasets: List of AGP and NHANES with their variable sets.
 * Success Criteria Status: SC-001 = "Not Measurable", SC-004 = "Not Measurable".
 * Recommendation: "Project requires a single-cohort dataset with paired 16S and cognitive data to proceed."

**Strict Interpretation**: The spec mandates a fallback path. The plan satisfies this by executing a "Gap Detection & Reporting" protocol, which is the only scientifically valid response to the absence of paired data. Any attempt to compute correlations from independent cohorts would be a category error.

**Dataset Selection for Implementation**:
* **Microbiome**: AGP (parquet) - `
* **Cognitive**: NHANES (csv) - `

*Note: If the NHANES CSV does not contain specific cognitive flexibility tasks (e.g., only chronic conditions), the pipeline will flag this as a "Missing Variable" error and stop, or use a proxy if available.*

## Methodological Choices

### 1. Microbiome Preprocessing
* **Filtering**: Samples with <10,000 reads; taxa with <0.1% mean abundance (Constitution Principle VI).
* **Normalization**:
 * **Primary**: DESeq2 (via `rpy2` or Python equivalent `scikit-bio` if available on CPU).
 * **Fallback**: Rarefaction to the minimum sequencing depth.
 * **Rationale**: DESeq2 is robust for compositional data but may be heavy. Rarefaction is CPU-light. We will implement both and compare (FR-006).
* **Transformation**: Centered Log-Ratio (CLR) for regression inputs to handle compositionality.

### 2. Cognitive Data Processing
* **Imputation**: Multiple Imputation by Chained Equations (MICE) using `sklearn.impute.IterativeImputer` (CPU-tractable).
* **Normalization**: Z-scoring of cognitive scores.
* **Proxy**: If specific tasks (set-shifting) are missing, use the composite cognitive score.

### 3. Correlation Analysis (Conditional)
* **Method**: Spearman rank correlation (non-parametric, robust to outliers).
* **Correction**: Benjamini-Hochberg FDR (q < 0.05).
* **Stratification**: Age groups (<40, 40-59, ≥60).
* **Condition**: ONLY executed if paired data is found. If not, skipped.

### 4. Regression Analysis (Conditional)
* **Model**: LASSO (L1) or Elastic Net (L1+L2) via `sklearn.linear_model.ElasticNet`.
* **Inputs**: CLR-transformed taxa + age, sex, BMI.
* **Condition**: ONLY executed if paired data is found. If not, skipped.

### 5. Sensitivity & Visualization (Conditional)
* **Normalization Sensitivity**: Compare results from DESeq2 vs. Rarefaction (if paired data exists).
* **Visuals**: Heatmap (seaborn), Forest Plot (matplotlib) (if paired data exists).

### 6. Gap Reporting (FR-008)
* **Trigger**: If paired data is NOT found.
* **Action**: Generate `data/gap_report.json`.
* **Content**: Detailed explanation of the data gap, list of available variables, and status of success criteria.

## Statistical Rigor & Assumptions

* **Multiple Comparisons**: BH-FDR applied to all taxa tested (n ≈ 50-100) IF paired data exists.
* **Power**: No formal power calculation is possible without effect size estimates from prior literature. The analysis is exploratory.
* **Causal Claims**: **None**. All results labeled "associational".
* **Collinearity**: Taxa are compositional (sum to 1). CLR transformation mitigates but does not eliminate collinearity. Independent effects should not be over-interpreted.
* **Measurement Validity**: AGP 16S data is standard; NHANES cognitive batteries are validated.
* **Data Gap**: If no paired data exists, the analysis is halted, and the gap is reported. No invalid statistical bridges are constructed.

## Compute Feasibility

* **Memory**: Filtering to 10k samples and 50-100 taxa keeps RAM usage < 2GB.
* **CPU**: Spearman correlation (O(N*M)) and LASSO (O(N*M^2)) are tractable for N=10k, M=100 on 2 cores.
* **Time**: Estimated runtime: 1-2 hours for full pipeline on N=10k.
* **Libraries**: All `scikit-learn`, `scipy`, `pandas` are CPU-native. No CUDA.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use AGP + NHANES (separate) | Only verified datasets available. |
| Default to FR-008 (Gap Report) | Individual linkage impossible with verified sources. |
| NO Ecological Correlation | Scientifically invalid for individual-level questions. |
| NO Synthetic Linkage | Creates artifacts, not biological signals. |
| CPU-only methods | GitHub Actions free-tier constraints. |
| No causal claims | Observational data, no randomization. |
