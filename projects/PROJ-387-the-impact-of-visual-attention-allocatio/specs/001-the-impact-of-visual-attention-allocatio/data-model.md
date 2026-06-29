# Data Model: 001-visual-attention-recall

## Entities

### EyeTrackingRecord
Represents a single reading event.
- **participant_id**: `str` (Unique identifier)
- **passage_id**: `str` (Unique identifier for story segment)
- **fixation_duration_ms**: `float` (Average fixation duration in milliseconds)
- **saccade_amplitude_deg**: `float` (Average saccade amplitude in degrees)
- **gaze_distribution_density**: `float` (AOI coverage percentage; minimum 70% for valid records per field-standard metric definition)
- **track_loss_pct**: `float` (Percentage of lost track data; must be ≤5.0)
- **calibrated**: `bool` (Eye-tracker calibration status)

### RecallScore
Represents memory performance for a passage.

**Primary Outcome**:
- **free_recall_accuracy**: `float` (0.0 to 1.0) — Standard measure for narrative memory in eye-tracking studies. Requires validation evidence (inter-rater reliability ≥0.80, test-retest stability ≥0.70).

**Secondary Outcome**:
- **recognition_score**: `float` (0.0 to 1.0) — Convergent validity measure. Same validity requirements as primary outcome.

- **participant_id**: `str` (Foreign key to EyeTrackingRecord)
- **passage_id**: `str` (Foreign key to EyeTrackingRecord)
- **valence_label**: `str` (One of: "positive", "negative", "neutral") — Must be human-rated per Constitution VII; NLP-derived labels not viable for primary analysis.

### AnalysisResult
Represents the statistical output for a specific metric-category pair.
- **attention_metric**: `str` (e.g., "fixation_duration_ms")
- **valence_category**: `str` (e.g., "positive")
- **lmm_coefficient**: `float` (Model estimate)
- **p_value_raw**: `float` (Uncorrected p-value)
- **p_value_corrected**: `float` (Bonferroni-adjusted p-value)
- **association_label**: `str` (Constant: "associational")

## Data Flow

1. **Raw Ingestion**: `data/raw/` (CSV/EDF) → Checksummed.
2. **Validation**: `code/ingestion/validate_data.py` checks schema + quality.
   - If `track_loss_pct > 5.0` → Reject.
   - If `calibrated == False` → Reject.
   - If `gaze_distribution_density < 70.0` → Reject (AOI coverage threshold).
3. **Processing**: `data/processed/` (Cleaned CSV with required columns).
4. **Analysis**: `output/results/` (JSON/CSV with AnalysisResult schema).
5. **Visualization**: `output/plots/` (PNG files).

## Constraints

- **PII**: No personal identifiers in committed data (Constitution III).
- **Immutability**: Raw data files never modified. Derivations create new files.
- **Checksums**: All files in `data/` recorded in `state/...yaml` (Constitution III).
- **Outcome Validity**: Primary outcome (free_recall_accuracy) must have documented validation evidence; secondary outcome (recognition_score) requires same validation or flagged as unverified.
- **Valence Integrity**: Valence labels must be human-rated metadata only; NLP-derived labels blocked for primary analysis (circularity risk).

## Measurement Standards

### Eye-Tracking Metrics
- **Fixation Duration**: Measured in milliseconds; average across all fixations for passage.
- **Saccade Amplitude**: Measured in degrees of visual angle; average across all saccades.
- **Gaze Distribution Density**: AOI coverage percentage (field-standard metric); minimum 70% coverage required for valid record.

### Recall Metrics
- **Free Recall Accuracy**: Proportion of correctly recalled story elements (0.0 to 1.0).
- **Recognition Score**: Proportion of correctly identified story elements from options (0.0 to 1.0).

### Valence Categories
- **Positive**: Human-rated valence >6 on 9-point Likert scale (Constitution VII).
- **Neutral**: Human-rated valence 4-6 on 9-point Likert scale.
- **Negative**: Human-rated valence <4 on 9-point Likert scale.