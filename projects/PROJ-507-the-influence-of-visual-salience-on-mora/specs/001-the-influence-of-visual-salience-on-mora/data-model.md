# Data Model: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Overview

This document describes the data model for the project, including the structure of raw data, processed data, and analysis results. The data model ensures consistency, reproducibility, and traceability throughout the project lifecycle.

## Entities

### Scenario

A morally ambiguous visual situation identified from the source dataset.

**Attributes**:
- `scenario_id`: Unique identifier for the scenario.
- `narrative_text`: The text description of the moral scenario (curated manually).
- `original_image_path`: Path to the original image file (generated or selected).
- `ambiguity_score`: Mean score from human coding (1-5 Likert scale).
- `ambiguity_label`: Boolean indicating if the scenario is morally ambiguous (mean ≥ 3.5 AND Cohen's κ ≥ 0.6).
- `annotator_ids`: List of IDs of the ≥3 independent annotators who rated this scenario.

### Stimulus Variant

A specific manipulated version of a Scenario (low/medium/high salience).

**Attributes**:
- `variant_id`: Unique identifier for the variant.
- `scenario_id`: Foreign key to the Scenario.
- `salience_level`: Categorical value (Low, Medium, High).
- `manipulated_image_path`: Path to the manipulated image file.
- `contrast_change`: RMS contrast change in the target region (percentage).
- `semantic_similarity`: CLIP cosine similarity between original and manipulated image.
- `ssim_score`: Structural Similarity Index Score for non-target regions.
- `manipulation_valid`: Boolean indicating if the manipulation was successful (contrast ≥ 15% AND similarity ≥ 0.95 AND ssim ≥ 0.90).
- `narrative_preserved`: Boolean indicating if the separate coder panel confirmed narrative preservation (≥80% agreement).

### Response

A single data point linking a Participant to a Stimulus Variant.

**Attributes**:
- `response_id`: Unique identifier for the response.
- `participant_id`: Foreign key to the Participant.
- `variant_id`: Foreign key to the Stimulus Variant.
- `blame_rating`: Integer value (1-7 Likert scale).
- `timestamp`: Timestamp of the response.
- `salience_level`: Categorical value (Low, Medium, High) for convenience.

### Participant

An individual completing the survey.

**Attributes**:
- `participant_id`: Unique identifier for the participant.
- `start_time`: Timestamp of survey start.
- `end_time`: Timestamp of survey end.
- `total_responses`: Number of responses provided.
- `exclusion_flag`: Boolean indicating if the participant was excluded (straight-lining or other criteria).
- `exclusion_reason`: String describing the reason for exclusion (if applicable).

## Data Flow

1. **Raw Data**: Curated text narratives and source images are stored in `data/raw`.
2. **Processed Data**:
   - Scenarios are identified and coded for ambiguity.
   - Stimulus variants are generated and validated.
   - Validation metrics (CLIP, RMS, SSIM, narrative_preserved) are stored in `data/processed/stimuli/stimuli_manifest.csv`.
   - Processed data is stored in `data/processed` with checksums.
3. **Survey Data**: Responses are collected and stored in `data/processed/responses.csv`.
4. **Analysis Results**: Statistical analysis outputs (LMM tables, R², confidence intervals, power analysis) are stored in `data/results`.

## Data Integrity

- **Checksums**: All files in `data/` are checksummed and recorded in `state/projects/PROJ-507-the-influence-of-visual-salience-on-mora.yaml`.
- **Versioning**: **Any change to the data model entities (Scenario, Stimulus Variant, Response) or their attributes triggers a state file update.** Each artifact carries a content hash. Changes to artifacts update the `updated_at` timestamp.
- **Traceability**: Every figure and statistic in the final report traces back to exactly one row in `data/results` and one block in `code/`.
- **Validation Metrics**: The `stimuli_manifest.csv` file serves as the Single Source of Truth for stimulus validity, containing all validation metrics (CLIP, RMS, SSIM, narrative_preserved) as required by Constitution Principle III and IV.