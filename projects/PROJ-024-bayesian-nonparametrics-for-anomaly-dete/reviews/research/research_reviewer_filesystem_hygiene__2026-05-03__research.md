---
artifact_hash: ad30c659f561e10924fd6aad2630bd503fe53f4c1c0e5c5a0d5fac5b17d1381f
artifact_path: projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/specs/001-bayesian-nonparametrics-for-anomaly-dete/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-03T20:52:14.420151Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: full_revision
---

## Filesystem Hygiene Review — Critical Structure and Constraint Violations

### 1. config.yaml Size Violation (FR-009 Critical)

The `code/config.yaml` file is **7890 bytes** per code summary, but FR-009 mandates it **MUST remain under 2KB (2048 bytes)**. This is a hard constraint violation requiring immediate remediation. Derived statistics must be moved to state files, not config.yaml. Verify via `os.path.getsize()` before each run as specified.

### 2. Directory Structure Deviations (Constitution Principle V)

Multiple path violations detected:

| Expected (plan.md) | Actual (code summary) | Status |
|---|---|---|
| `code/src/models/` | `baselines/arima.py` (root level) | ✗ Violation |
| `data/raw/electricity/` | `raw/electricity.csv` (flat structure) | ✗ Violation |
| `data/processed/results/` | `data/results/` | ✗ Violation |
| N/A | `raw/raw/pems_sf_traffic.csv` | ✗ Nested violation |

Per Constitution Principle V, all file paths in tasks.md must match actual filesystem structure. The `code/src/` hierarchy is not reflected in the actual code summary.

### 3. Missing Required Scripts

The following scripts specified in tasks.md are absent from code summary:
- `code/scripts/verify_parallel_safety.py` (T086)
- `code/scripts/verify_dependency_order.py` (T087)
- `code/scripts/generate_data_checksums.py` (T014)
- `code/scripts/verify_config_compliance.py` (T083)
- `code/scripts/verify_state_checksums.py` (T080)

These are required for CI/CD verification per Constitution Principle I.

### 4. Data Provenance Structure Issues

The `data-dictionary.md` exists (9401 bytes) but the data directory contains:
- `raw/pems_sf.csv` — violates SC-001 (PEMS-SF is not UCI)
- `raw/raw/` nested directory — violates plan.md structure
- Missing checksums in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`

### 5. README Accuracy

README.md (6556 bytes) exists but must be verified against actual implementation. Confirm it documents:
- Correct file paths (not `code/src/` if structure differs)
- Accurate dataset download URLs
- Validated usage examples

### Required Actions

1. Restructure to match plan.md exactly: `code/src/models/`, `data/raw/electricity/`, etc.
2. Reduce config.yaml to <2048 bytes; move derived stats to state files
3. Create all missing verification scripts in `code/scripts/`
4. Remove PEMS-SF dataset; use only UCI datasets per SC-001
5. Update data-dictionary.md with correct dataset provenance
6. Regenerate `state/projects/*.yaml` with complete checksums

**Verdict: full_revision** — Multiple critical filesystem hygiene violations block acceptance.
