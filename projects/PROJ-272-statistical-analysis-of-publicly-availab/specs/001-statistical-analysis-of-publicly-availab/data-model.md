# Data Model: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Overview

This document defines the data structures for the statistical analysis pipeline. It covers the raw input, cleaned intermediate, and final feature matrix formats. All data is stored in `data/` with checksums for reproducibility.

## Entity Definitions

### Participant
- **ID**: Unique identifier (string).
- **Cognitive Status**: Enum (`Control`, `MCI`, `AD`).
- **Transcript**: Cleaned text (string).
- **Word Count**: Integer.

### Linguistic Feature
- **Type**: Lexical, Syntactic, or Semantic.
- **Value**: Float (normalized) or `NaN` (if zero-division or invalid).
- **Source**: Script name (e.g., `features.py`).

## Data Flow

1. **Raw Input** (`data/raw/`):
   - `adress_raw.txt` (from ADReSS GitHub).
2. **Cleaned Intermediate** (`data/interim/`):
   - `cleaned_transcripts.csv`: ID, Status, Cleaned Text, Word Count.
3. **Feature Matrix** (`data/processed/`):
   - `features.csv`: ID, Status, TTR, MTLD, NounVerbRatio, MeanClauseLength, TUnitCount, SemanticSimilarity.

## Schema Definitions

### Input Schema (Raw)
- **Format**: TXT or JSON.
- **Fields**: `id`, `text`, `status` (optional).

### Intermediate Schema (Cleaned)
- **Format**: CSV.
- **Fields**:
  - `participant_id`: String (unique).
  - `cognitive_status`: String (`Control`, `MCI`, `AD`).
  - `cleaned_text`: String (UTF-8, no non-verbal annotations).
  - `word_count`: Integer (≥ 50).

### Output Schema (Features)
- **Format**: CSV.
- **Fields**:
  - `participant_id`: String.
  - `cognitive_status`: String.
  - `ttr`: Float (Type-Token Ratio).
  - `mtld`: Float (Measure of Textual Lexical Diversity).
  - `noun_verb_ratio`: Float (or `NaN`).
  - `mean_clause_length`: Float.
  - `t_unit_count`: Integer.
  - `semantic_similarity`: Float (0.0 - 1.0).

## Data Hygiene Rules

- **Checksums**: SHA-256 hash recorded for every file in `data/`.
- **PII**: No names, dates of birth, or locations in `data/`.
- **Immutability**: Raw data never modified. Derivations create new files.
- **Zero-Handling**: `noun_verb_ratio` may be `NaN` if zero nouns or verbs detected.