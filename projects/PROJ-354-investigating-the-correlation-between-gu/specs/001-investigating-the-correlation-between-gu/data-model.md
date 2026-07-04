# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data

## Entities

### Participant
Represents a UK Biobank cohort member with linked data.
*   `participant_id`: Unique identifier (string/int).
*   `age`: Age at baseline (float/int).
*   `sex`: Biological sex (categorical: 'Male', 'Female').
*   `bmi`: Body Mass Index (float).
*   `diet_quality_score`: Composite diet score (float).
*   `physical_activity_level`: Level of physical activity (categorical/float).
*   `medication_use`: Flag for medication use (boolean).
*   `antibiotic_use`: Flag for recent antibiotic use (boolean).
*   `has_microbiome`: Boolean indicating presence of microbiome data.
*   `has_cognitive`: Boolean indicating presence of cognitive data.

### MicrobiomeProfile
Represents the ILR-transformed microbiome composition for a participant.
*   `participant_id`: Foreign key to Participant.
*   `ilr_coordinates`: Dictionary or array of ILR-transformed genus-level coordinates (floats).
*   `sample_date`: Date of sample collection (date).
*   `sequencing_quality`: Quality metric score (float).

### CognitiveScore
Represents standardized cognitive performance metrics.
*   `participant_id`: Foreign key to Participant.
*   `reaction_time_ms`: Reaction time in milliseconds (float).
*   `numeric_memory_score`: Score out of 100 (float/int).
*   `reasoning_score`: Score out of 100 (float/int).
*   `test_date`: Date of cognitive testing (date).

### AssociationResult
Represents the output of the statistical analysis.
*   `taxon_name`: Name of the genus-level taxon (string).
*   `cognitive_metric`: Name of the cognitive metric (e.g., "reaction_time").
*   `effect_size_beta`: Coefficient from the linear model (float).
*   `unadjusted_p_value`: Raw p-value (float).
*   `adjusted_p_value`: Benjamini-Hochberg adjusted p-value (float).
*   `interaction_p_value`: P-value for the Age_Group * Taxon interaction (float, nullable).
*   `causality_claim`: Always `false` (boolean).

## Data Flow

1.  **Raw Data**: Downloaded from UK Biobank (or provided locally) -> `data/raw/`.
2.  **Preprocessing**:
    *   Filter by antibiotic use and data completeness.
    *   Aggregate to genus-level.
    *   Apply ILR transformation.
    *   Output: `data/processed/ilr_microbiome.parquet`, `data/processed/cognitive_scores.parquet`.
3.  **Analysis**:
    *   Join preprocessed data.
    *   Fit linear models.
    *   Apply BH correction.
    *   Output: `results/associations/association_results.parquet`.
4.  **Visualization**:
    *   Generate Manhattan plots.
    *   Output: `results/plots/manhattan_plot.png`.

## Constraints & Validations

*   **ILR Coordinates**: Must sum to 0 (mathematical property of ILR).
*   **P-values**: Must be in range [0, 1].
*   **Causality**: `causality_claim` must be `false` in all output files.
*   **Missing Data**: Participants with >2 missing confounder values are excluded.
