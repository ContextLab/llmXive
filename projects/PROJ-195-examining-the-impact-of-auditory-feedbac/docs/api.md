# Project API Reference

This document provides function signatures, descriptions, and usage examples for the core modules in the `code/` directory.

## `download.py`

Handles dataset acquisition, validation, and subsampling for the ds000246 dataset.

### `get_available_space(path: str) -> int`
Returns the available disk space in bytes at the specified path.

### `calculate_sha256(file_path: str) -> str`
Calculates and returns the SHA256 checksum of a file.

### `fetch_gitattributes(dataset_id: str) -> str`
Fetches the `.gitattributes` file content from the OpenNeuro dataset to determine file sizes.

### `parse_gitattributes(content: str) -> Dict[str, float]`
Parses the gitattributes content into a dictionary mapping file paths to estimated sizes (in bytes).

### `estimate_dataset_size(dataset_id: str, subjects: List[str]) -> float`
Estimates the total size of the dataset for a given list of subjects.

### `select_subsampled_subjects(max_size_gb: float = 14.0) -> List[str]`
Selects a deterministic subset of subjects (`sub-01` to `sub-10`) to ensure total size remains under 14GB.

### `download_file(url: str, dest_path: str, chunk_size: int = 8192) -> None`
Downloads a file from a URL with progress logging.

### `main() -> None`
Entry point: Validates environment, estimates size, selects subjects, and initiates download.

**Usage Example:**
```python
from download import main

if __name__ == "__main__":
 main()
```

---

## `preprocess.py`

Orchestrates the fMRIPrep execution and quality control (QC) filtering.

### `run_fmriprep_for_subject(subject_id: str, raw_dir: str, out_dir: str, fmriprep_tag: str) -> bool`
Executes the fMRIPrep Docker container for a specific subject.
- Returns `True` if successful, `False` if the process fails.

### `process_qc_and_exclude(valid_subjects_path: str, motion_threshold: float = 2.0) -> List[str]`
Parses fMRIPrep logs for motion parameters, calculates frame displacement, and filters out subjects exceeding the threshold.
- Writes the list of valid subjects to `data/processed/valid_subjects.txt`.

### `main() -> None`
Entry point: Iterates over raw data, runs fMRIPrep, performs QC, and generates the valid subject list.

**Usage Example:**
```python
from preprocess import main

if __name__ == "__main__":
 main()
```

---

## `glm_first_level.py`

Implements the first-level General Linear Model (GLM) analysis for individual subjects.

### `load_events(events_tsv_path: str) -> pd.DataFrame`
Loads event timing information from a BIDS events.tsv file.

### `create_design_matrix(events: pd.DataFrame, frame_times: np.ndarray, hrf_model: str = 'glover') -> pd.DataFrame`
Constructs the design matrix (X) by convolving event onsets with the HRF.
- Supports 'delayed' and 'pitch-shifted' conditions as part of the 'perturbed' regressor.

### `run_first_level_glm(func_file: str, design_matrix: pd.DataFrame, confounds: Optional[pd.DataFrame] = None) -> FirstLevelModel`
Fits the GLM to the functional data and returns the fitted model object.

### `main() -> None`
Entry point: Loads valid subjects, processes each subject's data, and saves contrast maps to `data/processed/`.

**Usage Example:**
```python
from glm_first_level import main

if __name__ == "__main__":
 main()
```

---

## `stats_config.py`

Manages configuration for statistical analysis parameters.

### `load_config(config_path: str = "stats_config.yaml") -> Dict[str, Any]`
Loads the YAML configuration file.

### `get_glm_params(config: Dict) -> Dict`
Extracts GLM parameters (smoothing, high_pass filter).

### `get_fdr_threshold(config: Dict) -> float`
Returns the FDR correction threshold (default 0.05).

### `get_roi_path(config: Dict) -> str`
Returns the path to the auditory cortex ROI mask.

---

## `behavior.py`

Extracts behavioral metrics and calculates learning rates.

### `extract_trial_rts(events_df: pd.DataFrame) -> Dict[str, List[float]]`
Extracts reaction times (RT) per trial from the events dataframe.

### `calculate_learning_rate_slope(rts: List[float], trial_indices: List[int]) -> float`
Calculates the slope of RT over trials using Ordinary Least Squares (OLS) regression.

### `main() -> None`
Entry point: Processes all valid subjects and saves `data/processed/learning_rates.csv`.

---

## `correlation_analysis.py`

Computes the correlation between neural activation and behavioral learning rates.

### `calculate_pearson_correlation(betas: List[float], slopes: List[float]) -> Tuple[float, float]`
Computes Pearson's r and the p-value.

### `generate_scatter_plot(betas: List[float], slopes: List[float], output_path: str) -> None`
Generates a scatter plot with regression line and saves it to `figures/`.

---

## `viz.py`

Generates visualizations of statistical maps and behavioral correlations.

### `generate_thresholded_stat_map(t_map_path: str, threshold: float, output_path: str) -> None`
Applies a threshold to a t-stat map and saves the result.

### `generate_stat_map_overlay(stat_map: str, bg_map: str, output_path: str) -> None`
Overlays a statistical map on a structural background.

---

## `utils.py`

Utility functions for BIDS path handling, logging, and QC.

### `get_bids_subject_path(root: str, subject_id: str) -> Path`
Constructs the path to a subject's BIDS directory.

### `check_motion_threshold(motion_file: str, threshold: float = 2.0) -> bool`
Checks if a subject's motion exceeds the threshold.

### `log_deviation(subject_id: str, deviation_type: str, details: str) -> None`
Logs a QC deviation to `data/processed/preprocessing.log`.

### `validate_event_labels(events_df: pd.DataFrame) -> None`
Validates that required event labels ('normal', 'delayed', 'pitch-shifted') are present. Raises an error if missing.