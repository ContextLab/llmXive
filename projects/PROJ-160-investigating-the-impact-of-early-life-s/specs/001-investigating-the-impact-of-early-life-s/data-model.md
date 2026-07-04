# Data Model: Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes

## Entity Definitions

### 1. Participant
Represents an individual in the ABCD Study cohort.
*   `participant_id`: Unique identifier (String).
*   `family_id`: Group identifier for siblings/twins (String).
*   `age`: Age at baseline (Float, years).
*   `sex`: Biological sex (String: "Male", "Female").
*   `scanner_site`: MRI scanner location (String).
*   `ace_score`: Adverse Childhood Experiences score (Float, after INT transformation).
*   `mri_quality_flag`: Boolean or categorical flag for MRI quality (Boolean/Enum).

### 2. HippocampalSubfield
Represents volume measurements for a specific subfield.
*   `participant_id`: Foreign key to Participant.
*   `subfield_name`: Name of the subfield (Enum: "CA3", "DG", "Subiculum").
*   `raw_volume`: Unadjusted volume in mm³ (Float).
*   `icv`: Intracranial volume in mm³ (Float).
*   `normalized_volume`: `raw_volume / icv` (Float, 4+ decimal precision).

### 3. StatisticalModel
Represents the output of a fitted LMM.
*   `model_id`: Unique identifier (String).
*   `subfield_name`: Target subfield.
*   `formula`: String representation of the model formula.
*   `beta_ace`: Standardized coefficient for ACE score (Float).
*   `ci_lower`: Lower bound of 95% CI (Float).
*   `ci_upper`: Upper bound of 95% CI (Float).
*   `p_value`: Uncorrected p-value (Float).
*   `p_value_corrected`: Bonferroni-adjusted p-value (Float).
*   `permutation_p_value`: Empirical p-value from 5,000 cluster permutations (Float).

### 4. AnalysisResult
Aggregated output for reporting. This entity is instantiated and persisted by `code/analysis/results.py` to `data/processed/results.yaml`.
*   `analysis_type`: String. Enum: "primary", "exploratory_ratio", "sensitivity", "robustness".
*   `effect_size`: The primary coefficient of interest (Float).
*   `significance`: Boolean (based on corrected p-value for primary; descriptive for ratio).
*   `sensitivity_summary`: JSON object mapping alpha thresholds to significant counts.
*   `ratio_stats`: JSON object containing descriptive stats for the CA3:DG ratio (mean, sd, correlation with ACE).
*   `interpretation`: String. Explicitly states "Associational" for all results.

## Data Flow

1.  **Raw Ingestion**: Download `phenotypic.csv` and `subcorticalSegmentationStats.csv`.
2.  **Filtering**: Remove rows where `ace_score` is null or `mri_quality_flag` indicates failure.
3.  **Transformation**:
    *   Calculate `normalized_volume` = `raw_volume` / `icv`.
    *   Apply **Inverse Normal Transformation (INT)** to `ace_score`.
4.  **Modeling**: Iterate through subfields (CA3, DG, Subiculum) and fit LMM.
5.  **Correction**: Apply Bonferroni ($p_{adj} = p \times 3$) for primary subfields only.
6.  **Robustness**: Run **cluster-level** permutation test; generate sensitivity sweep table.
7.  **Output**: Save results to `data/processed/results.yaml` (AnalysisResult entity) and `data/processed/models.json`.