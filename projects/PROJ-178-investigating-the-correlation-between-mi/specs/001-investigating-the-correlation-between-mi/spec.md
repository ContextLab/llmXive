# Feature Specification: Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates

**Feature Branch**: `001-mitochondrial-aging-correlation`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates in Publicly Available Datasets"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing (Priority: P1)

The system MUST successfully download, filter, and parse mitochondrial DNA variant data and sample metadata from the 1000 Genomes Project to create a unified analysis-ready dataset.

**Why this priority**: Without valid, cleaned input data, no statistical analysis can occur. This is the foundational step that enables all subsequent research.

**Independent Test**: The system can be tested by verifying the existence of a processed CSV/Parquet file containing per-sample heteroplasmy burden, haplogroup, age, sex, and ancestry PCs, with zero missing values in critical columns.

**Acceptance Scenarios**:

1. **Given** the 1000 Genomes VCF files and panel metadata are accessible, **When** the ingestion script runs, **Then** a unified dataframe is produced with ≥ 2,500 samples containing `heteroplasmy_burden`, `age`, `sex`, `population`, and `haplogroup` columns.
2. **Given** raw VCFs containing non-PASS variants, **When** the filtering step executes, **Then** only variants with `PASS` filter status and mitochondrial chromosome (`chrM`) are retained in the output matrix.
3. **Given** samples with missing age metadata, **When** the merge step completes, **Then** those samples are excluded from the final dataset, and a log entry records the count of excluded samples.

---

### User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

The system MUST perform Spearman correlation and linear regression analysis to quantify the relationship between mitochondrial heteroplasmy burden and chronological age, adjusting for confounders.

**Why this priority**: This directly addresses the core research question (correlation between mtDNA variation and aging) and generates the primary scientific result. Spearman correlation is prioritized for robustness to non-normal age distributions.

**Independent Test**: The system can be tested by running the analysis on a synthetic dataset with a known correlation (e.g., r=0.15) and verifying the model recovers a p-value < 0.05 and a coefficient sign consistent with the input.

**Acceptance Scenarios**:

1. **Given** a merged dataset of heteroplasmy burden and age, **When** the Spearman correlation is computed with covariates (sex, ancestry PCs, sequencing depth) applied via partial correlation, **Then** the output includes the correlation coefficient and p-value.
2. **Given** the fitted model results, **When** multiple hypothesis testing correction is applied, **Then** the Benjamini-Hochberg adjusted p-values are calculated for all tested associations.
3. **Given** the primary Spearman correlation results, **When** a linear regression (OLS) model is computed as a secondary check, **Then** the resulting coefficient and p-value are recorded and compared against the Spearman result.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

The system MUST execute sensitivity analyses to validate the stability of findings against threshold choices and population stratification.

**Why this priority**: This ensures the results are not artifacts of arbitrary parameters (like the 1% VAF threshold) or population structure, addressing the methodological soundness requirement for threshold justification.

**Independent Test**: The system is tested by running the sensitivity analysis with thresholds 0.5%, 1.0%, and 2.0% and verifying the output contains three distinct correlation coefficients.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the heteroplasmy burden is recalculated using thresholds of 0.5%, 1.0%, and 2.0%, **Then** the correlation coefficients for all three thresholds are reported, and the variation is documented.
2. **Given** samples from diverse continental populations, **When** the analysis is repeated within each major ancestry group (e.g., European, African, East Asian), **Then** the correlation coefficient and p-value are reported for each subgroup.
3. **Given** samples with varying sequencing depths, **When** the dataset is subsampled to equalize depth across groups, **Then** the model is re-run and the change in the heteroplasmy coefficient is recorded.

### Edge Cases

