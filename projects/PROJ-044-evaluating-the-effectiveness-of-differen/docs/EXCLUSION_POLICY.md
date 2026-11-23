# Dataset Exclusion Policy

## Shakespeare Dataset Exclusion

The **Shakespeare** dataset is **explicitly excluded** from this research project.

### Reason for Exclusion
Per the `plan.md` Gap Analysis and `spec.md` (Task T000), the Shakespeare dataset lacks a verified, programmatic source that meets the project's reproducibility and integrity standards.

### Implementation Constraints
1. **Code Enforcement**: The `code/config.py` module explicitly raises a `ValueError` if "shakespeare" is provided as a dataset argument.
 ```python
 if dataset == "shakespeare":
 raise ValueError("Shakespeare excluded per plan.md Gap Analysis (no verified source).")
 ```
2. **Documentation**: All documentation, including `README.md` and `tasks.md`, contains explicit warnings about this exclusion.
3. **Data Pipeline**: The data download and partitioning scripts (`code/data/download.py`, `code/data/partition.py`) are hard-coded to only accept "femnist".

### Supported Datasets
- **FEMNIST**: The only supported dataset for this project.
 - Source: Hugging Face `leaf/femnist`
 - Access Method: Streaming download via `datasets` library.

## Compliance
Any attempt to bypass this exclusion or use unsupported datasets will result in runtime errors and failure of the validation pipeline. This policy is enforced to ensure research integrity and reproducibility.