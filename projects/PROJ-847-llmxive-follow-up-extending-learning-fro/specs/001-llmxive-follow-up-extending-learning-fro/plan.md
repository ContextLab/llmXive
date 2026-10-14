# Implementation Plan: llmxive-density-analysis

**Branch**: `001-llmxive-density-analysis` | **Date**: 2026-10-14 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-density-analysis/spec.md`

## Summary
Implement the d‑OPSD training pipeline on a lightweight discrete diffusion model using the GSM8K dataset.  
* Phase 1 – fixed‑density baseline runs for ρ ∈ {0.1, 0.3, 0.5, 0.7, 0.9} with **multiple random seeds** (default 3) to enable replication (FR‑001 – FR‑003).  
* Phase 2 – adaptive density scheduler based on prediction entropy (FR‑004).  
* Phase 3 – hard 6‑hour timeout and checkpointing (FR‑005).  
* Phase 4 – statistical validation: **independent‑samples t‑test** (instead of paired) comparing the adaptive run to the fixed baseline at ρ = 0.5, quadratic fit with bootstrap validation, sensitivity sweep (FR‑006 – FR‑008).  

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch==2.3.0`, `datasets==2.19.0`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `jsonschema`  
**Storage**: File‑based `data/` and `outputs/` directories (no DB)  
**Testing**: Optional `pytest` suite for internal contract validation; not required by the specification.  
**Target Platform**: Linux CPU runner (multi‑core) on GitHub Actions; optional GPU off‑load not required (Principle VI)  
**Constraints**: ≤ 6 h wall‑clock, ≤ 7 GB RAM, ≤ 14 GB disk (Principle VI)  
**Scale/Scope**: Full GSM test split (~several GB); model ≤ 100 M parameters (FR‑002)

## Verified Datasets
| Dataset | URL / HF Identifier | Loader |
|---------|--------------------|--------|
| GSM8K (test split, parquet) | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="test", streaming=False)` |
| bigbench_lite (logical subset) | HuggingFace `bigbench_lite` dataset | `datasets.load_dataset("bigbench_lite")` |

Both are openly downloadable without authentication and fit within CI runner disk limits. Streaming is used for GSM8K to keep RAM ≤ 6 GB.

## Constitution Check
- **I. Reproducibility** – deterministic seeds, full script reproducibility.  
- **II. Verified Accuracy** – all external citations (GSM8K, bigbench_lite, original GSM8K paper) are verified via the Reference‑Validator.  
- **III. Data Hygiene** – checksums recorded, no in‑place mutation.  
- **IV. Single Source of Truth** – every figure/table derived from `outputs/` artifacts.  
- **V. Versioning Discipline** – artifact hashes recorded in project state; any change updates `state/projects/...yaml` timestamp.  
- **VI. Computational Resource Bounding** – hard timeout logic (FR‑005).  
- **VII. Independent Validation** – test set distinct from entropy calculations (FR‑004, FR‑007).

All principles satisfied; no violations.

## Project Structure
### Documentation (this feature)
```
specs/001-llmxive-density-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── training_result.schema.yaml
│   └── statistical_result.schema.yaml
└── tasks.md   # generated later
```

### Source Code
```
src/
├── llmxive/
│   ├── __init__.py
│   ├── data.py           # dataset download & preprocessing (FR-001)
│   ├── model.py          # lightweight diffusion model loader (FR-002)
│   ├── trainer.py        # training loop, fixed & adaptive modes (FR-003‑FR-005)
│   ├── scheduler.py      # entropy‑based adaptive scheduler (FR-004)
│   └── analysis.py       # statistical tests & regression (FR-006‑FR-008)
└── cli/
    └── run_experiments.py  # entry‑point for all phases
tests/
├── unit/
│   ├── test_data.py
│   ├── test_trainer.py
│   └── test_scheduler.py
└── contract/
    └── test_contracts.py   # jsonschema validation against contracts/*.yaml
```

## Phase Details & Contract Mapping
| Phase | Description | Output Artifact | Contract |
|-------|-------------|-----------------|----------|
| 1 | Fixed‑density baseline runs (5 ρ values) with 3 seeds each. | `outputs/fixed_baselines_*.csv` | `training_result.schema.yaml` |
| 2 | Adaptive scheduler run with 3 seeds. | `outputs/adaptive_run_*.json` | `training_result.schema.yaml` |
| 3 | Timeout handling, checkpointing, metadata collection. | Included in Phase 1/2 artifacts. | `training_result.schema.yaml` |
| 4 | Statistical validation: **independent‑samples t‑test** comparing adaptive vs. fixed ρ = 0.5, quadratic regression with bootstrap, sensitivity sweep. | `outputs/statistics/independent_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json` | `statistical_result.schema.yaml` |

## Complexity Tracking
All tasks fit within the outlined phases and respect the constitution. No additional complexity introduced.

---