- What happens when a sample has zero heteroplasmic variants above the threshold? (System must handle zero-valued burden without crashing, treating it as a valid data point).
- How does the system handle samples where haplogroup assignment fails? (System must flag these samples and exclude them from the haplogroup-specific analysis while retaining them for the burden-only analysis if age is present).
- What if the 1000 Genomes panel file is missing the `age` column for a specific population? (System must log the missing data and proceed with available populations, explicitly noting the limitation).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse mitochondrial VCFs from the 1000 Genomes Project FTP site and merge them with sample metadata (See US-1).
- **FR-002**: System MUST filter variants to retain only `PASS` status and mitochondrial chromosome data, calculating per-sample heteroplasmy burden as the **count of heteroplasmic sites with VAF ≥ 1%** (See US-1).
- **FR-003**: System MUST assign mitochondrial haplogroups to each sample using `haplogrep2` and encode them as categorical variables for regression (See US-2).
- **FR-004**: System MUST compute the **Spearman rank correlation** between heteroplasmy burden and age, adjusting for sex, ancestry PCs, and sequencing depth, and compute Benjamini-Hochberg adjusted p-values. OLS regression is performed as a secondary check (See US-2).
- **FR-005**: System MUST execute a sensitivity analysis sweeping the heteroplasmy threshold over {0.5%, 1.0%, 2.0%} and report the resulting correlation coefficients (See US-3).
- **FR-006**: System MUST perform subgroup analysis within major continental ancestries to test for consistency of the association (See US-3).

### Key Entities

- **Sample**: Represents an individual in the dataset; attributes include `sample_id`, `age`, `sex`, `population`, `haplogroup`, `heteroplasmy_burden`, and `sequencing_depth`.
- **Variant**: Represents a specific mitochondrial mutation; attributes include `position`, `reference_allele`, `alternate_allele`, `vaf`, and `filter_status`.
- **AnalysisResult**: Represents the output of a statistical test; attributes include `model_type`, `predictor`, `coefficient`, `p_value`, `adjusted_p_value`, and `threshold_used`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The system MUST calculate and report the correlation coefficient and p-value between heteroplasmy burden and age (See US-2).
- **SC-002**: The system MUST calculate and report the p-value for the heteroplasmy term after Benjamini-Hochberg correction (See US-2).
- **SC-003**: The stability of the correlation across different VAF thresholds is measured by the variation in correlation coefficients across the {[deferred], [deferred], [deferred]} sweep (See US-3).
- **SC-004**: The consistency of the association across continental ancestry groups is measured by comparing the sign and magnitude of the coefficient in each subgroup (See US-3).
- **SC-005**: The total runtime of the analysis pipeline is measured against the constraint of ≤ 6 hours on a 2-CPU, 7 GB RAM runner (See Assumptions).

## Assumptions

- **Assumption about data availability**: The 1000 Genomes Project Phase 3 data (VCFs and panel file) is accessible via the public FTP site without authentication, and the `age` column is present in the metadata for a sufficient number of samples to achieve statistical power.
- **Assumption about computational resources**: The entire dataset (VCFs and derived matrices) fits within the memory and disk limits of the GitHub Actions free-tier runner, allowing processing without external cloud storage or memory-mapped files.
- **Assumption about methodological validity**: Since the 1000 Genomes data is observational (no random assignment), findings are framed as associational; the analysis does not claim causal inference between mtDNA variation and aging.
- **Assumption about threshold justification**: The 1% VAF threshold for heteroplasmy burden is based on community standards for distinguishing true low-frequency variants from sequencing noise; the sensitivity analysis (FR-005) validates that the conclusion is robust to this choice.
- **Assumption about haplogroup assignment**: `haplogrep2` can successfully assign haplogroups to ≥ 90% of samples; samples failing assignment are excluded from haplogroup-specific analyses but retained in burden-only models.
- **Assumption about power**: The sample size available in the 1000 Genomes Project (N = [deferred]) provides sufficient power to detect a small effect size (r ≈ 0.1) with α = 0.05, though this is acknowledged as a limitation if the effect is smaller. Note: The 'age' variable in 1000 Genomes may be binned or imprecise for some samples; the system will report the effective sample size used for the age-correlation analysis to account for this measurement error.