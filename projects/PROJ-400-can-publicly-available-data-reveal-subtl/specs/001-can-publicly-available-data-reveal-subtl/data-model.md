# Data Model: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Entity Definitions

### 1. Nucleus
Represents the atomic nucleus being studied.
- **Attributes**:
  - `name`: String (e.g., "6He", "19Ne")
  - `mass_number`: Integer (e.g., 6, 19)
  - `atomic_number`: Integer
  - `experimental_conditions`: String (summary of conditions, e.g., "trapped", "cold atoms")

### 2. DMeasurement
Represents a single published measurement of the D-coefficient.
- **Attributes**:
  - `nucleus`: Reference to `Nucleus`
  - `value`: Float (The D-coefficient value)
  - `uncertainty`: Float (Standard deviation)
  - `source_experiment`: String (Experiment name or reference ID)
  - `reference_id`: String (Citation ID, e.g., "DOI:10.xxxx")
  - `is_range`: Boolean (True if the value was derived from a range)
  - `original_range`: String (Original range string if applicable, e.g., "-0.001 to 0.001")

### 3. MetaAnalysisResult
Represents the aggregated statistical output.
- **Attributes**:
  - `nucleus`: Reference to `Nucleus`
  - `weighted_average`: Float
  - `combined_uncertainty`: Float
  - `n_measurements`: Integer
  - `p_value_heterogeneity`: Float (from Cochran's Q)
  - `d_upper_bound_95`: Float (95% CI upper bound)
  - `sensitivity_limit`: Float
  - `pdg_comparison`: String ("tighter", "looser", "consistent")
  - `random_seed`: Integer (The seed used for any stochastic fallbacks, e.g., shuffle tests for Cochran's Q, to ensure reproducibility)
  - `z_score`: Float (The Z-score for the null hypothesis test against D=0)
  - `hypothesis_result`: String ("non-zero" or "null")

## Data Flow

1. **Raw Input**: JSON/HTML scraped from PDG/NNDC (or mock data for testing).
2. **Harmonized**: `DMeasurement` objects stored in `data/processed/harmonized_d_measurements.csv`.
3. **Aggregated**: `MetaAnalysisResult` objects stored in `data/processed/meta_analysis_results.csv`.
4. **Final Report**: JSON/Markdown generated from `MetaAnalysisResult` for the paper.

## Constraints & Validation

- **Uncertainty**: Must be strictly positive ($> 0$).
- **Value**: Can be negative, zero, or positive.
- **Consistency**: If `n_measurements` < 2, `p_value_heterogeneity` is set to `null` and a warning is logged.
- **Range Handling**: If `is_range` is true, `uncertainty` must be calculated as `(max - min) / 2`.
- **Reproducibility**: `random_seed` must be recorded for any run involving stochastic elements (e.g., shuffle fallbacks).
- **Hypothesis Test**: `z_score` must be calculated for every result to determine `hypothesis_result`.