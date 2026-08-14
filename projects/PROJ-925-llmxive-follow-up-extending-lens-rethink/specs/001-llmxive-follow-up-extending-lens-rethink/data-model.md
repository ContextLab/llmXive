# Data Model: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Overview

This document defines the data structures used in the pipeline, ensuring strict separation between input features (text-only) and target variables (derived from CLIP/Human ratings).

## Entities

### 1. CaptionRecord (Input)
Represents a raw data point from the dataset.
- `caption_id` (str): Unique identifier.
- `caption` (str): Raw text.
- `clip_score` (float): Pre-computed CLIP similarity score (generated in Phase 0 if missing).
- `human_rating` (float): Human preference rating (derived from binary preference in Phase 0 if missing).

### 2. LinguisticFeatureVector (Derived - Input to Model)
Computed from `caption` only.
- `uncertainty_proxy` (float): `ln(perplexity)`.
- `syntactic_depth` (int): Max dependency tree depth.
- `noun_phrase_density` (float): Distinct NPs / total tokens.
- `token_count` (int): Number of tokens.
- `distinct_np_count` (int): Count of distinct noun phrases.
- `token_diversity` (float): Type-token ratio.

### 3. DeviationTarget (Derived - Output)
- `deviation_score` (float): $| \text{Z\_clip} - \text{Z\_human} |$.
- `is_learnable` (bool): Flag indicating if variance > 0.
- **Note**: If `human_rating` is binary, `deviation_score` will be discrete. This is acknowledged in the methodology. The distribution is bounded and non-Gaussian; statistical tests must be non-parametric.

### 4. ModelOutput
- `predicted_deviation` (float).
- `feature_importance` (dict).

## Data Flow

1. **Raw Load**: `CaptionRecord` from `pick-a-pic` (streamed).
2. **Phase 0**: Generate missing `clip_score` and `human_rating`.
3. **Filter**: Remove records where `human_rating` is NaN.
4. **Feature Extraction**: `CaptionRecord` -> `LinguisticFeatureVector` (Text-only).
5. **Target Calculation**: `clip_score`, `human_rating` -> `DeviationTarget` (Z-score fit on train, transform on test).
6. **Merge**: `LinguisticFeatureVector` + `DeviationTarget` -> `TrainingSample`.
7. **Train**: `TrainingSample` -> `ModelOutput`.

## Constraints

- **No Image Data**: `LinguisticFeatureVector` must never contain image pixels or CLIP image embeddings.
- **No Circular Validation**: `DeviationTarget` is calculated independently of `LinguisticFeatureVector`.
- **Zero Variance**: If `DeviationTarget` has zero variance, the pipeline halts before training.
- **Multicollinearity**: If VIF > 5, Ridge Regression is used to stabilize coefficients while retaining features.
- **Target Distribution**: The target variable is non-negative and bounded. Statistical analysis must use non-parametric methods (Spearman's rho, bootstrapping) to account for this.
