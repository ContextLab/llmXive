# Data Model: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Key Entities & Attributes

### 1. Sample
Represents an individual participant.
- `sample_id`: Unique identifier (string).
- `cohort`: Source dataset (AGP or UKBB).
- `fiber_intake_g_day`: Dietary fiber intake in grams/day (float).
- `sequencing_depth`: Number of sequencing reads (int).
- `age`: Age in years (float).
- `sex`: Sex (string: "M", "F", "Other").
- `bmi`: Body Mass Index (float).
- `antibiotic_use`: Antibiotic use in last 3 months (boolean).
- `batch`: Sequencing batch ID (string).
- `missing_covariate_pct`: Percentage of missing covariates (float).
- `excluded_reason`: Reason for exclusion (string, if applicable).

### 2. Taxon
Represents a bacterial taxon (e.g., genus, species).
- `taxon_id`: Unique identifier (string, e.g., "Genus_Bacteroides").
- `taxonomic_level`: Level (e.g., "Genus", "Species").
- `abundance_raw`: Raw count (int).
- `abundance_relative`: Relative abundance (float, 0-1).
- `clr_value`: CLR-transformed value (float).
- `pseudocount_applied`: Boolean (true if pseudocount was added).

### 3. Association Result
Result of MaAsLin2 analysis.
- `taxon_id`: Reference to Taxon.
- `sample_id`: Reference to Sample (for cohort context).
- `cohort`: AGP or UKBB.
- `effect_size`: Beta coefficient of the association (continuous fiber).
- `p_value`: Raw p-value.
- `q_value`: Adjusted q-value.
- `standard_error`: Standard error of the effect size.
- `significant`: Boolean (q < 0.05).

### 4. Differential Abundance Result
Result of ANCOM-II or DESeq2.
- `taxon_id`: Reference to Taxon.
- `cohort`: AGP or UKBB.
- `method`: "ANCOM-II" or "DESeq2".
- `effect_size`: Log-fold change or similar (float).
- `q_value`: Adjusted q-value.
- `direction`: "up" or "down".
- `significant`: Boolean (q < 0.05).

### 5. Cross-Cohort Validation
Replication status of significant findings.
- `taxon_id`: Reference to Taxon.
- `agp_significant`: Boolean.
- `ukbb_significant`: Boolean.
- `agp_direction`: "up" or "down" (if significant).
- `ukbb_direction`: "up" or "down" (if significant).
- `replication_status`: "Replicated", "Non-Replicable", or "Cohort-Specific".
- `agp_q_value`: q-value from AGP.
- `ukbb_q_value`: q-value from UKBB.

### 6. Power Analysis
- `cohort`: AGP or UKBB.
- `sample_size`: Number of samples after filtering.
- `effect_size_detected`: Minimum detectable effect size.
- `power`: Calculated power (float).
- `margin_of_error`: Margin of error (float).
- `power_flag`: "Sufficient" (power >= 0.8) or "Insufficient".

## Data Flow

1. **Raw Data**: Downloaded from AGP/UKBB (or open substitute) → `data/raw/`.
2. **Harmonized Data**: Filtered, unit-converted, covariates imputed → `data/processed/harmonized.tsv`.
3. **Transformed Data**: CLR-transformed abundances → `data/processed/clr_transformed.tsv`.
4. **Analysis Results**: Association and differential abundance results → `data/processed/association_results.tsv`, `data/processed/diff_abundance_results.tsv`.
5. **Validation Results**: Cross-cohort replication status → `data/processed/validation_results.tsv`.
6. **Summary**: Final summary tables (median fiber, power) → `data/processed/summary.tsv`.

## Constraints & Validations

- **Fiber Intake**: Must be between 0 and 200 g/day.
- **Sequencing Depth**: Must be >= 5,000 reads.
- **Missing Covariates**: Samples with >20% missing covariates excluded.
- **PII**: No PII allowed in `data/processed` or `data/interim`.
- **Checksums**: All raw files must have a recorded checksum.