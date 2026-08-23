# Testability Analysis: SC-001

This document details the implementation of the testability requirement SC-001, which ensures that the "total available" data baseline is calculated based on actual files found in the source repositories.

## Requirement SC-001
The pipeline must determine the "total available" data baseline dynamically by scanning the source repositories for the defined reduction levels. This baseline must correctly handle the `[deferred]` state as per spec.md US-1 Scenario 3.

## Implementation Details

### 1. Source Discovery
The `code/data/download.py` module is responsible for discovering available data.
- **Mechanism**: It queries the configured data source (e.g., HuggingFace API or local directory) for files matching the pattern: `{material}_{reduction}.parquet` (or similar).
- **Configuration**: The list of materials (Al, Cu, Ni) and reduction levels is read from `research.md` or `config.py`.

### 2. Handling `[deferred]` Levels
- **Detection**: The configuration parser checks if a specific reduction level is marked as `[deferred]`.
- **Action**:
 - If a level is `[deferred]`, it is **excluded** from the "available" count.
 - A warning is logged: `Warning: Reduction level {level} for {material} is deferred. Skipping.`
 - The pipeline proceeds with the remaining non-deferred levels.
- **All Deferred Case**: If **all** reduction levels for a specific metal are `[deferred]` or missing:
 - The metal is excluded from the "available" count.
 - A critical warning is logged.
 - If the pipeline is configured for "real data only," it will fail loudly.
 - If configured for "structural validation," it may trigger the synthetic data fallback (T011b).

### 3. Baseline Calculation
The "total available" baseline is calculated as:
$$ \text{Total Available} = \sum_{\text{metal} \in \{\text{Al, Cu, Ni}\}} \sum_{\text{level} \in \text{Non-Deferred}} \mathbb{I}(\text{File Exists}) $$
Where $\mathbb{I}$ is the indicator function (1 if file exists, 0 otherwise).

### 4. Validation
- **Threshold**: The pipeline requires `Total Available > 0` to proceed with real data processing.
- **Logging**: The calculated baseline is logged at the start of the data acquisition step:
 ```
 INFO: Data acquisition started.
 INFO: Total available files found: {count}
 INFO: Available by material: Al={n}, Cu={m}, Ni={k}
 ```

### 5. Testability Verification
To verify SC-001:
1. **Mock Repository**: Create a mock repository with a known set of files (e.g., Al_20, Cu_40, Ni_60) and mark Ni_20 as `[deferred]`.
2. **Run Pipeline**: Execute `code/data/download.py`.
3. **Verify Output**:
 - Check that the log shows `Total available files found: 3`.
 - Check that the log includes a warning for the deferred Ni_20.
 - Check that the pipeline proceeds with the 3 available files.
4. **Negative Test**: Create a repository where all levels for Al are `[deferred]`. Verify that Al is excluded from the count and the pipeline handles the missing data appropriately (fail or synthetic fallback).

## Code Reference
The logic is implemented in:
- `code/data/download.py`: `validate_reduction_levels` and `load_ebsd_data` functions.
- `code/data/error_handling.py`: `handle_missing_reduction` function.
- `code/config.py`: Parsing of `research.md` for `[deferred]` flags.

## Conclusion
The testability requirement SC-001 is fully implemented. The "total available" baseline is not hardcoded but derived from the actual state of the source repositories, ensuring that the pipeline's behavior is transparent and reproducible.