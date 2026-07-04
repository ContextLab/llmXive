# Data Model: Gut Microbiome and Cognitive Decline Analysis

## 1. Entity Definitions

### 1.1 Sample (Participant)
Represents a single individual with both microbiome and cognitive data.
- `sample_id`: Unique identifier (string).
- `participant_id`: Original ID used for merging AGP and HRS (string).
- `age`: Integer (years).
- `sex`: Categorical (Male, Female, Other).
- `bmi`: Float (kg/m²).
- `is_missing_bmi`: Boolean (True if original BMI was missing and imputed).
- `cognitive_score`: Float (normalized score from HRS).
- `age_group`: Categorical (60-69, 70-79, 80+).

### 1.2 Taxon (Genus)
Represents a microbial genus and its abundance across samples.
- `genus_name`: String.
- `relative_abundance`: Float (0.0 to 1.0).
- `css_normalized_value`: Float (Cumulative Sum Scaling normalized value).

### 1.3 ModelArtifact
Represents the trained Random Forest model and its metadata.
- `model_id`: String (UUID).
- `hyperparameters`: Dictionary (`n_estimators`, `max_depth`, `random_state`).
- `metrics`: Dictionary (`r2`, `rmse`, `fdr_significant_count`).
- `shap_rankings`: List of tuples (genus, mean_abs_shap_value).
- `timestamp`: ISO8601 datetime.

## 2. Data Flow

1. **Raw Input**: AGP (Qiita) Taxa counts + HRS (Official) Metadata.
2. **Intermediate**: Merged DataFrame (Sample + Taxa).
3. **Processed**: CSS-normalized + Imputed DataFrame.
4. **Output**:
   - Correlation Table (Genus, Rho, P-value, Q-value, Method).
   - Model Performance Metrics.
   - Sensitivity Analysis Report.

## 3. Storage Schema

- **Raw Data**: `data/raw/agp_*.csv`, `data/raw/hrs_*.csv` (or official formats).
- **Processed Data**: `data/processed/merged_age60.csv`, `data/processed/css_normalized.csv`.
- **Results**: `data/results/correlations.json`, `data/results/model_metrics.json`.

## 4. Constraints

- **Missing Data**: Rows with missing `cognitive_score` or `age` are dropped. Missing `bmi` is imputed via MICE; `is_missing_bmi` flag is set.
- **Zero Inflation**: Microbiome data contains many zeros. CSS normalization handles zeros without log transformation.
- **Memory**: All data must fit in RAM. If the merged dataset exceeds a substantial size threshold, the pipeline will log a warning and subsample taxa to the top 200 genera.
- **Linkage**: If no `participant_id` match is found, the pipeline terminates with a fatal error.