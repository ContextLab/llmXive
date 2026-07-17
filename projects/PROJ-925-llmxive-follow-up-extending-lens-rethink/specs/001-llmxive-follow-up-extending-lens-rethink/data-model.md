# Data Model: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Entities

### 1. CaptionRecord (Raw Input)
Represents a single row from the source dataset.
- `id`: string (unique identifier)
- `text`: string (raw caption)
- `image_id`: string (optional, for reference)
- `clip_score`: float (pre-computed or computed on the fly)
- `preference_score`: float (0.0 to 1.0) or null (mapped from `preference_score`)

### 2. LinguisticFeatureVector (Derived)
The output of the feature extraction step.
- `id`: string (foreign key to CaptionRecord)
- `textual_perplexity`: float (ln(perplexity)) - *Proxy for linguistic uncertainty*
- `syntactic_depth`: int (max dependency tree depth)
- `noun_phrase_density`: float (ratio)
- `token_diversity`: float (type-token ratio)
- `caption_length`: int (number of tokens, used as confounder)
- `status`: string ("valid" or "failed")

### 3. DeviationTarget (Derived)
The target variable for the model.
- `id`: string (foreign key)
- `deviation_score`: float (absolute difference of raw scores)
- `clip_score`: float (raw CLIP score)
- `human_rating`: float (raw Human rating)

### 4. StabilityMetrics (Aggregated)
Results of the sensitivity analysis.
- `feature_name`: string
- `mean_rank`: float
- `std_rank`: float
- `p_value`: float
- `is_significant`: boolean (after BH correction)

## Data Flow

1. **Ingestion**: `loader.py` reads from `data/raw` (streaming).
2. **Feature Extraction**: `features.py` transforms `text` -> `LinguisticFeatureVector`. Includes `try/except` for failed extractions; logs and excludes failures.
3. **Target Engineering**: `preprocess.py` transforms `clip_score` + `human_rating` -> `DeviationTarget` (using raw difference). Checks for zero variance; raises `ValueError` if unlearnable.
4. **Join**: Records are joined on `id`. Rows with missing `human_rating` or failed features are dropped.
5. **Modeling**: `train.py` ingests the joined dataframe.
   - **Stability Loop**: Iterates over 5 seeds. Inside loop: re-sample data, retrain model, calculate importance.
   - **Permutation**: 1,000 iterations.
   - **Correction**: Benjamini-Hochberg.
6. **Output**: `results/stability_metrics.json` and `results/model.pkl`.

## Constraints

- **No Circular Data**: `features.py` must not receive `clip_score` or `human_rating`.
- **No In-Place Modification**: Raw data is read-only. All derived data is written to new files.
- **Null Handling**: Missing `human_rating` results in row exclusion, not imputation.
- **Normalization**: No normalization is applied to the target variable. Raw difference is used.
- **Confounding**: `caption_length` must be included as a predictor to control for length bias.