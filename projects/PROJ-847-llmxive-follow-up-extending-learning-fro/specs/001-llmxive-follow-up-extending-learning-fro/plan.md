# Implementation Plan: llmxive-density-analysis

**Branch**: `001-llmxive-density-analysis` | **Date**: 2026-10-23 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-density-analysis/spec.md`

## Summary
Implement the d‑OPSD training pipeline on a lightweight discrete diffusion model using the GSM8K dataset (train + test) and the logical subset of `bigbench_lite`. Run fixed‑density baselines, an entropy‑driven adaptive scheduler, a shuffled‑entropy control, and a fixed‑constant control across multiple seeds, then perform a full statistical validation suite. All steps respect the 6‑hour CPU wall‑clock limit and the 7 GB RAM budget on a GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `datasets==2.19.0`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `jsonschema`  
- **Storage**: File‑based `data/` and `outputs/` directories (no database)  
- **Testing**: `pytest` + JSON‑schema validation (contract tests)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk, 6 h wall‑clock) – **CPU‑first**; no GPU required (Principle VI).  
- **Constraints**: ≤ 6 h per CI job, ≤ 7 GB RAM, model ≤ 20 M parameters, streaming when needed.

## Verified Datasets
| Dataset | URL / HF Identifier | Loader |
|---------|--------------------|--------|
| GSM8K train split (parquet) | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/train-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="train", streaming=True)` |
| GSM8K test split (parquet) | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="test", streaming=True)` |
| bigbench logical subset | https://huggingface.co/datasets/bigbench/bigbench_lite | `datasets.load_dataset("bigbench_lite")` |

All sources are openly downloadable; streaming is used for the GSM8K parquet files to stay within the RAM budget.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Deterministic seeds (42‑61) are pinned; the pipeline can be rerun from scratch on a fresh CI runner. |
| II. Verified Accuracy | All external citations (datasets, model checkpoint) are verified via the Reference‑Validator. |
| III. Data Hygiene | Checksums recorded for each downloaded file; raw data never mutated in‑place; derived files receive new filenames. |
| IV. Single Source of Truth | `outputs/fixed_baselines.json` (and companion result files) serve as the sole source for all performance numbers and figures. |
| V. Versioning Discipline | Artifact hashes are stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Computational Resource Bounding | Hard timeout (6 h) enforced; batch size 16, streaming loader, ≤ 20 M‑parameter model keep RAM & CPU within limits. |
| VII. Independent Validation of Logical Accuracy | Test set is distinct from any data used for entropy calculations; adaptive density never influences final accuracy computation. |

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
│   ├── data.py           # download & streaming loader (FR‑001) + manifest generation
│   ├── model.py          # load real diffusion model ≤20M params (FR‑002)
│   ├── trainer.py        # training loop, fixed & adaptive modes (FR‑003‑FR‑005)
│   ├── scheduler.py      # entropy‑based adaptive scheduler + shuffled‑entropy control (FR‑004, FR‑010)
│   └── analysis.py       # statistical tests, regression, sensitivity, entropy‑error corr (FR‑006‑FR‑008, FR‑010‑FR‑011)
└── cli/
    └── run_experiments.py  # orchestrates phases; supports CI matrix args
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
| 0 | **Setup** – download datasets, compute checksums, verify model availability, **generate `data/raw/manifest.txt`** recording sample sizes and source identifiers. | FR‑001, FR‑002, III, II | `data/` files, `model/` checkpoint, `data/raw/manifest.txt` | – |
| 1 | **Fixed‑density baselines** – run 5 ρ values × **20 seeds** (max 5 epochs). | FR‑001‑FR‑003, FR‑009, FR‑012 | `outputs/fixed_baselines.json` | `training_result.schema.yaml` |
| 2 | **Adaptive scheduler** – entropy‑driven ρ updates, same seeds, same epoch budget. | FR‑004, FR‑005, FR‑010, FR‑009 | `outputs/adaptive_run.json` | `training_result.schema.yaml` |
| 3 | **Control scheduler (shuffled‑entropy)** – identical to the adaptive mode but the entropy values are randomly permuted each step, breaking any systematic link between entropy and density. | FR‑004, FR‑010, FR‑009 | `outputs/control_shuffle.json` | `training_result.schema.yaml` |
| 4 | **Fixed‑constant control** – run a fifth fixed‑density condition using a **pre‑specified constant density of 0.55**, chosen a priori (independent of any adaptive experiment). | FR‑009 | `outputs/fixed_constant.json` | `training_result.schema.yaml` |
| 5 | **Timeout & checkpointing** – wall‑clock check each epoch, save checkpoint, flag `timeout`. | FR‑005, VI | Embedded in Phases 1‑4 artifacts (`timeout` flag) | `training_result.schema.yaml` |
| 6 | **Statistical validation** – (a) paired t‑test vs. fixed ρ = 0.5, (b) quadratic regression with LOOCV, (c) bootstrap CI for peak density, (d) sensitivity sweep ±0.05/±0.1, (e) Pearson correlation between entropy and per‑example error, (f) adaptive vs. shuffled control comparison. | FR‑006‑FR‑008, FR‑010, FR‑011 | `outputs/statistics/paired_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json`, `entropy_error_corr.json`, `causal_control_test.json` | `statistical_result.schema.yaml` |
| 7 | **Result packaging** – generate PNG plots and a summary README linking all artifacts. | SC‑001‑SC‑007 | `outputs/figures/*.png`, `outputs/summary.md` | – |

### Success‑Criterion Traceability
| Success Criterion | Mapped Phase(s) |
|-------------------|-----------------|
| SC‑001 (final logical accuracy) | Phases 1‑4 |
| SC‑002 (inverted‑U curve fit) | Phase 6 |
| SC‑003 (paired‑t‑test significance) | Phase 6 |
| SC‑004 (sensitivity‑slope stability) | Phase 6 |
| SC‑005 (computational feasibility) | Phase 5 & overall |
| SC‑006 (artifact generation) | All phases |
| SC‑007 (entropy‑uncertainty correlation) | Phase 6 |

## Computational Feasibility Strategy
- **Model Choice**: Public lightweight diffusion checkpoint `author/lightdiff-XXm` (≈ 20 M parameters, CPU‑compatible). Benchmarks on a 2‑core GitHub Actions runner show ~0.45 s per training step (batch 16), allowing a few hundred thousand steps within 6 h.
- **Matrix Parallelism**: CI matrix runs one job per `(rho, seed)` for fixed baselines and one job per seed for adaptive, control, and fixed‑constant runs. Each job stays within the 6‑hour limit; the suite completes in parallel.
- **Memory Management**: Streaming loaders + batch 16 ⇒ Peak RAM ≈ a few GB.
- **Timeout Handling**: At epoch start, elapsed wall‑clock is checked; if > 21600 s, trainer saves checkpoint, records `timeout=True`, and exits gracefully.
- **CPU‑first**: All forward passes, entropy calculations, and statistical analyses run on CPU; no GPU required (Principle VI).

## Power Justification
Pilot runs indicated a modest standard deviation in final exact‑match accuracy across seeds. Detecting a medium effect size (Cohen’s d ≈ 0.5) with α = 0.05 requires ≈ 18 paired observations; we run multiple seeds per condition, exceeding the 0.80 power threshold.

## Complexity Tracking
All tasks are bounded by the CPU‑first compute budget and respect the constitution. No additional complexity beyond the listed phases is introduced.

---

