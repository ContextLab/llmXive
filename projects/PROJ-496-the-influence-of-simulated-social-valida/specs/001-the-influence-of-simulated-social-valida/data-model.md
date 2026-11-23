# Data Model: The Influence of Simulated Social Validation on Neural Responses to Novel Information

## Overview
This document defines the data structures, schemas, and flow for the project. All data artifacts must adhere to the schemas defined in `contracts/` to ensure reproducibility (Constitution Principle I) and data hygiene (Principle III).

## Entity Definitions

### 1. EEGDataset
Represents a candidate dataset from OpenNeuro/PhysioNet.
- **Attributes**:
  - `dataset_id` (str): Unique identifier (e.g., "ds00XXXX").
  - `task_description` (str): Description of the task.
  - `feedback_type` (str): "simulated", "real", "mixed", or "unknown".
  - `anxiety_measure` (str): Name of scale (e.g., "LSAS", "SPIN") or "none".
  - `file_urls` (list[str]): List of verified download URLs.
  - `status` (str): "eligible", "sim-only", "real-only", "partial", "none".

### 2. PreprocessedEpoch
Represents a single trial after filtering and ICA.
- **Attributes**:
  - `subject_id` (str): Participant ID.
  - `condition` (str): "simulated" or "real".
  - `epoch_data` (array[float]): Time-series data (channels x timepoints).
  - `rejected` (bool): True if artifact threshold exceeded.

### 3. P300Measure
The primary outcome variable derived from epochs.
- **Attributes**:
  - `subject_id` (str): Participant ID.
  - `condition` (str): "simulated" or "real".
  - `p300_amplitude` (float): Peak voltage in µV (250-550ms at Pz/CPz).
  - `p300_latency` (float): Time to peak in ms.
  - `trial_count` (int): Number of valid trials used.

### 4. StatisticalModel
Results of the LMM analysis.
- **Attributes**:
  - `fixed_effects` (dict): Estimates for intercept, validation_type, anxiety, interaction.
  - `random_effects` (dict): Variance components.
  - `adjusted_pvalues` (dict): Holm-Bonferroni corrected p-values.
  - `effect_sizes` (dict): Cohen's d for each effect.
  - `convergence` (bool): Model convergence status.

## Data Flow

1. **Ingestion**: `code/search.py` -> `data/raw/dataset_catalog.csv` (from verified URLs).
2. **Validation**: `code/search.py` checks `anxiety_measure` and `feedback_type`. If no match -> `Negative Finding Report`.
3. **Preprocessing**: `code/preprocess.py` reads raw EEG -> `data/processed/p300_metrics.csv`.
4. **Analysis**: `code/analyze.py` reads metrics -> `data/results/model_summary.csv`, `data/results/sensitivity_sweep.csv`.
5. **Reporting**: `code/report.py` generates PDF/HTML from `data/results/`.

## Constraints & Hygiene

- **Checksums**: All files in `data/raw` and `data/processed` must have a corresponding `.sha256` file.
- **PII**: No participant names or IDs that can be traced to real individuals. Use anonymized `subject_id`.
- **Immutability**: Raw data is never overwritten. All processing creates new files in `data/processed`.
