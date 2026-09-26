# Environment Configuration and Checksum Verification

This document describes the environment configuration management and checksum verification system implemented for the plant traits SDM project.

## Overview

The system provides:
1. **Environment Configuration**: Loading YAML/JSON configuration files for project settings.
2. **Checksum Verification**: SHA-256 verification for all raw data downloads to ensure data integrity.
3. **Manifest Management**: Automatic registration and verification of downloaded files.

## Configuration Files

Place configuration files in the project root:
- `config.yaml` (preferred)
- `config.yml`
- `config.json`

Example `config.yaml`:
```yaml
database:
 host: localhost
 port: 5432
data:
 raw_dir: data/raw
 processed_dir: data/processed
model:
 n_estimators: 100
 max_depth: 10
```

## Checksum Verification Workflow

### 1. After Downloading Raw Data

When you download a new raw data file (e.g., from GBIF, WorldClim, or TRY), register its checksum:

```python
from src.utils.env_config import register_checksum
from pathlib import Path

file_path = Path("data/raw/your_data.csv")
register_checksum(
 manifest_path=Path("data/raw/download_manifest.json"),
 file_path=file_path
)
```

This computes the SHA-256 checksum and adds an entry to `data/raw/download_manifest.json`.

### 2. Verifying Downloads

Before processing data, verify all downloaded files:

```python
from src.utils.env_config import verify_all_downloads

results = verify_all_downloads()
# Returns dict: {file_path: True/False}
```

Or verify a single file:

```python
from src.utils.env_config import verify_download

is_valid = verify_download(Path("data/raw/your_data.csv"))
```

### 3. Manual Checksum Computation

```python
from src.utils.env_config import compute_file_checksum

checksum = compute_file_checksum(Path("data/raw/your_data.csv"))
print(f"SHA-256: {checksum}")
```

## Manifest Format

The `download_manifest.json` file stores:
```json
{
 "data/raw/example.csv": {
 "file_path": "data/raw/example.csv",
 "checksum": "abc123...",
 "algorithm": "sha256",
 "size_bytes": 123456,
 "registered_at": "/path/to/project"
 }
}
```

## Integration with Data Fetching

When implementing data fetching scripts (e.g., `fetch_gbif.py`, `fetch_climate.py`), use the following pattern:

```python
from src.utils.env_config import register_checksum, verify_checksum
from pathlib import Path

def fetch_and_verify(url: str, output_path: Path):
 #... download code...

 # Register checksum after download
 register_checksum(
 manifest_path=Path("data/raw/download_manifest.json"),
 file_path=output_path
)
```

## Testing

Run unit tests to verify checksum functionality:

```bash
pytest tests/unit/test_env_config.py -v
```

## Error Handling

- **File Not Found**: Raises `FileNotFoundError`
- **Checksum Mismatch**: Logs error and returns `False`
- **Missing Manifest**: Logs warning and returns empty results

## Best Practices

1. Always register checksums immediately after downloading new data.
2. Verify all downloads before starting analysis.
3. Include the manifest in version control (if file sizes are reasonable).
4. Document the source URL and expected checksum in your data documentation.