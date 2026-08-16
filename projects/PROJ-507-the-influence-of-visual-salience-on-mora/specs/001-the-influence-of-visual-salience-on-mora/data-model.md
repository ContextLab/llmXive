# Data Model: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Overview

This document defines the data structures for the project, ensuring alignment with the spec and constitution. Data flows from raw ingestion → manipulation → survey → analysis.

## Entity-Relationship Diagram (Simplified)

```
[Scenario] --1:N--> [Stimulus Variant] --N:M--> [Response]
                     |
                     v
              [Participant]
```

## Data Models

### Scenario

- **scenario_id**: Unique identifier (string, e.g., "MD_001")
- **original_image_path**: Path to raw image (string)
- **metadata_tags**: List of tags (e.g., ["dilemma", "conflict"])
- **ambiguity_mean**: Mean ambiguity score (float, ≥3.5 for retention)
- **ambiguity_kappa**: Cohen's κ (float, ≥0.6 for retention)
- **external_ground_truth_match**: Boolean (True if matched with external source)
- **human_coding_status**: "retained" | "excluded"

### Stimulus Variant

- **variant_id**: Unique identifier (string, e.g., "MD_001_low")
- **scenario_id**: Foreign key to Scenario (string)
- **salience_level**: "low" | "medium" | "high"
- **manipulation_params**: JSON with contrast/brightness values (versioned)
- **clip_similarity**: Cosine similarity to original (float, ≥0.95)
- **rms_contrast_change**: Percentage change in ROI (float, ≥15%)
- **moral_intent_preservation_score**: Float (correlation ≥0.90)
- **semantic_integrity**: "passed" | "failed"
- **image_path**: Path to manipulated image (string)

### Response

- **response_id**: Unique identifier (string)
- **participant_id**: Participant identifier (string)
- **variant_id**: Foreign key to Stimulus Variant (string)
- **blame_rating**: Integer (1-7)
- **timestamp**: ISO 8601 datetime
- **valid**: True | False (after cleaning)

### Participant

- **participant_id**: Unique identifier (string)
- **total_responses**: Integer
- **mean_blame**: Float
- **variance_blame**: Float
- **straight_liner**: True | False (variance <0.1 or >90% identical)
- **inclusion_status**: "included" | "excluded"

### Pre-Registration Config

- **precision_threshold**: Float (e.g., 0.3)
- **threshold_source**: String (e.g., "config/pre_registration.yaml")

## Data Flow

1. **Ingestion**: Raw images from MoralD → `data/raw/`
2. **Filtering**: Metadata tags → candidate scenarios
3. **External Ground Truth Validation**: Cross-reference with external source → `data/processed/ground_truth_match.csv`
4. **Human Coding**: Ambiguity scores → `data/processed/ambiguity_scores.csv` (via `02_human_coding.py`)
5. **Manipulation**: Generate variants → `data/processed/stimuli/`
6. **Survey**: Collect responses → `data/processed/responses.csv`
7. **Cleaning**: Exclude straight-liners → `data/processed/cleaned_responses.csv`
8. **Analysis**: CLMM on cleaned data → `data/processed/results.json`

## Constraints

- **Checksums**: All files in `data/` checksummed; hashes in `checksums.txt`.
- **PII**: No personally identifiable information; participant IDs anonymized.
- **Versioning**: Each transformation produces new file; no in-place edits.
- **Pre-Registration**: Precision threshold defined in `config/pre_registration.yaml` and versioned.