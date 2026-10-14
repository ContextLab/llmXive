# Implementation Plan: llmxive-density-analysis

**Branch**: `001-llmxive-density-analysis` | **Date**: 2026-10-14 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-density-analysis/spec.md`

## Summary
Implement the d‑OPSD (on‑policy self‑distillation) training pipeline on a lightweight discrete diffusion model using the GSM8K dataset (train + test) and a supplemental logical subset from `bigbench_lite`. The plan proceeds through five ordered phases, each respecting the 6‑hour CPU limit and the 7 GB RAM budget:

1. **Fixed‑density baselines** – five retaining ratios (ρ ∈ {0.1, 0.3, 0.5, 0.7, 0.9}) each run with **ten** independent random seeds (42‑51) (FR‑001 – FR‑003, FR‑009, FR‑012).  
2. **Adaptive scheduler** – entropy‑driven dynamic adjustment of ρ (FR‑004, FR‑005, FR‑010, FR‑009).  
3. **Control scheduler** – shuffled‑entropy baseline to isolate causal effect of the adaptive heuristic (addresses methodology‑ff50dca5).  
4. **Resource bounding & checkpointing** – hard 6 h wall‑clock limit per CI job, graceful timeout, checkpoint saving (FR‑005, VI).  
5. **Statistical validation** – paired t‑test vs. fixed ρ = 0.5, quadratic regression with leave‑one‑out CV, sensitivity sweep ±0.05/±0.1, entropy‑error Pearson correlation, and power analysis with ≥ 0.80 achieved using ten seeds (FR‑006‑FR‑008, FR‑010‑FR‑011).

All results are written to JSON files validated against schemas (FR‑012).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `datasets==2.19.0`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `jsonschema`  
- **Storage**: File‑based `data/` and `outputs/` directories (no DB)  
- **Testing**: `pytest` + JSON‑schema validation (contract tests)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk, 6 h wall‑clock) – **CPU‑first**; no GPU off‑load required (Principle VI).  
- **Constraints**: ≤ 6 h per CI job, ≤ 7 GB RAM, model ≤ 100 M parameters, dataset streamed to stay within RAM.

## Verified Datasets
| Dataset | URL / HF Identifier | Loader |
|---------|--------------------|--------|
| GSM8K train split (parquet) | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/train-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="train", streaming=True)` |
| GSM8K test split (parquet) | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="test", streaming=True)` |
| bigbench logical subset | https://huggingface.co/datasets/bigbench/bigbench_lite | `datasets.load_dataset("bigbench_lite")` |

All sources are openly downloadable; **streaming** is used for GSM8K parquet files to keep RAM ≤ 6 GB.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Deterministic seeds (42‑51) are pinned; full pipeline can be rerun from scratch on a fresh CI runner. |
| II. Verified Accuracy | All external citations (datasets, model identifier) are verified via the Reference‑Validator. |
| III. Data Hygiene | Checksums recorded for each downloaded file; raw data never mutated in‑place; derived files receive new names. |
| IV. Single Source of Truth | Every figure, table, and statistic is generated from the JSON artifacts in `outputs/`; no hand‑typed numbers. |
| V. Versioning Discipline | Artifact hashes are stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Computational Resource Bounding | Hard timeout (6 h) enforced; batch size 16, streaming loader, and model size ≤ 100 M keep RAM & CPU within limits. |
| VII. Independent Validation of Logical Accuracy | Test set (GSM8K test split) is distinct from any data used for entropy calculations; adaptive density never influences final accuracy computation. |

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
│   ├── data.py           # download & streaming loader (FR‑001)
│   ├── model.py          # load real diffusion model ≤100M params (FR‑002)
│   ├── trainer.py        # training loop, fixed & adaptive modes (FR‑003‑FR‑005)
│   ├── scheduler.py      # entropy‑based adaptive scheduler + shuffled‑entropy control (FR‑004, FR‑010)
│   └── analysis.py       # statistical tests, regression, sensitivity, entropy‑error corr (FR‑006‑FR‑008, FR‑010‑FR‑011)
└── cli/
    └── run_experiments.py  # entry point orchestrating phases; supports CI matrix args
tests/
├── unit/
│   ├── test_data.py
│   ├── test_trainer.py
│   └── test_scheduler.py
└── contract/
    └── test_contracts.py   # jsonschema validation against contracts/*.yaml
```

