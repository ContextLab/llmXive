# SC-001 Testability Implementation

## Objective

Ensure that the data acquisition pipeline is testable by calculating the 'total available' baseline based on actual files found in source repositories for defined reduction levels, correctly handling `[deferred]` states as per spec.md US-1 Scenario 3.

## Implementation Overview

The testability of SC-001 is achieved through the following mechanisms:

1. **Dynamic File Discovery**: The pipeline scans source repositories for EBSD files matching material and reduction criteria, rather than relying on hardcoded lists.
2. **Deferred State Handling**: Reduction levels marked `[deferred]` in `research.md` are logged as warnings and skipped, with the pipeline proceeding using available data.
3. **Baseline Calculation**: The 'total available' baseline is computed from the count of **actual** files found, ensuring testability against real data availability.
4. **Synthetic Fallback Logic**: If **ALL** levels for a metal are `[deferred]` or missing, synthetic data is generated **only** for structural validation, with explicit logging.

## Detailed Workflow

### Step 1: Reduction Level Configuration

Reduction levels are defined in `research.md` (Section 2.1). Example:

```markdown
## Reduction Levels

- Aluminum: 0%, 20%, 40%, 60%, 80%
- Copper: 0%, 20%, 40%, 60%, 80%
- Nickel: 0%, 20%, 40%, 60%, 80% [deferred]
```

The `code/config.py` module parses these levels:

```python
def get_reductions() -> Dict[str, List[Tuple[int, bool]]]:
 """
 Returns dict: {material: [(level, is_deferred),...]}
 """
 # Parses research.md or config file
 pass
```

### Step 2: File Discovery

The `code/data/download.py` module scans repositories:

```python
def load_all_processed_datasets(reductions: Dict) -> List[Path]:
 """
 Scans source repos for files matching material/reduction criteria.
 Returns list of found file paths.
 """
 found_files = []
 for material, levels in reductions.items():
 for level, is_deferred in levels:
 if is_deferred:
 logger.warning(f"Skipping deferred level: {material} at {level}%")
 continue
 # Search for files matching pattern
 files = search_repository(material, level)
 found_files.extend(files)
 return found_files
```

### Step 3: Baseline Calculation

The 'total available' baseline is calculated as:

```python
total_available = len(found_files)
expected_count = sum(1 for mat, levels in reductions.items()
 for level, is_deferred in levels
 if not is_deferred)
availability_ratio = total_available / expected_count if expected_count > 0 else 0.0
```

### Step 4: Deferred State Handling

- **Scenario A**: Some levels are `[deferred]`.
 - Log warning: "Level X% for material Y is deferred; proceeding with available data."
 - Continue processing non-deferred levels.
 - Record deferred levels in metadata.

- **Scenario B**: **ALL** levels for a metal are `[deferred]` or missing.
 - Log CRITICAL: "No real data available for material Z; triggering synthetic fallback for structural validation only."
 - Invoke `code/data/generate_synthetic.py` with pinned seed.
 - Mark dataset as "synthetic" in metadata.

### Step 5: Output Metadata

The consolidated dataset (`data/processed/cleaned_ebsd.parquet`) includes:

```python
metadata = {
 "source_status": "real" or "synthetic",
 "available_levels": [0, 20, 40], # Actual levels with data
 "deferred_levels": [60, 80], # Levels marked [deferred]
 "reliability_flag": "high", # Based on availability_ratio
 "total_files_found": 15,
 "expected_files": 20,
 "availability_ratio": 0.75
}
```

## Testability Verification

### Test Case 1: All Levels Available

- **Input**: `research.md` with no `[deferred]` markers; all files present.
- **Expected**: `source_status = "real"`, `availability_ratio = 1.0`.
- **Verification**: Check metadata in `cleaned_ebsd.parquet`.

### Test Case 2: Some Levels Deferred

- **Input**: `research.md` with `[deferred]` on some levels; files present for others.
- **Expected**: Warnings logged, `source_status = "real"`, `availability_ratio < 1.0`.
- **Verification**: Check logs and metadata.

### Test Case 3: All Levels Deferred

- **Input**: `research.md` with `[deferred]` on all levels for a metal.
- **Expected**: CRITICAL log, synthetic data generated, `source_status = "synthetic"`.
- **Verification**: Check logs and metadata.

### Test Case 4: Missing Files

- **Input**: `research.md` lists levels, but files are missing from repositories.
- **Expected**: Warnings logged, `availability_ratio < 1.0`, proceed with available files.
- **Verification**: Check logs and metadata.

## Implementation Files

- `code/data/download.py`: File discovery and deferred handling.
- `code/data/error_handling.py`: Logging and exclusion logic.
- `code/data/generate_synthetic.py`: Synthetic fallback (only if all deferred).
- `code/data/consolidate.py`: Metadata injection into output Parquet.
- `code/config.py`: Parsing of `research.md` for reduction levels.

## Compliance with US-1 Scenario 3

**US-1 Scenario 3**: "If a specific metal/reduction combination is missing, skip that entry, log the error, and proceed with available data."

**Implementation**:
- Missing files are skipped during `load_all_processed_datasets`.
- Errors are logged via `logger.error()` or `logger.warning()`.
- Processing continues with remaining files.
- Exclusion logic (T014) applies if >50% of points are filtered.

## Conclusion

SC-001 testability is ensured by dynamically calculating the 'total available' baseline from actual files found, correctly handling `[deferred]` states, and providing explicit metadata in output artifacts. This allows independent verification of data availability and pipeline robustness.

---
*This document complements the main README.md and provides detailed implementation of SC-001 testability requirements.*