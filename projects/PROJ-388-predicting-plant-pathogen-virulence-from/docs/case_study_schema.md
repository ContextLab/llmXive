# Descriptive Case Study Report Schema

## Purpose
This document defines the schema, content requirements, and validation criteria for the 'Descriptive Case Study Report' generated when the sample size (N) is insufficient for statistical inference (N < 10).

This report serves as a sanctioned fallback mechanism (per Plan: Power & Limitation Disclosure) to ensure scientific rigor when the dataset is too small to support PGLS or robust FDR correction. It explicitly avoids reporting p-values or confidence intervals to prevent Type I errors.

## Trigger Condition
The report generation logic in `src/analysis/correlation.py` must check:
```python
if sample_size < 10:
 generate_case_study_report()
```

## Output Location
- **File Path**: `output/case_study_report.md`
- **Format**: Markdown (`.md`)

## Required Sections

### 1. Executive Summary
- **Content**: A brief, non-technical summary stating that the analysis was performed on a small cohort (N < 10) and that results are descriptive only.
- **Constraint**: Must explicitly state "No statistical significance testing was performed due to low sample size."

### 2. Sample Size and Limitations
- **Content**:
 - Exact count of isolates/species aggregates used (N).
 - Breakdown by species (if aggregated).
 - **Explicit Limitation Statement**: "With N < 10, the study lacks statistical power to detect small-to-moderate effect sizes. Results should be treated as hypotheses for future validation, not confirmed associations."
 - Mention of potential bias in small samples (e.g., outlier sensitivity).

### 3. Aggregate Statistics
- **Content**: Descriptive statistics for the dataset.
 - **Phenotypic Scores**: Mean, Median, Standard Deviation, Range (Min, Max).
 - **Genomic Features**: For each feature analyzed, report:
 - Presence/Absence frequency (count and percentage).
 - Mean virulence score for "Present" vs "Absent" groups (if applicable), without p-values.
- **Format**: Use Markdown tables.

### 4. Feature Observations (Qualitative)
- **Content**:
 - List the top 3-5 genomic features with the largest absolute difference in mean phenotype between presence/absence groups (or highest raw correlation magnitude).
 - **Constraint**: Do **not** list p-values, adjusted p-values, or confidence intervals.
 - **Constraint**: Do **not** use terms like "significant," "significant association," or "statistically significant." Use terms like "notable difference," "strong raw correlation," or "observed trend."
 - Include a qualitative description of the biological context if known (e.g., "Feature X is a known effector in related species").

### 5. Data Provenance
- **Content**:
 - List of source URLs for the genomes and phenotypic data used.
 - Accession numbers for the specific isolates included in this small cohort.
 - Timestamp of data extraction.

### 6. Recommendations for Future Work
- **Content**:
 - Specific recommendations to increase sample size (e.g., "Target N >= 30 for PGLS applicability").
 - Suggested additional isolates or species to include to improve power.
 - Validation steps required before any clinical or agricultural deployment.

## Validation Criteria

The generated report must pass the following checks before being accepted:

1. **File Existence**: `output/case_study_report.md` must exist and be non-empty.
2. **Section Presence**: All six required sections (1-6) must be present as top-level headers (`#` or `##`).
3. **Forbidden Content Check**: The file must **NOT** contain the following strings:
 - "p-value"
 - "p <"
 - "significant" (case-insensitive, unless in the context of "not significant" or "statistically significant" used to describe the *lack* of testing)
 - "FDR"
 - "adjusted p"
4. **Sample Size Accuracy**: The N reported in Section 2 must match the actual number of rows in the input dataset used for this run.
5. **No Synthetic Data**: The report must not reference any synthetic or mock data; it must reflect the real, small dataset loaded.

## Implementation Notes

- The `src/analysis/correlation.py` module must include a function `generate_case_study_report(df, output_path, sample_size)` that constructs this markdown content.
- The function should use the `pandas` library to calculate the descriptive statistics (mean, std, etc.).
- The function should use the `datetime` module for the timestamp.
- The function must raise an error if the input dataframe is empty or if `sample_size >= 10` (logic error).