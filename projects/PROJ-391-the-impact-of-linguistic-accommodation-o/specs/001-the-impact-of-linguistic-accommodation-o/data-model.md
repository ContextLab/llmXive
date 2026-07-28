# Data Model: Linguistic Accommodation and Speaker Emotional Intensity

## Overview

This document defines the data structures, schemas, and transformation logic for the project. It ensures that the data pipeline produces consistent, valid, and verifiable artifacts. The data model reflects the pivot to **human-human dialogue** and the aggregation of emotion labels to the dialogue level.

## Entity Definitions

### 1. DialoguePair
Represents a single interaction unit (turn pair) in the dialogue.
- **Fields**:
  - `conversation_id`: String (unique identifier for the dialogue session).
  - `turn_index`: Integer (index of the first turn in the pair).
  - `speaker_role`: String (e.g., "Speaker_A", "Speaker_B").
  - `text`: String (normalized text of the turn).
  - `partner_text`: String (normalized text of the adjacent turn).
  - `dialogue_emotion_label`: String (original label from dataset, e.g., "Joy", "Neutral").

### 2. AccommodationMetric
Computed metrics for a specific `DialoguePair`.
- **Fields**:
  - `conversation_id`: String (FK to DialoguePair).
  - `turn_index`: Integer (FK to DialoguePair).
  - `lexical_overlap`: Float (Jaccard similarity of tokens, 0.0 to 1.0, 4 decimal precision).
  - `syntactic_similarity`: Float (Jaccard similarity of POS tags, 0.0 to 1.0, 4 decimal precision).
  - `bigram_overlap`: Float (Jaccard similarity of bigrams, 0.0 to 1.0).
  - `sentence_length_variance`: Float (Standard deviation of sentence lengths).
  - `dependency_similarity`: Float (Optional, for sensitivity analysis, 0.0 to 1.0).

### 3. EmotionalIntensity
Mapped numeric score for a specific `DialoguePair` (derived from dialogue-level label).
- **Fields**:
  - `conversation_id`: String (FK).
  - `turn_index`: Integer (FK).
  - `original_emotion`: String.
  - `emotional_intensity`: Integer (1-5 scale, mapped from dialogue label).
  - `is_valid`: Boolean (True if emotion label existed and was mapped).

### 4. ValidationGroundTruth
Human-rated intensity for a subset of dialogues (Phase 1).
- **Fields**:
  - `conversation_id`: String (FK).
  - `rater_id`: String.
  - `human_intensity`: Integer (1-5).
  - `timestamp`: String.

### 5. AnalysisResult
Aggregated statistical results.
- **Fields**:
  - `metric_type`: String (e.g., "lexical_spearman", "syntactic_spearman").
  - `correlation_coefficient`: Float.
  - `p_value`: Float.
  - `ci_lower`: Float.
  - `ci_upper`: Float.
  - `n_samples`: Integer.
  - `bootstrap_iterations`: Integer.
  - `pseudo_r2`: Float (McFadden's Pseudo-R2 for regression).

## Data Flow

1. **Raw Input**: DailyDialog (JSON/Parquet).
2. **Normalization**: NFKC applied. Empty turns filtered.
3. **Metric Computation**: Jaccard, POS tags, Bigrams, Variance calculated for adjacent turn pairs.
4. **Aggregation**: Dialogue-level emotion label assigned to all turn pairs in the dialogue.
5. **Mapping**: Emotion labels converted to 1-5 intensity.
6. **Validation**: Human ratings collected for subset.
7. **Aggregation**: Merged into a single analysis-ready dataframe.
8. **Statistical Output**: Correlation coefficients, CIs, regression coefficients (Odds Ratios, Pseudo-R2).

## Data Hygiene Rules

- **Immutability**: Raw data files in `data/raw/` are never modified.
- **Checksums**: MD5 checksums recorded for all raw files.
- **Null Handling**: Missing emotion labels result in `emotional_intensity = null` (excluded from correlation).
- **Precision**: All float metrics stored with 4 decimal places.
- **Unit of Analysis**: Emotion is dialogue-level; Accommodation is turn-pair level.