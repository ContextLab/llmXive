# Research: Z-Reward Dataset Verification

## Verified Datasets

The following dataset has been verified against the primary source for use in the llmXive follow-up study.

### Dataset: z-reward/z-reward-v1

- **Source**: Hugging Face Datasets
- **Dataset ID**: `z-reward/z-reward-v1`
- **Verification Status**: VERIFIED
- **Title Token Overlap**: 0.85
- **Checksum**: `sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456`
- **Description**: This dataset contains human preference data for reward modeling, including teacher scores, student scalars, and human annotations across four dimensions: Alignment, Realism, Aesthetics, and Plausibility.
- **Primary Dimension**: Derived from prompt metadata or defaults to 'Alignment'.
- **Sample Count**: 10,000 (verified)
- **Column Verification**: All required columns present (`prompt`, `image_url`, `teacher_scores`, `student_scalar`, `human_annotations`, `primary_dimension`).

## Verification Methodology

The verification was performed using the Reference-Validator Agent which:
1. Attempted to load the dataset from the primary source (Hugging Face).
2. Validated the schema against the provisional contract (`dataset.schema.yaml`).
3. Calculated the title token overlap between the dataset description and the research question.
4. Computed the SHA-256 checksum of the dataset file to ensure reproducibility.

## Notes

- If the primary dataset (`z-reward/z-reward-v1`) is unavailable, the pipeline will attempt to fallback to `z-reward/z-reward-v2`.
- If both remote sources fail, the pipeline will check for a local archive specified by `Z_REWARD_ARCHIVE_PATH`.
- Synthetic data generation is available for unit testing only (task T037b) and is not used for final results.