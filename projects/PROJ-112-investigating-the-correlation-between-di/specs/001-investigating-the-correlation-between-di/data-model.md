# Data Model: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Key Entities

### Sample
Represents an individual participant.
- **Attributes**:
  - `sample_id` (string): Unique identifier generated as `SHA256(cohort + original_sample_id)`. Enforced for Single Source of Truth traceability.
  - `cohort` (string): "AGP" or "UKBB".
  - `fiber_intake_g_day` (float): Self-reported fiber intake (0–200 g/day).
  - `read_depth` (int): Total sequencing reads.
  - `age` (int/float): Age in years.
  - `bmi` (float): Body Mass Index.
  - `antibiotic_use` (boolean): Recent antibiotic use (Yes/No).
  - `sex` (string): "Male", "Female", "Other".
  - `batch` (string): Sequencing batch ID.

### Taxon
Represents a bacterial taxon (Genus/Species level).
- **Attributes**:
  - `taxon_id` (string): Taxonomic identifier (e.g., "g__Bacteroides").
  - `raw_count` (int): Raw read count for the sample.
  - `clr_value` (float): Centered Log-Ratio transformed value.
  - `prevalence` (float): Fraction of samples where count > 0.

### Covariate
Represents confounding variables used in models.
- **Attributes**:
  - `covariate_name` (string): e.g., "Age", "BMI".
  - `value` (float/string): Normalized value.
  - `missing_ratio` (float): Proportion of missing values in the cohort.

## Data Flow

1.  **Raw Ingestion**:
    - `data/raw/agp_raw.tsv` (AGP OTU table + metadata from Qiita 10160).
    - `data/raw/ukbb_raw.tsv` (UKBB OTU table + metadata from Field 21003/22012).
2.  **Filtering & Harmonization**:
    - Filter: `read_depth >= 5000`, `0 <= fiber_intake <= 200`.
    - Exclude: Missing fiber intake.
    - Convert: All fiber units to `g/day`.
    - **ID Generation**: `sample_id` = `SHA256(cohort + original_id)`.
    - Output: `data/processed/merged_harmonized.tsv`.
3.  **Transformation**:
    - **Imputation**: Apply MICE (Multivariate Imputation by Chained Equations) for missing covariates if <20% missing. Exclude if >20%.
    - Apply CLR (pseudocount=1) to taxon counts.
    - Output: `data/processed/clr_transformed.tsv`.
4.  **Analysis Output**:
    - Correlation Results: `data/processed/results/correlation_maaslin2.tsv`.
    - Cross-Cohort Validation: `data/processed/results/validation_summary.tsv`.

## Schema Constraints

- **Fiber Intake**: Must be `float` in range `[0.0, 200.0]`.
- **Read Depth**: Must be `int` >= 5000.
- **Taxon Abundance**: Non-negative `int` (raw) or `float` (CLR).
- **Missing Data**: Samples with >20% missing covariates are excluded. MICE used for <20%.
- **Zero Handling**: Pseudocount of 1 applied before log transformation.
- **Unique ID**: `sample_id` must be a valid SHA256 hash string.
