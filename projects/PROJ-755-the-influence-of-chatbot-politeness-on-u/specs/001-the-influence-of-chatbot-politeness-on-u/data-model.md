# Data Model: The Influence of Chatbot Politeness on User-Perceived Quality

## Overview

This document defines the data structures for the project, ensuring alignment with the "Data Hygiene" and "Single Source of Truth" principles of the project constitution. All data flows from `data/raw` (immutable) to `data/processed` (derived).

## Entity Definitions

### 1. Dialogue (Primary Unit of Analysis)
A single conversation between a user and a chatbot.
- **Dialogue ID**: Unique identifier (string).
- **User ID**: Unique identifier for the participant (string).
- **Mean Politeness Score**: Z-scored mean of politeness scores of all chatbot utterances in the dialogue (float).
- **Quality Rating**: User-reported rating (integer, 1-5).
- **Conversation Length**: Total word count or utterance count (integer).
- **Demographics**: Age (integer/float), Gender (categorical).
- **Status**: Included/Excluded (reason).

### 2. Utterance
A single message within a dialogue.
- **Utterance ID**: Unique identifier (string).
- **Dialogue ID**: Foreign key to Dialogue.
- **Speaker Role**: `user` or `chatbot` (categorical).
- **Text Content**: Raw text (string).
- **Politeness Score**: Raw score from BERT model (float).

### 3. User
A participant in the dataset.
- **User ID**: Unique identifier (string).
- **Age**: (integer/float).
- **Gender**: (categorical).
- **Number of Dialogues**: (integer).

## Data Flow

1.  **Raw**: Downloaded datasets (Parquet/CSV) stored in `data/raw/`.
2.  **Validation**: `validate_data.py` checks schema and logs errors.
3.  **Transformation**:
    - Filter incomplete dialogues (missing quality rating).
    - Compute utterance-level politeness scores.
    - Aggregate to dialogue-level mean.
    - Z-score the mean.
4.  **Merge**: Combine Persona-Chat and EmpatheticDialogues (if both valid) into a single `data/processed/dialogues_merged.csv`.
5.  **Analysis**: `run_clmm.py` reads `dialogues_merged.csv` and outputs `data/processed/model_results.csv`.

## Schema Definitions

The project uses the following YAML schemas for validation (see `contracts/`):
- `dataset.schema.yaml`: Validates the `dialogues_merged.csv` structure.
- `model_output.schema.yaml`: Validates the `model_results.csv` structure.

## Assumptions & Constraints

- **Missing Data**: Dialogues with missing quality ratings are excluded. Dialogues with missing demographics are retained for main analysis but excluded from subgroup analysis.
- **Data Volume**: Streaming is used for initial loading to avoid RAM overflow.
- **PII**: No Personally Identifiable Information (names, emails) is stored. User IDs are anonymized hashes.
