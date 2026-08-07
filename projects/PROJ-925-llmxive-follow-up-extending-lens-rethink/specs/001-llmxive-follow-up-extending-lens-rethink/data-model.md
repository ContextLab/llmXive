# Data Model: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Entity Definitions

### 1. CaptionRecord (Raw Input)
Represents a single data point from the source dataset before transformation.
- `caption_id`: Unique string identifier.
- `caption_text`: Raw string of the text prompt.
- `clip_score`: Float (raw, unnormalized).
- `human_rating`: Float (raw, unnormalized) or null.
- `image_url`: String (metadata, not used for feature extraction).

### 2. LinguisticFeatureVector (Derived Input)
The structured set of predictors extracted from `caption_text`.
- `caption_id`: String (FK to CaptionRecord).
- `linguistic_uncertainty_proxy`: Float (ln(perplexity)).
- `syntactic_depth`: Integer (max dependency tree depth).
- `noun_phrase_density`: Float (ratio).
- `token_diversity`: Float (unique tokens / total tokens).
- `caption_length`: Integer (token count).
- `visual_token_density`: Float (ratio of noun phrases to total tokens; proxy for image complexity per FR-007).

### 3. DeviationTarget (Derived Output)
The target variable for the regression model.
- `caption_id`: String (FK).
- `normalized_clip_score`: Float (0.0 to 1.0).
- `normalized_human_rating`: Float (0.0 to 1.0).
- `deviation_score`: Float (absolute difference).
- `exclusion_reason`: String (if excluded, e.g., "missing_human_rating").

### 4. FeatureImportanceRanking (Model Output)
Sorted list of features by predictive power.
- `feature_name`: String.
- `importance_score`: Float (XGBoost gain/split).
- `p_value`: Float (from feature permutation test).
- `is_significant`: Boolean (after BH correction).

## Data Flow
1. **Ingestion**: `loader.py` fetches raw `CaptionRecord` data.
2. **Feature Engineering**: `features.py` consumes `caption_text` only (Principle VI) and outputs `LinguisticFeatureVector`.
3. **Target Calculation**: `preprocess.py` consumes `clip_score` and `human_rating` to generate `DeviationTarget`.
4. **Training**: `train.py` joins `LinguisticFeatureVector` and `DeviationTarget` (excluding nulls) to train the model.
5. **Evaluation**: `train.py` outputs `FeatureImportanceRanking` and stability metrics.

## Constraints & Validations
- **Null Handling**: `human_rating` must not be null for inclusion in training.
- **Normalization**: Both CLIP and Human ratings must be in [0, 1] before subtraction.
- **Type Safety**: All numeric fields must be floats/ints; no strings in numeric columns.
- **Immutability**: Raw data in `data/raw` is never modified. All derived files are new.
- **Image Complexity**: Replaced by `visual_token_density` (text-derived) to satisfy FR-007 without violating Principle VI.