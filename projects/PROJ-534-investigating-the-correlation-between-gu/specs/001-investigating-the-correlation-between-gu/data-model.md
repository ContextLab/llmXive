# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility in Aging

## Entities and Attributes

### Participant

Represents an individual in the study cohort.

-   `participant_id`: String (Unique ID)
-   `age`: Integer (>= 65 for filtered cohort)
-   `sex`: String ("Male", "Female", "Other")
-   `bmi`: Float (Body Mass Index)
-   `dietary_fiber_intake`: Float (grams/day)
-   `antibiotic_use_history`: Boolean (True/False)
-   `cognitive_flexibility_score`: Float (Standardized score)
-   `microbiome_sample_id`: String (FK to MicrobiomeProfile)

### MicrobiomeProfile

Represents the microbial composition metrics for a sample.

-   `sample_id`: String (Unique ID, matches `microbiome_sample_id`)
-   `shannon_diversity`: Float
-   `simpson_diversity`: Float
-   `chao1`: Float
-   `bray_curtis_distance`: Float (Distance to reference or centroid)
-   `unifrac_distance`: Float (Distance to reference or centroid)
-   `raw_sequence_path`: String (Optional, path to raw FASTQ/BIOM if available)

### AnalysisResult

Represents the output of a statistical test.

-   `test_id`: String (UUID)
-   `test_type`: String ("Pearson", "Spearman", "LinearRegression", "PERMANOVA")
-   `metric_name`: String (e.g., "Shannon", "Simpson")
-   `correlation_coefficient`: Float (or `beta` for regression)
-   `p_value`: Float
-   `adjusted_p_value`: Float (BH corrected)
-   `confidence_interval_lower`: Float
-   `confidence_interval_upper`: Float
-   `sample_size`: Integer
-   `effect_size`: Float (e.g., $R^2$)

## Data Flow

1.  **Raw Input**: `raw/` (Synthetic or Downloaded)
2.  **Ingestion**: `data/processed/merged_raw.csv` (Joined on `participant_id`)
3.  **Filtering**: `data/processed/cohort_filtered.csv` (Age >= 65, non-null)
4.  **Diversity Calculation**: `data/processed/diversity_metrics.csv` (Added columns)
5.  **Analysis Output**: `data/results/statistical_results.json` (Aggregated results)
6.  **Visualization**: `data/results/plots/` (PNG/SVG files)

## Constraints

-   **Age**: Must be >= 65 in the final analysis cohort.
-   **Completeness**: No null values allowed in `cognitive_flexibility_score`, `shannon_diversity`, or covariates used in regression.
-   **Uniqueness**: `participant_id` and `sample_id` must be unique.
