# Data Model: The Influence of Simulated Social Validation on Neural Responses to Novel Information

## 1. Entity Definitions

### 1.1 EEGDataset
Represents a candidate public EEG study.
- `dataset_id`: Unique identifier (e.g., "ds000117").
- `task_description`: String describing the task.
- `feedback_type`: Enum: `simulated`, `real`, `mixed`, `unknown`.
- `anxiety_measure`: String (e.g., "LSAS", "SPIN", "None").
- `file_urls`: List of strings (verified URLs).
- `status`: Enum: `eligible`, `partial_eeg`, `partial_anxiety`, `ineligible`.

### 1.2 PreprocessedEpoch
Represents a single trial after filtering and ICA.
- `subject_id`: String (participant ID).
- `condition`: Enum: `simulated`, `real`.
- `epoch_data`: Array of floats (time-series data, optional for storage, usually stored in binary `.fif` or `.mat`).
- `rejected`: Boolean (True if artifact rejection threshold exceeded).

### 1.3 P300Measure
Derived metrics for each trial/subject/condition.
- `subject_id`: String.
- `condition`: Enum: `simulated`, `real`.
- `p300_amplitude`: Float (µV).
- `p300_latency`: Float (ms).
- `num_trials`: Integer (count of valid trials).
- `rejection_threshold`: Float (µV) used for this row.
- `qc_passed`: Boolean (True if trial count ≥30 and amplitude in 2-15 µV range).

### 1.4 StatisticalModel
Results of the mixed-effects regression (Primary Path) or Negative Finding (Fallback Path).
- `model_id`: String (timestamp/hash).
- `path_type`: Enum: `primary_lmm`, `negative_finding`.
- `fixed_effects`: Dictionary (term: estimate). (Only if `primary_lmm`)
- `random_effects`: Dictionary (term: variance). (Only if `primary_lmm`)
- `adjusted_pvalues`: Dictionary (term: p-value). (Only if `primary_lmm`)
- `bayes_factors`: Dictionary (term: BF). (Only if `primary_lmm`)
- `effect_sizes`: Dictionary (term: Cohen's d). (Only if `primary_lmm`)
- `threshold_used`: Float (µV). (Only if `primary_lmm`)
- `negative_finding_notes`: String (Used in Negative Finding Path to describe the data gap).

## 2. Data Flow

1.  **Raw Data**: Downloaded from verified URLs -> `data/raw/`.
2.  **Preprocessing**: `search.py` -> `preprocess.py` -> `data/processed/epochs/`.
3.  **Extraction**: `preprocess.py` -> `data/processed/p300_measures.csv`.
4.  **Analysis**: `analyze.py` reads `p300_measures.csv` -> `data/results/model_results.json`.
    - If **Primary Path**: LMM results + Bayes Factors.
    - If **Negative Finding Path**: Negative Finding Report data.
5.  **Reporting**: `report.py` reads `model_results.json` -> `data/results/report.pdf`.

## 3. Constraints

- **No PII**: Subject IDs are anonymized.
- **Checksums**: All files in `data/raw` must have a corresponding `.sha256` file.
- **Immutability**: Raw data is never modified. Derivations are new files.
- **QC Gate**: `qc_passed` must be True for inclusion in Primary Path analysis.
- **Negative Finding**: If `path_type` is `negative_finding`, all statistical fields are null/empty, and `negative_finding_notes` is populated.
