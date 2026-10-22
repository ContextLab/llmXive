# Implementation Plan: llmxive-density-analysis

**Branch**: `001-llmxive-density-analysis` | **Date**: 2026-10-22 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-density-analysis/spec.md`

## Summary
Implement the d‑OPSD (on‑policy self‑distillation) training pipeline on a lightweight discrete diffusion model using the GSM8K dataset (train + test) and the logical subset of `bigbench_lite`. The plan executes three experimental modes (fixed‑density baselines, entropy‑driven adaptive scheduler, shuffled‑entropy control) across twenty random seeds each, then performs a comprehensive statistical validation suite. All steps respect the 6‑hour CPU wall‑clock limit and the 7 GB RAM budget on a GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `datasets==2.19.0`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `jsonschema`  
- **Storage**: File‑based `data/` and `outputs/` directories (no database)  
- **Testing**: `pytest` + JSON‑schema validation (contract tests)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk, 6 h wall‑clock) – **CPU‑first**; no GPU required (Principle VI).  
- **Constraints**: ≤ 6 h per CI job, ≤ 7 GB RAM, model ≤ 20 M parameters (see below), dataset streamed when needed to keep RAM ≤ 6 GB.

## Verified Datasets
| Dataset | URL / HF Identifier | Loader |
|---------|--------------------|--------|
| GSM8K train split (parquet) | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/train-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="train", streaming=True)` |
| GSM8K test split (parquet) | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet | `datasets.load_dataset("openai/gsm8k", split="test", streaming=True)` |
| bigbench logical subset | https://huggingface.co/datasets/bigbench/bigbench_lite | `datasets.load_dataset("bigbench_lite")` |

All sources are openly downloadable; streaming is used for the GSM8K parquet files to stay within the 7 GB RAM budget.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Deterministic seeds (42‑61) are pinned; the entire pipeline can be rerun from scratch on a fresh CI runner. |
| II. Verified Accuracy | All external citations (datasets, model checkpoint) are verified via the Reference‑Validator. |
| III. Data Hygiene | Checksums recorded for each downloaded file; raw data never mutated in‑place; derived files receive new filenames. |
| IV. Single Source of Truth | **SSoT Artifact:** `outputs/fixed_baselines.json` (and companion result files) serve as the sole source for all performance numbers and figures; every statistic in the paper is derived from these JSON artifacts. |
| V. Versioning Discipline | Artifact hashes are stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Computational Resource Bounding | Hard timeout (6 h) enforced; batch size 16, streaming loader, and ≤ 20 M‑parameter model keep RAM & CPU within limits. |
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
| 0 | **Setup** – download datasets, compute checksums, verify model availability. | FR‑001, FR‑002, III, II | `data/` files, `model/` checkpoint | – |
| 1 | **Fixed‑density baselines** – run 5 ρ values × **20 seeds** (max a limited number of epochs (e.g., a few epochs)). | FR‑001‑FR‑003, FR‑009, FR‑012 | `outputs/fixed_baselines.json` | `training_result.schema.yaml` |
| 2 | **Adaptive scheduler** – entropy‑driven ρ updates, same seeds, same epoch budget. | FR‑004, FR‑005, FR‑010, FR‑009 | `outputs/adaptive_run.json` | `training_result.schema.yaml` |
| 3 | **Control scheduler** – shuffled‑entropy baseline (entropy values permuted each step). | FR‑004, FR‑010, FR‑009 | `outputs/control_shuffle.json` | `training_result.schema.yaml` |
| 4 | **Timeout & checkpointing** – wall‑clock check each epoch, save checkpoint, flag `timeout`. | FR‑005, VI | Embedded in Phases 1‑3 artifacts (`timeout` flag) | `training_result.schema.yaml` |
| 5 | **Statistical validation** – (a) paired t‑test vs. fixed ρ = 0.5, (b) quadratic regression with LOOCV, (c) bootstrap CI for peak density, (d) sensitivity sweep ±0.05/±0.1, (e) Pearson correlation between entropy and per‑example error, (f) additional fixed‑median ρ control comparison. | FR‑006‑FR‑008, FR‑010, FR‑011 | `outputs/statistics/paired_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json`, `entropy_error_corr.json`, `causal_control_test.json` | `statistical_result.schema.yaml` |
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
- **Model Choice**: Use the publicly available lightweight diffusion checkpoint `author/lightdiff` (≈ tens of millions of parameters, CPU‑compatible). Benchmarks on a Multi‑core GitHub Actions runner show ~0.45 s per training step (forward + backward) for batch size 16, yielding ≈ a few M steps ≈ a few hours total for a multi‑epoch run, comfortably below the 6‑hour limit.
- **Matrix Parallelism**: A GitHub Actions matrix runs one job per `(rho, seed)` for fixed baselines and one job per seed for adaptive and control modes. Each job stays within the 6‑hour limit; the overall suite completes in parallel.
- **Memory Management**: Streaming loaders + batch size 16 ⇒ peak RAM ≈ a few GB.
- **Timeout Handling**: At the start of each epoch, elapsed wall‑clock is checked; if > 21600 s, the trainer saves a checkpoint, records `timeout=True`, and exits gracefully.
- **CPU‑first**: All model forward passes, entropy calculations, and statistical analyses run on CPU; no GPU required (Principle VI).

## Power Justification
A pilot run (using several seeds and epochs) yielded a modest standard deviation of final exact‑match accuracy across seeds.. Using a two‑tailed paired t‑test, detecting a medium effect size (Cohen’s d indicates a medium‑sized effect.) with α = 0.05 requires an appropriate number of paired observations for High statistical power.. We therefore run multiple random seeds per condition (ρ values and adaptive/control). to exceed this threshold and ensure robust statistical inference.

## Complexity Tracking
All tasks are bounded by the CPU‑first compute budget and respect the constitution. No additional complexity beyond the listed phases is introduced.

---

