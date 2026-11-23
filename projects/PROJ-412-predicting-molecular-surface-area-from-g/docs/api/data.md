# Data Module API Documentation

This document provides detailed API documentation for the `code/data/` module, covering the implementation of Functional Requirements FR-001 to FR-007 related to data ingestion, preprocessing, and splitting.

## Overview

The data module handles the entire data lifecycle:
- **FR-001**: Data ingestion from ZINC15 with streaming
- **FR-002**: Graph construction and feature extraction
- **FR-003**: 3D conformer generation and SASA calculation
- **FR-004**: Data splitting with stratification
- **FR-005**: Data validation and schema compliance
- **FR-006**: Logging and statistics tracking
- **FR-007**: Checksum verification for reproducibility

## Modules

### `code/data/ingest.py`

Responsible for streaming data from ZINC15 and initial processing.

#### Functions

**`calculate_checksum(data_chunk: bytes) -> str`**
Calculates SHA-256 checksum of a data chunk for integrity verification (FR-007).

**`save_checksums(checksums: Dict[str, str], path: Path) -> None`**
Saves checksums to a JSON manifest file.

**`fetch_zinc15_streaming() -> Iterable[Dict]`**
Fetches SMILES data from ZINC15 using HuggingFace `datasets` streaming API.
- Implements FR-001: Real data sourcing with streaming to avoid memory issues
- Raises `ConnectionError` if source is unreachable (Fail Loudly principle)
- Respects `DATA_SOURCE_OVERRIDE` environment variable

**`process_smiles_chunk(chunk: List[str]) -> List[Dict]`**
Processes a chunk of SMILES strings:
- Validates SMILES syntax using T017 utility
- Filters molecules with >100 atoms (max atoms constraint)
- Logs excluded molecules to `logs/excluded_molecules.log` (FR-006)
- Returns list of processed molecule dictionaries

**`write_chunk_to_parquet(processed_data: List[Dict], output_path: Path) -> None`**
Writes processed data chunk to Parquet format with schema validation.

**`process_and_write_chunk(chunk: List[str], chunk_index: int) -> None`**
Orchestrates chunk processing and writing with checksum verification.

**`main() -> None`**
Entry point for the ingestion pipeline.

---

### `code/data/preprocess.py`

Handles 2D graph feature extraction, 3D conformer generation, and SASA calculation.

#### Functions

**`generate_conformer_params() -> Dict[str, Any]`**
Generates RDKit ETKDG parameters for 3D conformer generation.
- Returns dict with `numThreads`, `maxAttempts`, `energyMinimizationSteps`, `random_seed`
- Implements FR-003: Explicit parameter logging for reproducibility

**`calculate_sasa(mol: Chem.Mol, conf: Conformer) -> float`**
Calculates Solvent Accessible Surface Area (SASA) using RDKit.
- Implements FR-003: 3D geometric descriptor calculation

**`map_rdkit_exception_to_reason(exception: Exception) -> str`**
Maps RDKit exceptions to standardized failure reasons:
- 'INVALID_VALENCE' for ValueError
- 'ETKDG_FAIL' for ETKDG RuntimeError
- 'MINIMIZATION_FAIL' for minimization RuntimeError
- 'CONFORMER_GENERATION_FAIL' for generic RDKitException
- Implements FR-003: Deterministic failure reporting

**`process_molecule_3d(molecule_data: Dict) -> Dict`**
Processes a single molecule:
- Generates 3D conformer using ETKDG
- Calculates SASA and geometric descriptors
- Handles failures with detailed logging
- Implements FR-003: Complete 3D feature extraction

**`process_chunk_3d(chunk: List[Dict]) -> Tuple[List[Dict], List[Dict]]`**
Processes a chunk of molecules in parallel.
- Returns tuple of (successful_results, failed_results)
- Implements FR-003: Batch processing with failure tracking

**`save_conformer_params(params: Dict, path: Path) -> None`**
Saves conformer generation parameters to JSON file.
- Implements FR-003: Parameter persistence for reproducibility

**`save_failure_report(failures: List[Dict], path: Path) -> None`**
Saves conformer generation failures to CSV with columns: `smiles`, `failure_reason`, `atom_count`.

**`main() -> None`**
Entry point for the 3D preprocessing pipeline.

---

### `code/data/split.py`

Implements stratified data splitting by molecular weight.

#### Classes

**`SplitResult`**
Dataclass representing split results:
- `train_indices: List[int]`
- `test_indices: List[int]`
- `ks_p_value: float`
- `train_mw_stats: Dict[str, float]`
- `test_mw_stats: Dict[str, float]`

#### Functions

**`load_processed_data(path: Path) -> pd.DataFrame`**
Loads processed dataset from Parquet file.

**`calculate_mw_stats(df: pd.DataFrame) -> Dict[str, float]`**
Calculates molecular weight statistics (mean, std, min, max) for a dataframe.

