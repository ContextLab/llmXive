# Static Analysis API Reference

This module provides utilities for calculating structural regularity scores for Python repositories.
The scoring system evaluates directory structure, test presence, and import patterns to determine
how "standard" a repository layout is.

## Functions

### `calculate_dir_score(directory_path: Path) -> float`

Calculates a normalized score (0.0 to 1.0) based on the presence of standard project directories.

**Parameters:**
- `directory_path` (Path): Path to the root of the repository.

**Returns:**
- `float`: A score where 1.0 indicates all standard directories (`src/`, `tests/`, `docs/`) are present,
 0.0 indicates none are present, and partial presence results in linear interpolation.

**Example:**
```python
from pathlib import Path
from static_analysis import calculate_dir_score

score = calculate_dir_score(Path("/path/to/repo"))
print(f"Directory Score: {score}")
```

### `calculate_test_score(directory_path: Path) -> float`

Calculates a binary score based on the presence of a `tests/` directory.

**Parameters:**
- `directory_path` (Path): Path to the root of the repository.

**Returns:**
- `float`: 1.0 if `tests/` exists, 0.0 otherwise.

### `extract_imports_from_file(file_path: Path) -> Tuple[List[str], List[str]]`

Parses a Python file to extract absolute and relative imports.

**Parameters:**
- `file_path` (Path): Path to the Python file.

**Returns:**
- `Tuple[List[str], List[str]]`: A tuple containing (absolute_imports, relative_imports).
 - `absolute_imports`: List of strings like `["os", "sys"]`.
 - `relative_imports`: List of strings like `[".utils", "..config"]`.

### `calculate_import_score(directory_path: Path) -> float`

Calculates the ratio of absolute imports to total imports across all Python files in the repository.

**Parameters:**
- `directory_path` (Path): Path to the root of the repository.

**Returns:**
- `float`: A score between 0.0 (all relative) and 1.0 (all absolute). Returns 0.0 if no imports are found.

### `calculate_regularity_score(directory_path: Path) -> float`

Computes the final weighted regularity score for a repository.

**Formula:**
`score = dir_score + w1 * test_score + w2 * import_score`

Where `w1` and `w2` are adjustable weights (defaulting to 0.5 each in this implementation).

**Parameters:**
- `directory_path` (Path): Path to the root of the repository.

**Returns:**
- `float`: The normalized regularity score.

### `analyze_repository(directory_path: Path) -> Dict[str, Any]`

Performs a full analysis of a repository and returns a dictionary containing all component scores
and the final regularity score.

**Parameters:**
- `directory_path` (Path): Path to the root of the repository.

**Returns:**
- `Dict[str, Any]`: A dictionary with keys:
 - `dir_score`: float
 - `test_score`: float
 - `import_score`: float
 - `regularity_score`: float

### `main()`

Entry point for CLI execution. Scans a provided directory for Python repositories, calculates
regularity scores, and prints results to stdout.

**Usage:**
```bash
python -m static_analysis /path/to/repositories
```
