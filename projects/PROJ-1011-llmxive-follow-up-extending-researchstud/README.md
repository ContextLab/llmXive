# llmXive Follow-up: Extending ResearchStudio-Idea

## Task T004: Data Directory Structure and Checksum Manifest

This task implements the foundational data directory structure and checksum manifest logic required for the project.

### Features

1. **Directory Structure**: Creates standardized directories:
 - `data/raw/` - Raw, unprocessed data
 - `data/processed/` - Processed and cleaned data
 - `data/results/` - Final analysis results and reports

2. **Checksum Manifest**: Maintains `data/manifest.json` with:
 - SHA256 checksums for all tracked files
 - File sizes and metadata
 - Verification capabilities for data integrity

### Usage

```bash
# Initialize data directories and manifest
python code/setup_data_dirs.py --project-root.

# In your code:
from code.utils.data_manifest import (
 create_directory_structure,
 register_new_file,
 verify_manifest
)

# Setup directories
dirs = create_directory_structure(".")

# Register a new file after creation
register_new_file(".", "data/raw/my_data.csv")

# Verify all files in manifest
if verify_manifest("."):
 print("All files verified successfully")
```

### API

- `create_directory_structure(project_root)`: Creates data directories
- `calculate_file_checksum(file_path)`: Calculates SHA256 checksum
- `load_manifest(project_root)`: Loads manifest JSON
- `save_manifest(project_root, data)`: Saves manifest JSON
- `update_manifest_with_file(project_root, file_path)`: Adds file to manifest
- `verify_manifest(project_root)`: Verifies all manifest files
- `register_new_file(project_root, file_path)`: Convenience function for new files

### Tests

Run unit tests:
```bash
pytest tests/unit/test_data_manifest.py -v
```