## Phase Details & FR Mapping
| Phase | Description | Core FRs addressed | Output Artifact | Contract |
|-------|-------------|--------------------|-----------------|----------|
| 0 | **Setup** – download datasets, compute checksums, verify model availability. | FR‑001, FR‑002, III, II | `data/` files, `model/` checkpoint | – |
| 1 | **Fixed‑density baselines** – run 5 ρ values × **10 seeds** (max 10 epochs). | FR‑001‑FR‑003, FR‑009, FR‑012 | `outputs/fixed_baselines.json` | `training_result.schema.yaml` |
| 2 | **Adaptive scheduler** – entropy‑driven ρ updates, same seeds, same epoch budget. | FR‑004, FR‑005, FR‑010, FR‑009 | `outputs/adaptive_run.json` | `training_result.schema.yaml` |
| 3 | **Control scheduler** – shuffled‑entropy baseline (entropy values permuted each step) to test causal impact. | FR‑004, FR‑010, FR‑009 | `outputs/control_shuffle.json` | `training_result.schema.yaml` |
| 4 | **Timeout & checkpointing** – wall‑clock check each epoch, save checkpoint, flag `timeout`. | FR‑005, VI | Embedded in Phase 1‑3 artifacts (`timeout` flag) | `training_result.schema.yaml` |
| 5 | **Statistical validation** – (a) paired t‑test vs. fixed ρ = 0.5, (b) quadratic regression with LOOCV, (c) bootstrap CI for peak density, (d) sensitivity sweep ±0.05/±0.1, (e) Pearson correlation between entropy and per‑example error, (f) power analysis confirming ≥ 0.80 with ten seeds. | FR‑006‑FR‑008, FR‑010, FR‑011 | `outputs/statistics/paired_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json`, `entropy_error_corr.json` | `statistical_result.schema.yaml` |
| 6 | **Result packaging** – generate PNG plots (loss curves, density‑vs‑step, quadratic fit with CI, entropy‑error scatter) and a summary README linking all artifacts. | SC‑001‑SC‑007 | `outputs/figures/*.png`, `outputs/summary.md` | – |

### Success‑Criterion Traceability
| Success Criterion | Mapped Phase(s) |
|-------------------|-----------------|
| SC‑001 (final logical accuracy) | Phase 1, 2, 3 |
| SC‑002 (inverted‑U curve fit) | Phase 5 (quadratic regression) |
| SC‑003 (paired‑t‑test significance) | Phase 5 |
| SC‑004 (sensitivity‑slope stability) | Phase 5 |
| SC‑005 (computational feasibility) | Phase 4 & overall matrix execution |
| SC‑006 (artifact generation) | All phases |
| SC‑007 (entropy‑uncertainty correlation) | Phase 5 |

## Computational Feasibility Strategy
- **Matrix Parallelism**: The CI workflow will launch a GitHub Actions matrix over the Cartesian product of `rho` (5 values) and `seed` (10 values). Each matrix job runs a single training instance (fixed, adaptive, or control) and respects the 6‑hour wall‑clock limit. The total wall‑clock wall time for the suite is therefore bounded by the longest individual job, not the sum of all jobs.
- **Memory Management**: Streaming loaders for GSM8K keep peak RAM ≈ 5 GB (batch size 16).  
- **Timeout Handling**: At the start of each epoch, elapsed wall‑clock is checked; if > 21600 s, the trainer saves a checkpoint, records `timeout=True`, and exits gracefully.  

## Complexity Tracking
All tasks are bounded by the CPU‑first compute budget and respect the constitution. No additional complexity beyond the listed phases is introduced.
