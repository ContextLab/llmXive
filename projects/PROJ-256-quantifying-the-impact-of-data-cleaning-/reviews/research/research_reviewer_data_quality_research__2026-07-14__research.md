---
action_items:
- id: f1819b258ec3
  severity: writing
  text: 'File: data/raw/README.md (or create data/raw/)'
- id: b558abc7fcdb
  severity: writing
  text: 'Change: Document the exact URLs, DOIs, and SHA-256 checksums of the 2 datasets
    used (UCI HAR, UCI Shopper). If the files are not included in the repo, provide
    a verified, executable command or script to download them to this directory.'
- id: e976b9dc34e3
  severity: writing
  text: 'File: data/processed/data_quality_report.md (Create)'
- id: 6579b10e6f73
  severity: writing
  text: 'Change: Record the dataset selection process: total datasets attempted, number
    excluded (with reasons per spec edge cases), and the final n=2 sample. Explicitly
    state that the sample size is a limitation and that aggregate statistics (median/IQR)
    are unstable.'
- id: 217af9a50ba6
  severity: writing
  text: 'File: code/data_loader.py (or scripts/download_data.sh)'
- id: 945dbcad5b46
  severity: writing
  text: 'Change: Ensure the script explicitly fails (non-zero exit) if the download
    from the verified URL fails, rather than silently falling back to mock data or
    skipping the step. Add a log entry confirming the checksum of the downloaded file
    matches the expected value.'
artifact_hash: 21385be9ff6aabb87c4cf55fcdf382d57dcae8502dde76fbe91c17f85b06fa72
artifact_path: projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-14T16:03:15.431676Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

The project demonstrates a clear intent to study data cleaning impacts, but the **provenance and reproducibility of the input data are currently broken**, creating a high risk that the results cannot be verified or reproduced by a downstream user.

**1. Missing Data Provenance and Reproducibility Path**
The `spec.md` (FR-001) and `plan.md` explicitly require downloading datasets from "OpenML Small Datasets" or "UCI Machine Learning Repository." However, the `data/raw/` directory contains only a `README.md` (662 bytes) and **no actual dataset files** (e.g., `.csv`, `.arff`). The `data_loader.py` script is referenced in `tasks.md` (T011) to handle downloads, but the execution evidence shows only `data/processed/null_fpr_metrics.json` was produced.
*   **Risk**: Without the raw data files present in the repository or a documented, executable script that successfully downloads and caches them to `data/raw/`, the "baseline" and "cleaned" metrics reported in `data/processed/` are unverifiable. A reviewer cannot confirm if the data matches the claimed sources (UCI HAR, UCI Shopper) or if the cleaning strategies were applied to the correct inputs.
*   **Fix**: Either include the raw dataset files in `data/raw/` (if license permits) OR provide a robust, executable script (e.g., `scripts/download_data.sh` or `code/data_loader.py` invoked via CLI) that downloads the specific datasets (with checksums) to `data/raw/` as a mandatory step before analysis. The `data/raw/README.md` must explicitly list the URLs, DOIs, and expected checksums for the 2 datasets used.

**2. Undocumented Data Filtering and Population Shift**
The `plan.md` notes a "Dataset Feasibility Notice" stating that the spec's requirement for ≥10 datasets was reduced to 2 (UCI HAR, UCI Shopper) due to a lack of verified sources. While this is a valid methodological pivot, the **transition from the raw data to the analyzed sample is not documented in the data artifacts**.
*   **Risk**: The `data/processed/` directory contains results, but there is no `data_quality_report.md` or similar artifact detailing *why* only these 2 datasets were selected from the potential pool, or if any rows were dropped due to missingness/outliers *before* the cleaning strategies were applied. The `spec.md` (Edge Cases) mentions skipping datasets with >80% missing outcomes, but there is no record of how many datasets were attempted and how many were excluded.
*   **Fix**: Add a `data/processed/data_quality_report.md` that documents: (a) the total number of datasets attempted to be downloaded, (b) the number excluded and the specific reason for each (e.g., "Dataset X excluded: >80% missing outcome"), and (c) the final sample size (n=2) with a justification that this sample is representative of the "small dataset" population intended by the research question.

**3. Potential Synthetic Data Substitution**
The execution evidence shows `data/processed/null_fpr_metrics.json` was generated. The `spec.md` (FR-011) requires generating "permutation null datasets" (shuffling outcomes) to estimate false-positive rates.
*   **Risk**: It is unclear if the *primary* analysis results (baseline and cleaned metrics) were derived from real downloaded data or if the "2 datasets" mentioned in the plan are actually synthetic placeholders generated by the code to satisfy the execution gate. The `data/raw/` directory is empty, which strongly suggests the code might be generating mock data if the download fails silently or if the download step was skipped.
*   **Fix**: Explicitly confirm in `data/raw/README.md` that the files `uci_har.csv` and `uci_shopper.csv` (or similar) exist and are real downloads. If the code generates synthetic data for the "null" tests, ensure the *primary* analysis data is clearly distinguished and labeled as "Real Data" vs "Synthetic Null Data" in the output artifacts.

**Required Changes**
- **File**: `data/raw/README.md` (or create `data/raw/`)
  - **Change**: Document the exact URLs, DOIs, and SHA-256 checksums of the 2 datasets used (UCI HAR, UCI Shopper). If the files are not included in the repo, provide a verified, executable command or script to download them to this directory.
- **File**: `data/processed/data_quality_report.md` (Create)
  - **Change**: Record the dataset selection process: total datasets attempted, number excluded (with reasons per spec edge cases), and the final n=2 sample. Explicitly state that the sample size is a limitation and that aggregate statistics (median/IQR) are unstable.
- **File**: `code/data_loader.py` (or `scripts/download_data.sh`)
  - **Change**: Ensure the script explicitly fails (non-zero exit) if the download from the verified URL fails, rather than silently falling back to mock data or skipping the step. Add a log entry confirming the checksum of the downloaded file matches the expected value.