**`stratified_split_by_mw(df: pd.DataFrame, test_ratio: float = 0.2, seed: int = 42) -> SplitResult`**
Performs stratified split by molecular weight:
- Implements FR-004: Stratified splitting by MW
- Performs Kolmogorov-Smirnov test for distribution comparison
- Returns SplitResult with indices and statistics

**`validate_split_distribution(split_result: SplitResult, threshold: float = 0.05) -> bool`**
Validates that train/test distributions are similar (KS p-value > threshold).

**`save_indices_to_csv(indices: List[int], path: Path) -> None`**
Saves index list to CSV file.

**`main() -> None`**
Entry point for data splitting pipeline.

---

### `code/data/validation.py`

Provides SMILES validation and dataset verification utilities.

#### Classes

**`ValidationStats`**
Dataclass for validation statistics:
- `total_count: int`
- `valid_count: int`
- `invalid_count: int`
- `excluded_count: int`
- `invalid_smiles: List[str]`

#### Functions

**`validate_smiles_syntax(smiles_list: List[str]) -> Tuple[List[str], List[str]]`**
Validates SMILES syntax and returns (valid, invalid) lists.
- Implements FR-005: Input validation
- Uses RDKit for syntax checking

**`check_atom_count(mol: Chem.Mol, max_atoms: int = 100) -> bool`**
Checks if molecule has acceptable atom count.
- Implements FR-005: Size constraint validation

**`process_single_molecule_with_validation(smiles: str) -> Optional[Dict]`**
Processes a single molecule with full validation pipeline.

**`validate_and_process_dataset(input_path: Path, output_path: Path) -> ValidationStats`**
Validates and processes entire dataset with comprehensive statistics.

**`main() -> None`**
Entry point for validation pipeline.

---

### `code/data/logging_stats.py`

Handles logging infrastructure for dataset statistics and excluded molecules.

#### Classes

**`ExcludedMolecule`**
Dataclass for excluded molecule records:
- `smiles: str`
- `reason: str`
- `atom_count: Optional[int]`
- `timestamp: str`

**`DatasetStatistics`**
Dataclass for dataset-level statistics:
- `total_processed: int`
- `total_excluded: int`
- `total_failed: int`
- `avg_molecular_weight: float`
- `avg_sasa: float`
- `timestamp: str`

#### Functions

**`log_excluded_molecule(molecule: ExcludedMolecule, log_path: Path) -> None`**
Logs excluded molecule to JSONL file.

**`log_dataset_statistics(stats: DatasetStatistics, log_path: Path) -> None`**
Logs dataset statistics to JSON file.

**`log_split_statistics(split_result: SplitResult, log_path: Path) -> None`**
Logs split statistics including KS test results.

**`main() -> None`**
Entry point for statistics logging.

---

## Traceability to Functional Requirements

| FR-ID | Description | Implemented In |
|-------|-------------|----------------|
| FR-001 | Real data ingestion from ZINC15 | `ingest.py` - `fetch_zinc15_streaming()` |
| FR-002 | Graph construction with 2D features | `preprocess.py` - `process_smiles_chunk()` |
| FR-003 | 3D conformer generation and SASA | `preprocess.py` - `process_molecule_3d()`, `calculate_sasa()` |
| FR-004 | Stratified data splitting by MW | `split.py` - `stratified_split_by_mw()` |
| FR-005 | Input validation and schema compliance | `validation.py` - `validate_smiles_syntax()`, `check_atom_count()` |
| FR-006 | Logging and statistics tracking | `logging_stats.py` - All logging functions |
| FR-007 | Checksum verification | `ingest.py` - `calculate_checksum()`, `save_checksums()` |

## Usage Examples

### Ingesting Data
```python
from code.data.ingest import fetch_zinc15_streaming, process_smiles_chunk

stream = fetch_zinc15_streaming()
for chunk in stream:
 processed = process_smiles_chunk(chunk)
 # Process and save...
```

### Generating 3D Descriptors
```python
from code.data.preprocess import process_molecule_3d, generate_conformer_params

params = generate_conformer_params()
result = process_molecule_3d({'smiles': 'CCO', 'mol': rdkit_mol})
```

### Splitting Data
```python
from code.data.split import stratified_split_by_mw, load_processed_data

df = load_processed_data('data/processed/paired_dataset.parquet')
split = stratified_split_by_mw(df, test_ratio=0.2)
```

## Error Handling

All functions follow the "Fail Loudly" principle:
- Network failures raise `ConnectionError` immediately
- Invalid data raises `ValueError` with detailed messages
- OOM conditions trigger early exit with diagnostics
- No silent fallbacks to synthetic data

## Dependencies

- `rdkit`: Chemical structure processing
- `pandas`: Data manipulation
- `scikit-learn`: Statistical tests (KS test)
- `datasets`: HuggingFace streaming
- `pyarrow`: Parquet file handling
