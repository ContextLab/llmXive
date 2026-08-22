# Data Model: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Entity Definitions

### 1. StimulusImage
Represents a single moral-scenario image.
- **id**: `str` (Unique identifier, e.g., "img_001")
- **file_path**: `str` (Relative path to raw image)
- **salience_map_path**: `str` (Relative path to generated `.npy` or `.png` salience map)
- **luminance**: `float` (Mean pixel intensity) - **Archived Only**: Collected for diagnostic purposes but **excluded from the LMM model** to avoid multicollinearity with DeepGaze II salience.
- **contrast**: `float` (Standard deviation of pixel intensity) - **Archived Only**: Collected for diagnostic purposes but **excluded from the LMM model**.
- **edge_density**: `float` (Proportion of edge pixels detected) - **Archived Only**: Collected for diagnostic purposes but **excluded from the LMM model**.
- **mask_faces_path**: `str` (Optional path to face mask)
- **mask_weapons_path**: `str` (N/A - Weapons excluded from analysis)

### 2. FixationTrial
Represents a single viewing event by a participant.
- **trial_id**: `str` (Unique ID for the trial)
- **participant_id**: `str` (Participant identifier)
- **stimulus_id**: `str` (Foreign key to StimulusImage)
- **region_of_interest**: `str` ("face", "control", "other") - *Note: "weapon" is excluded.*
- **dwell_time_ms**: `float` (Total time fixating on ROI)
- **first_fixation_prob**: `float` (Probability of first fixation landing on ROI)
- **fixation_latency_ms**: `float` (Time to first fixation on ROI)
- **global_salience**: `float` (Mean salience value of the ENTIRE image - **PRIMARY PREDICTOR**)
- **salience_score_roi**: `float` (Mean salience value within the ROI - **Diagnostic Only**: **Excluded from LMM** to prevent tautology)

### 3. AnalysisResult
Represents the output of the statistical model.
- **model_id**: `str` (e.g., "Model_A", "Model_B")
- **fixed_effect_salience**: `float` (Coefficient estimate for `global_salience`)
- **p_value_salience**: `float` (Raw p-value)
- **p_value_fdr**: `float` (FDR-adjusted p-value)
- **confidence_interval_lower**: `float`
- **confidence_interval_upper**: `float`
- **random_intercepts_participant**: `dict` (Variance components)
- **random_intercepts_item**: `dict` (Variance components)
- **sensitivity_delta**: `float` (Difference in effect size between Model A and B)
- **vif_salience**: `float` (Variance Inflation Factor)
- **calculated_power**: `float` (Calculated statistical power)
- **effect_size_assumed**: `float` (Effect size used for power calculation)
- **power_status**: `str` ("sufficient" or "insufficient")
- **disclaimer**: `str` ("correlational only" if p < 0.05)

## Data Flow

1. **Raw Data**: `data/raw/openneuro_ds003123/` (Parquet/CSV/Image files)
2. **Processed Salience**: `data/processed/salience_maps/` (NumPy arrays)
3. **Processed Masks**: `data/processed/masks/` (Binary masks for Face only)
4. **Aligned Dataset**: `data/interim/aligned_trials.csv` (Merged FixationTrial + StimulusImage features)
5. **Final Output**: `data/processed/analysis_results.json` (AnalysisResult records)

## Constraints

- **Immutability**: Raw data files in `data/raw` are never modified.
- **Checksums**: Every file in `data/raw` and `data/processed` has a corresponding SHA-256 hash in the state file.
- **PII**: No participant names or emails are stored. Only anonymous IDs.
- **Schema Validation**: All output files must pass validation against `contracts/output.schema.yaml`.
- **Predictor Definition**: `global_salience` is the **only** salience predictor in the LMM. `salience_score_roi` is **excluded** from the regression equation.
- **Low-Level Features**: `luminance`, `contrast`, `edge_density` are collected for archival/diagnostic purposes only and are **not** used as covariates in the model.