# API Documentation: Data Modules

This document provides the API reference for the data processing modules within the `code/data/` directory.
These modules handle data validation, downloading, and preprocessing.

## `code/data/validate_data_availability.py`

Validates the existence and suitability of the input dataset.

### Functions

- **`check_openneuro_ds003386() -> bool`**
 Checks if OpenNeuro ds003386 is available and contains required behavioral fields.
 - *Returns*: `True` if valid, `False` otherwise.

- **`check_alternative_datasets() -> Optional[str]`**
 Searches for alternative valid behavioral datasets (e.g., from UCI or other OpenNeuro IDs).
 - *Returns*: Path to valid dataset or `None`.

- **`main() -> int`**
 Entry point. Exits with code 1 if no valid dataset is found.

---

## `code/data/download.py`

Handles the fetching and checksum validation of the dataset.

### Functions

- **`log_error(message: str) -> None`**
 Logs an error message.

- **`log_info(message: str) -> None`**
 Logs an info message.

- **`calculate_sha256(filepath: str) -> str`**
 Calculates the SHA256 checksum of a file.

- **`download_dataset(url: str, dest_path: str) -> bool`**
 Downloads the dataset from a URL.

- **`validate_checksum(filepath: str, expected_hash: str) -> bool`**
 Validates the file checksum against the expected value.

- **`main() -> int`**
 Entry point. Downloads the dataset identified by `validate_data_availability.py`.

---

## `code/data/validate_data.py`

Validates the structure of the downloaded dataset.

### Functions

- **`load_dataset(filepath: str) -> pd.DataFrame`**
 Loads the CSV dataset.

- **`validate_fields(df: pd.DataFrame) -> bool`**
 Checks for required columns: `confidence_rating`, `source_label`.
 - *Raises*: `ValueError` if fields are missing.

- **`write_report(status: str, filepath: str) -> None`**
 Writes `data/validation_report.json` with status "PASS" or "FAIL".

- **`main() -> int`**
 Entry point.

---

## `code/data/preprocess.py`

Extracts trial-wise data and writes the derived dataset.

### Functions

- **`setup_directories() -> None`**
 Creates necessary output directories.

- **`load_and_clean_data(filepath: str) -> pd.DataFrame`**
 Loads and cleans the raw dataset.

- **`extract_trial_data(df: pd.DataFrame) -> pd.DataFrame`**
 Transforms raw data into the trial-level schema.

- **`write_output(df: pd.DataFrame, filepath: str) -> None`**
 Writes the processed data to `data/derived/trial_data.csv`.

- **`main() -> int`**
 Entry point.

---

## `code/data/validate_disjoint_trials.py`

Ensures that training and test splits used in analysis are disjoint.

### Functions

- **`load_summary_file(filepath: str) -> pd.DataFrame`**
 Loads a summary file containing split indices.

- **`get_unique_trials(df: pd.DataFrame) -> set`**
 Extracts unique trial IDs.

- **`validate_disjoint(set_a: set, set_b: set) -> bool`**
 Checks if two sets of trial IDs are disjoint.

- **`main() -> int`**
 Entry point.
