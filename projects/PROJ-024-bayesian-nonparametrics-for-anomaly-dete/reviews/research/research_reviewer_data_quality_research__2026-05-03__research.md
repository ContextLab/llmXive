---
artifact_hash: ad30c659f561e10924fd6aad2630bd503fe53f4c1c0e5c5a0d5fac5b17d1381f
artifact_path: projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/specs/001-bayesian-nonparametrics-for-anomaly-dete/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-03T20:51:46.976896Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: full_revision
---

## Data Quality Review — Critical Provenance and Hygiene Deficits

This review identifies **unresolved data quality issues** that block acceptance under Constitution Principles I (Reproducibility) and III (Data Hygiene). Multiple prior reviews have flagged these, but they remain unaddressed.

### 1. Config File Size Violation (FR-009 Critical) ⚠️

**Requirement**: `config.yaml` MUST remain under 2KB (2048 bytes) per FR-009. Validation: `os.path.getsize()` must exit with error code 1 if exceeded.

**Finding**: The code summary shows `config.yaml (7890 bytes)` — **nearly 4x over the limit**. This violates FR-009 and Constitution Principle I reproducibility requirements. Derived statistics must be stored in state files, not config.yaml.

**Action Required**: 
- Move all derived statistics from config.yaml to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
- Verify final config.yaml size < 2048 bytes using `code/scripts/verify_config_size.py`
- Ensure T082 and T083 pass before resubmission

### 2. Data Directory Structure Violation (Plan.md Deviation)

**Requirement**: Data must follow `data/raw/`, `data/processed/`, `data/processed/results/` per plan.md Project Structure.

**Finding**: Data summary shows files in `raw/raw/` subdirectories:
- `raw/raw/pems_sf_traffic.csv`
- `raw/raw/synthetic_control_chart.csv`
- `raw/raw/synthetic_timeseries.csv`

This violates Constitution Principle V (Versioning Discipline) — file paths in tasks.md must match actual filesystem structure.

**Action Required**:
- Consolidate all raw data under `data/raw/` (single level)
- Update `download_datasets.py` to write to correct paths
- Regenerate checksums for relocated files

### 3. Dataset Provenance Violation (UCI Requirement)

**Requirement**: SC-001 requires "at least 3 UCI datasets" (Electricity, Traffic, Synthetic Control Chart). PEMS-SF is explicitly **NOT from UCI** (per spec.md Assumptions).

**Finding**: Data summary shows `raw/pems_sf.csv` and `raw/raw/pems_sf_traffic.csv` in the repository. These violate the dataset selection criteria documented in spec.md.

**Action Required**:
- Remove PEMS-SF datasets from `data/raw/`
- Verify only UCI datasets (Electricity, Traffic, Synthetic Control Chart) remain
- Update data-dictionary.md to reflect actual datasets used

### 4. Checksum/Version Control Incomplete (Constitution Principle III)

**Requirement**: Every file under `data/` must be checksummed in state artifact_hashes map (T080, T081).

**Finding**: Multiple tasks show FAILED-IN-EXECUTION:
- T014: `code/scripts/generate_data_checksums.py exit=1`
- T080: `code/scripts/verify_state_checksums.py exit=3`

The state file may not contain complete checksum entries for all data files.

**Action Required**:
- Run `code/scripts/generate_state_checksums.py` to create complete checksums
- Verify T080 passes with exit code 0
- Ensure `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` contains SHA-256 hashes for all data files

### 5. License Documentation Incomplete (T079)

**Requirement**: All UCI dataset licenses MUST be documented in data-dictionary.md with exact license text, attribution requirements, and usage restrictions (per Constitution Principle III).

**Finding**: `data-dictionary.md (9401 bytes)` exists but license compliance has not been verified. Multiple prior data quality reviews flagged this.

**Action Required**:
- Verify data-dictionary.md contains license text for: ElectricityLoadDiagrams20112014, PEMS-Traffic, Synthetic Control Chart
- Document attribution requirements per UCI's terms
- Ensure T079 passes verification

### 6. Schema Files Missing (Plan.md Requirement)

**Requirement**: Schema YAML files in `specs/contracts/` must exist before contract tests run (plan.md Schema Creation Tasks, T016).

**Finding**: Code summary does not show `specs/contracts/` directory contents. Contract tests reference these schemas but they may not exist.

**Action Required**:
- Verify `specs/contracts/` contains: `dataset.schema.yaml`, `anomaly_score.schema.yaml`, `evaluation_metrics.schema.yaml`, `anomaly_detector.schema.yaml`, `threshold_calibrator.schema.yaml`
- Ensure contract tests can import and validate against these schemas

### 7. Missing Data Handling Unverified

**Requirement**: System must skip missing values and log warning; streaming update continues with next valid observation (Edge Cases, spec.md).

**Finding**: T030 addresses this but `code/src/models/dpgmm.py` shows multiple FAILED-IN-EXECUTION errors. Implementation may be incomplete.

**Action Required**:
- Verify missing value handling in `dpgmm.py` with test cases
- Ensure warnings are logged to appropriate log file
- Test with synthetic data containing NaN values

---

**Summary**: These are **critical data quality blockers** that violate Constitution Principles I, III, and V. All 7 issues must be resolved before the project can proceed to acceptance review. Prior reviews have flagged these repeatedly — this time they must be fixed.
