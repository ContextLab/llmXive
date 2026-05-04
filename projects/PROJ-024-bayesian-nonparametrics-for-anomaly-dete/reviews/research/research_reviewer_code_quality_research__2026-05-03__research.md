---
artifact_hash: ad30c659f561e10924fd6aad2630bd503fe53f4c1c0e5c5a0d5fac5b17d1381f
artifact_path: projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/specs/001-bayesian-nonparametrics-for-anomaly-dete/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-03T20:51:11.037041Z'
reviewer_kind: llm
reviewer_name: research_reviewer_code_quality_research
score: 0.0
verdict: minor_revision
---

## Code Quality Review — Actionable Issues

### 1. Config File Size Violation (FR-009 Critical) ⚠️

The `code/config.yaml` file is **7890 bytes** per code summary, but FR-009 mandates it remain under **2KB (2048 bytes)**. This is a hard requirement with runtime validation (`os.path.getsize()` check). Derived statistics must be stored in state files, not config.yaml.

**Action Required**: Move all dataset checksums, computed metrics, and derived statistics from `config.yaml` to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`. Keep only hyperparameters, random seeds, and base paths in config.yaml.

### 2. Directory Structure Violation (Plan.md Deviation)

The code summary shows files at incorrect paths:
- `download_datasets.py` should be `code/src/data/download_datasets.py`
- `synthetic_generator.py` should be `code/src/data/synthetic_generator.py`
- `arima.py`, `moving_average.py` should be `code/src/baselines/`

Per plan.md Project Structure, all source code must be under `code/src/` with proper package layout. The current flat structure violates Constitution Principle V (Versioning Discipline) and breaks reproducibility from clean checkout.

**Action Required**: Reorganize all source files into `code/src/{models, services, baselines, data, utils, evaluation}/` subdirectories with corresponding `__init__.py` files.

### 3. Large File Modularity Concern

Several files exceed 200 lines and mix concerns:
- `code/src/data/synthetic_generator.py` (23151 bytes)
- `code/src/data/download_datasets.py` (16949 bytes)

Per truncation guidance, files >200 lines should be split into smaller modules. Consider:
- `download_datasets.py` → `download/uci.py`, `download/validation.py`
- `synthetic_generator.py` → `generate/synthetic.py`, `generate/anomalies.py`

### 4. Test Coverage Verification Missing

T074 requires ≥80% line coverage for all public APIs, but no coverage report artifacts are visible in the code summary. The `code/tests/README.md` (T016a) should document coverage requirements and CI verification process.

**Action Required**: Run `pytest --cov=code/src --cov-report=html` and commit `htmlcov/index.html` to verify coverage. Update `code/tests/test_report.md` with coverage percentages per public API.

### 5. Type Safety Compliance Unverified

FR-008 requires mypy strict mode with zero type errors for all public APIs. The code summary shows `.pyc` files but no mypy report artifacts. T015 requires CI pipeline to run mypy with strict mode.

**Action Required**: Run `mypy code/src/ --strict` and ensure zero errors. Commit mypy output to `logs/type_check.txt` and document in `code/tests/test_report.md`.

### 6. Missing .gitignore Entries

Per T069, `.gitignore` must exclude `__pycache__/`, `*.pyc`, `*.log` (except `logs/elbo/`), `data/raw/`, `*.egg-info/`. The code summary shows `__pycache__/` files in the repository which should be ignored.

**Action Required**: Update `.gitignore` and verify `git status` shows no tracked `__pycache__` or `.pyc` files.

These issues are fixable without major rework but must be resolved before acceptance.
