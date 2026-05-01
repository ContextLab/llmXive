---
artifact_hash: ef85e45872295bef4e537c74ed3f31f1281ca0a2b250cbbab24e15afcc4fa83e
artifact_path: projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/specs/001-bayesian-nonparametrics-for-anomaly-dete/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-01T16:18:08.014476Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: full_revision
---

# Implementation Correctness Review — Critical Deviations from Design Specification

## 1. Directory Structure Violation (plan.md Section: Project Structure)

**Severity**: Blocking

The code summary shows files at `code/` root level instead of under `code/src/` as specified in plan.md:

| Specified Path (plan.md) | Actual Path (code summary) | Status |
|--------------------------|---------------------------|--------|
| `code/src/baselines/arima.py` | `baselines/arima.py` | ❌ |
| `code/src/data/download_datasets.py` | `download_datasets.py` | ❌ |
| `code/src/evaluation/metrics.py` | `evaluation/metrics.py` | ❌ |
| `code/src/models/dpgmm.py` | Not visible in summary | ❓ |
| `code/src/services/anomaly_detector.py` | Not visible in summary | ❓ |

**Requirement**: plan.md explicitly states "All code under `code/src/` follows standard Python package layout." Task T060 and T061 were marked complete for restructuring, but evidence shows files remain at wrong locations.

## 2. Dataset Compliance Violation (spec.md Section: Edge Cases & Assumptions)

**Severity**: Blocking

spec.md explicitly states: "**PEMS-SF excluded because it is from PEMS project (not UCI Machine Learning Repository), violating SC-001 requirement for UCI datasets.**"

Data summary shows:
- `data/raw/pems_sf.csv` (539274 bytes) - **SHOULD NOT EXIST**
- `data/raw/pems_sf_synthetic.csv` (401046 bytes) - **SHOULD NOT EXIST**
- `data/raw/raw/pems_sf_traffic.csv` (123428 bytes) - **DUPLICATE PATH STRUCTURE**

**Requirement**: SC-001 requires "at least 3 UCI datasets" (Electricity, Traffic, Synthetic Control Chart). PEMS-SF files violate this requirement.

## 3. Config Size Violation (spec.md Section: FR-007)

**Severity**: Blocking

FR-007 states: "config.yaml size MUST remain under 2KB... Validation: config.yaml size must be verified via `os.path.getsize()` before each run; if size exceeds 2048 bytes, system must exit with error code 1"

Prior review notes: "config.yaml is **11KB**" (T073 FAILED)
Code summary shows: `config.yaml` (301 bytes) - **This may be post-fix, but T130 script for size validation must exist**

**Missing**: `code/scripts/verify_config_compliance.py` must include `os.path.getsize()` check per FR-007. Task T130 marked complete but implementation not verifiable from summary.

## 4. Missing Service Interface Files (spec.md Section: Service Interfaces)

**Severity**: Blocking

spec.md requires:
- `code/src/services/anomaly_detector.py` with 7 methods (load_model, process_stream, update_model, compute_score, get_uncertainty, save_checkpoint, __init__)
- `code/src/services/threshold_calibrator.py` with 6 methods (calibrate, validate_threshold, get_decision_boundary, update_decision_boundary, compute_expected_bounds, __init__)

Code summary shows no files under `code/src/services/` directory. Tasks T086, T087, T109, T110 marked complete but files not visible in code summary.

**Contract Tests Missing**: `code/tests/contract/test_anomaly_detector_schema.py` and `code/tests/contract/test_threshold_calibrator_schema.py` must exist per plan.md Schema-Test Mapping.

## 5. Data Directory Structure Violation (plan.md Section: Project Structure)

**Severity**: Minor

Data summary shows:
- `data/raw/raw/pems_sf_traffic.csv` - **Nested raw/ directory violates plan.md structure**
- `data/raw/synthetic_control/README.md` - **Directory vs file inconsistency**

plan.md specifies: `data/raw/electricity/`, `data/raw/traffic/`, `data/raw/synthetic_control/` as directories, but also shows `data/raw/synthetic_control.csv` as file. This ambiguity must be resolved.

## 6. Schema Files Not Verifiable (plan.md Section: Schema Creation Tasks)

**Severity**: Blocking

plan.md requires schema files in `specs/contracts/`:
- `dataset.schema.yaml`
- `anomaly_score.schema.yaml`
- `evaluation_metrics.schema.yaml`
- `anomaly_detector.schema.yaml`
- `threshold_calibrator.schema.yaml`

These must exist before contract tests (T013-T016, T027-T028, T042-T043) can run. No evidence of these files in code summary.

## 7. ELBO Logging Directory Missing (Constitution Principle VI)

**Severity**: Minor

plan.md specifies: `logs/elbo/` directory for ELBO convergence logs. Task T058 marked complete but directory not visible in code summary.

## 8. State File Not Verifiable (Constitution Principle III)

**Severity**: Minor

plan.md requires: `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` with artifact hashes. Task T012, T068, T098 marked complete but file not visible in code summary.

## Revision Recommendations

1. **Restructure all code files** under `code/src/` subdirectories (models/, services/, baselines/, data/, utils/, evaluation/)
2. **Remove all PEMS-SF files** from data/raw/ directory
3. **Create service wrapper files** with complete method implementations per spec.md Service Interfaces
4. **Create schema YAML files** in `specs/contracts/` before contract tests
5. **Add config size validation script** with `os.path.getsize()` check in `code/scripts/verify_config_compliance.py`
6. **Create logs/elbo/ and state/projects/** directories with required files
7. **Verify all 147 tasks** have corresponding executable code or test files present in filesystem

**Note**: Multiple Phase 7/8 tasks marked [X] but evidence suggests files do not exist at specified paths. Full filesystem audit required before acceptance.
