# Data Model: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Overview

This document defines the data structures used in the pipeline. All data flows through a strict transformation chain: `Raw Data` -> `Processed Features` -> `Training Matrix` -> `Model Artifacts`. The `contracts/` directory is the **Single Source of Truth (SSoT)** for schema validation (Constitution Principle IV).

## Entity Definitions

### CaptionRecord (Raw/Intermediate)
Represents a single caption instance before feature extraction.
- `caption_id`: Unique string identifier.
- `image_id`: Identifier for the associated image.
- `caption_text`: The raw string content of the caption.
- `clip_score`: Float (0.0 - 1.0), computed similarity score.
- `human_rating`: Float (0.0 - 1.0), derived from Pick-a-Pic preference pairs.
- `source_dataset`: String, e.g., "pick-a-pic".

### LinguisticFeatureVector (Derived)
The output of the feature extraction module.
- `caption_id`: FK to CaptionRecord.
- `semantic_surprisal`: Float, $\ln(\text{perplexity})$. *Note: Operational proxy for semantic entropy.*
- `syntactic_depth`: Integer, max dependency tree depth.
- `noun_phrase_density`: Float, ratio of NP tokens.
- `token_diversity`: Float, unique tokens / total tokens.
- `caption_length`: Integer, total token count (covariate).
- `image_complexity`: Float, optional proxy for image complexity (covariate).
- `is_valid`: Boolean, true if extraction succeeded.

### DeviationScore (Target)
The target variable derived from the alignment gap.
- `caption_id`: FK.
- `deviation_score`: Float, $| \text{CLIP} - \text{Human} |$.
- `normalized_clip`: Float.
- `normalized_human`: Float.

### FeatureImportanceRanking (Model Output)
The final result of the analysis.
- `feature_name`: String.
- `importance_score`: Float (permutation importance).
- `p_value`: Float (raw).
- `adjusted_p_value`: Float (Benjamini-Hochberg).
- `is_significant`: Boolean.

## Data Flow Diagram

1. **Download**: `pick-a-pic.parquet` -> `data/raw/pick-a-pic_stream.parquet` (streamed)
2. **Preprocess**: Add `clip_score` (computed), `human_rating` (from preference pairs) -> `data/processed/caption_records.csv`
3. **Feature Extract**: `caption_text` -> `LinguisticFeatureVector` -> `data/processed/features.csv`
4. **Merge**: Join `features` + `deviation` -> `data/processed/training_matrix.csv`
5. **Train**: `training_matrix.csv` -> `code/models/xgboost_model.json` + `results/significance.json`

## Constraints

- **Immutability**: Raw files in `data/raw` are never modified.
- **Null Handling**: Any record with `NaN` in `semantic_surprisal` or `deviation_score` is dropped before training.
- **Schema Validation**: All CSV/Parquet files must match the schemas defined in `contracts/`.
- **Versioning**: Checksums of all processed files are recorded in `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml`.