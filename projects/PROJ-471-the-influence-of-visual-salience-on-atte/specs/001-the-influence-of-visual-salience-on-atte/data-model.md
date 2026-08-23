# Data Model: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## 1. Entity-Relationship Overview

The data model consists of three primary entities: `StimulusImage`, `FixationTrial`, and `AnalysisResult`.

### 1.1 StimulusImage
Represents a single stimulus image from the moral judgment dataset.
*   **ID**: Unique string (e.g., `img_001`).
*   **FilePath**: Relative path to the image file.
*   **SalienceMap**: Path to the generated `.npy` file (pixel-wise salience).
*   **LowLevelFeatures**: Dictionary of luminance, contrast, edge density (Diagnostic Only).
*   **Status**: `processed`, `failed`, `fallback_used`.

### 1.2 FixationTrial
Represents a single eye-tracking event.
*   **TrialID**: Unique string (e.g., `sub-01_trial_005`).
*   **ParticipantID**: String (e.g., `sub-01`).
*   **StimulusID**: Reference to `StimulusImage.ID`.
*   **RegionOfInterest**: Enum (`face`, `weapon`, `background`).
*   **DwellTime**: Float (ms).
*   **FirstFixation**: Boolean.
*   **FixationLatency**: Float (ms).

### 1.3 AnalysisResult
Represents the output of the statistical model.
*   **ModelID**: String (e.g., `LMM_v1`).
*   **FixedEffectEstimate**: Float.
*   **PValue**: Float.
*   **ConfidenceInterval**: Tuple (Lower, Upper).
*   **SensitivitySweepData**: List of results from Model A vs Model B.
*   **Disclaimer**: String ("correlational only").

## 2. Data Flow

1.  **Raw**: `data/raw/ds003123/` (Original dataset).
2.  **Interim**:
    *   `data/interim/salience_maps/`: `.npy` files for each image.
    *   `data/interim/masks/`: `.json` or `.png` masks for faces/weapons.
    *   `data/interim/fixations.csv`: Parsed eye-tracking data.
3.  **Processed**:
    *   `data/processed/aligned_data.csv`: Merged `StimulusImage` + `FixationTrial`.
    *   `data/processed/results.json`: Final statistical outputs.

## 3. Schema Definitions

### 3.1 Aligned Data Schema (CSV)
| Column | Type | Description |
| :--- | :--- | :--- |
| `trial_id` | str | Unique trial identifier |
| `participant_id` | str | Participant ID |
| `stimulus_id` | str | Stimulus ID |
| `roi_type` | str | `face` or `weapon` |
| `dwell_time_ms` | float | Dwell time in milliseconds |
| `first_fixation_prob` | float | Probability of first fixation |
| `salience_score` | float | Mean salience in ROI |
| `luminance` | float | Average luminance (diagnostic only) |
| `contrast` | float | Average contrast (diagnostic only) |
| `excluded` | bool | `True` if trial was excluded |

### 3.2 Results Schema (JSON)
See `contracts/output.schema.yaml` for full validation rules.
