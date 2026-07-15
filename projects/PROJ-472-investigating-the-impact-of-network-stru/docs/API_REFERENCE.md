# API Reference

This document provides a detailed reference for the Python modules in the Network Structure & Neural Avalanche Dynamics research pipeline.

## Table of Contents

- [Data Pipeline](#data-pipeline)
- [Analysis](#analysis)
- [Utilities](#utilities)
- [Configuration](#configuration)

---

## Data Pipeline

### `code/data/download.py`

Fetches dMRI tractography data from OpenNeuro ds003813.

**Public Functions**:
- `run_download_pipeline(subjects: List[str]) -> None`
 - Downloads `bvec`, `bval`, `dwi.nii.gz` for specified subjects.
 - **Args**:
 - `subjects`: List of subject IDs (e.g., `["sub-001", "sub-002"]`)
 - **Output**: Files saved to `data/raw/dMRI/{subject_id}/`

**Example**:
```python
from data.download import run_download_pipeline
run_download_pipeline(subjects=["sub-001", "sub-002"])
```

---

### `code/data/preprocess_dMRI.py`

Converts raw tractography to adjacency matrices using MRtrix3.

**Public Functions**:
- `download_parcellation() -> Path`
 - Downloads HCP-MMP1.0 parcellation file.
- `load_tractography(subject_id: str) -> Path`
 - Loads `.tck` file for a subject.
- `generate_connectome_matrix(tractography_path: Path, parcellation_path: Path) -> np.ndarray`
 - Computes adjacency matrix.
- `save_connectome_matrix(matrix: np.ndarray, subject_id: str) -> Path`
 - Saves matrix to `data/processed/connectomes/`.
- `run_preprocessing_for_subject(subject_id: str) -> None`
 - End-to-end preprocessing for one subject.
- `run_pipeline(subjects: List[str]) -> None`
 - Processes multiple subjects.

**Example**:
```python
from data.preprocess_dMRI import run_pipeline
run_pipeline(subjects=["sub-001"])
```

---

### `code/data/simulate_EEG.py`

Generates synthetic EEG time-series using Wilson-Cowan equations.

**Classes**:
- `WilsonCowanSimulator`
 - `__init__(connectome: np.ndarray, params: Dict)`
 - `simulate(duration: float, dt: float) -> np.ndarray`
 - Returns time-series (channels x time_steps)

**Public Functions**:
- `load_connectome(subject_id: str) -> np.ndarray`
 - Loads adjacency matrix from disk.
- `simulate_eeg_for_subject(subject_id: str) -> pd.DataFrame`
 - Generates and returns EEG data as DataFrame.
- `run_simulation_pipeline(subjects: List[str]) -> None`
 - Processes multiple subjects.

**Example**:
```python
from data.simulate_EEG import run_simulation_pipeline
run_simulation_pipeline(subjects=["sub-001"])
```

---

### `code/data/quality_control.py`

Performs QC checks on connectomes and simulated EEG.

**Public Functions**:
- `calculate_snr(eeg_data: np.ndarray) -> float`
 - Computes Signal-to-Noise Ratio.
- `check_graph_connectivity(adjacency_matrix: np.ndarray) -> bool`
 - Checks if graph is connected.
- `run_qc_for_subject(subject_id: str) -> bool`
 - Runs all QC checks; returns `True` if passed.
- `generate_qc_report(subjects: List[str]) -> pd.DataFrame`
 - Creates QC summary report.
- `calculate_pipeline_completeness(subjects: List[str]) -> float`
 - Returns proportion of subjects with complete pipelines.

**Example**:
```python
from data.quality_control import run_qc_for_subject
passed = run_qc_for_subject("sub-001")
```

---

### `code/data/store.py`

Unified storage for connectomes and EEG data.

**Public Functions**:
- `store_structural_connectome(subject_id: str, matrix: np.ndarray) -> None`
- `store_cleaned_eeg(subject_id: str, eeg_data: pd.DataFrame) -> None`
- `load_connectome_matrix(subject_id: str) -> np.ndarray`
- `load_eeg_time_series(subject_id: str) -> pd.DataFrame`
- `run_store_pipeline(subjects: List[str]) -> None`

**Example**:
```python
from data.store import store_structural_connectome
store_structural_connectome("sub-001", matrix)
```

---

## Analysis

### `code/analysis/metrics.py`

Computes network metrics (degree, clustering, rich-club).

**Public Functions**:
- `compute_degree_centrality(adjacency_matrix: np.ndarray) -> np.ndarray`
- `compute_clustering_coefficient(adjacency_matrix: np.ndarray) -> float`
- `compute_rich_club_coefficient(adjacency_matrix: np.ndarray, k: int) -> float`
- `run_metrics_pipeline(subjects: List[str]) -> None`

**Example**:
```python
from analysis.metrics import run_metrics_pipeline
run_metrics_pipeline(subjects=["sub-001"])
```

---

### `code/analysis/avalanches.py`

Detects neural avalanches from EEG time-series.

**Public Functions**:
- `z_score_normalize(signal: np.ndarray) -> np.ndarray`
- `calculate_threshold(signal: np.ndarray, percentile: float = 95) -> float`
- `detect_avalanches(signal: np.ndarray, threshold: float) -> List[AvalancheRecord]`
- `run_avalanche_detection_for_subject(subject_id: str) -> None`
- `run_avalanche_pipeline(subjects: List[str]) -> None`

**Example**:
```python
from analysis.avalanches import run_avalanche_pipeline
run_avalanche_pipeline(subjects=["sub-001"])
```

---

### `code/analysis/fitting.py`

Fits power-law models to avalanche size distributions.

**Public Functions**:
- `load_avalanche_sizes_from_store(subject_id: str) -> np.ndarray`
- `fit_power_law_model(sizes: np.ndarray) -> Dict[str, float]`
- `run_fitting_for_subject(subject_id: str) -> None`
- `run_fitting_pipeline(subjects: List[str]) -> None`

**Example**:
```python
from analysis.fitting import run_fitting_pipeline
run_fitting_pipeline(subjects=["sub-001"])
```

---

### `code/analysis/stats.py`

Statistical association analysis (correlations, permutation tests).

**Public Functions**:
- `load_metrics_data() -> pd.DataFrame`
- `compute_spearman_correlations(metrics_df: pd.DataFrame) -> pd.DataFrame`
- `run_permutation_test(x: np.ndarray, y: np.ndarray, n_shuffles: int = 10000) -> float`
- `apply_holm_bonferroni_correction(p_values: List[float]) -> List[float]`
- `calculate_vif(features: pd.DataFrame) -> pd.DataFrame`
- `run_correlation_analysis() -> pd.DataFrame`

**Example**:
```python
from analysis.stats import run_correlation_analysis
results = run_correlation_analysis()
```

---

### `code/analysis/export_metrics.py`

Exports participant-level metrics to CSV.

**Public Functions**:
- `collect_subject_metrics(subjects: List[str]) -> pd.DataFrame`
- `run_export_pipeline() -> Path`

**Example**:
```python
from analysis.export_metrics import run_export_pipeline
output_path = run_export_pipeline()
```

---

### `code/analysis/report.py`

Generates final analysis reports.

**Public Functions**:
- `load_correlation_results() -> pd.DataFrame`
- `format_associational_statement(correlation: float, p_value: float) -> str`
- `generate_executive_summary(results: pd.DataFrame) -> str`
- `generate_report() -> Path`

**Example**:
```python
from analysis.report import generate_report
generate_report()
```

---

## Utilities

### `code/config.py`

Global configuration and hyperparameters.

**Public Functions**:
- `get_data_root() -> Path`
- `ensure_directories() -> None`

**Key Variables**:
- `SIMULATION_PARAMS`: Wilson-Cowan parameters
- `PATHS`: Data directory structure

---

### `code/utils/logger.py`

Logging infrastructure.

**Public Functions**:
- `setup_logger(name: str) -> logging.Logger`
- `get_logger(name: str) -> logging.Logger`
- `log_exception(e: Exception) -> None`

---

### `code/utils/data_setup.py`

Data environment setup and checksum tracking.

**Public Functions**:
- `compute_file_checksum(file_path: Path) -> str`
- `verify_file_integrity(file_path: Path, expected_checksum: str) -> bool`
- `setup_data_environment() -> None`

---

## Entry Point

### `code/main.py`

Orchestrates the entire pipeline.

**Public Functions**:
- `parse_args() -> argparse.Namespace`
- `run_null_result_protocol() -> None`
- `main() -> None`

**Usage**:
```bash
python code/main.py --config code/config.yaml
```
