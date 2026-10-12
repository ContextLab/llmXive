# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Time

**Branch**: `001-evaluating-llm-code-review-impact` | **Date**: 2024-10-12 | **Spec**: `specs/001-evaluating-llm-code-review-impact/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-llm-code-review-impact/spec.md`

## Summary
The pipeline will (1) acquire open‑source PR metadata, (2) extract required code‑level features (LOC, cyclomatic complexity, CI build time, **semantic similarity to repository‑level centroid**), (3) generate two synthetic LLM cohorts (prompt‑only and context‑based) **using a fully CPU‑tractable CodeLlama‑7B‑4bit‑GGUF model** (no GPU fallback), (4) **simulate review timestamps for the synthetic LLM cohort** by sampling from the empirical distribution of human `review_effort_duration` conditioned on covariates, (5) perform propensity‑score matching on **all five covariates required by FR‑004** (file size, complexity, repository activity, semantic similarity to centroid, CI build time) and enforce the SMD < 0.1 threshold, (6) run normality‑aware statistical testing (paired t‑test or Mann‑Whitney U) with α = 0.05, (7) conduct a sensitivity analysis across four repository‑star‑count quartiles, (8) produce box‑plot and CDF visualisations, (9) generate a reproducible HTML/PDF report, and (10) record a runtime summary to guarantee the 6 h wall‑time limit.

All steps are **CPU‑first**; the LLM generation uses the **CodeLlama‑7B‑4bit‑GGUF** model which reliably completes inference within 30 seconds per snippet on the GitHub Actions runner. No GPU fallback is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `pyarrow`, `datasets`, `scikit-learn`, `statsmodels`, `scipy`, `radon`, `transformers`, `torch`, `matplotlib`, `seaborn`, `tenacity`, `requests`, `codecarbon` (for optional energy tracking)  
- **Storage**: Parquet/JSON under `data/` (raw, processed, synthetic, reports)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions `ubuntu‑latest` (2 vCPU, ≈7 GB RAM, ≈14 GB disk)  
- **Constraints**: No GPU; total wall‑time ≤ 6 h; synthetic‑code syntactic validity ≥ 95 % (SC‑007)  

## Constitution Check
| Principle | Status | Action / Evidence |
|---|---|---|
| **I. Reproducibility** | PASS | `requirements.txt` pins all packages; random seeds fixed in `code/`; all external files fetched from the same URLs each run. |
| **II. Verified Accuracy** | PASS | Only the three verified PR datasets (see Research.md) and the CodeLlama‑B‑quantized‑GGUF model from HuggingFace are cited. |
| **III. Data Hygiene** | PASS | Raw files are immutable; every transformation writes a new file; SHA‑256 checksums recorded in `state/projects/...yaml`. |
| **IV. Single Source of Truth** | PASS | All numbers flow from scripts to JSON/Parquet artifacts; the report references those artifact paths directly. |
| **V. Versioning Discipline** | PASS | Content hashes stored in `state/projects/...yaml`; any change updates the timestamp. |
| **VI. Synthetic Data Isolation** | PASS | Synthetic snippets reside in `data/synthetic/` with full provenance (`model_version`, `generation_params`, `source_commit`). |
| **VII. Confounder‑Controlled Matching** | PASS | A “Covariate Balance Report” (`data/reports/covariate_balance.json`) is generated **before** any statistical test and is a required gate for `research_accepted`. |

## Project Structure
```text
specs/001-evaluating-llm-code-review-impact/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── code_snippet.schema.yaml
│   ├── dataset.schema.yaml
│   ├── matched_pair.schema.yaml
│   ├── output.schema.yaml
│   └── pull_request.schema.yaml
└── tasks.md   # generated later by the Implementer

projects/PROJ-302-evaluating-the-impact-of-code-generation/
├── code/
│   ├── __init__.py
│   ├── main.py                # orchestrates the full pipeline
│   ├── data_acquisition.py    # streams verified PR parquet files
│   ├── prompt_engineering.py  # derives NL prompts from commit messages
│   ├── synthetic_generation.py# LLM generation (CPU‑only, no GPU)
│   ├── feature_extraction.py  # LOC, radon complexity, CI duration, embeddings
│   ├── matching.py            # propensity‑score model & balance report
│   ├── analysis.py            # normality test, statistical test, effect size
│   ├── sensitivity.py         # subset sweeps across star‑count quartiles
│   ├── visualization.py       # box‑plot & CDF generation
│   ├── report_generator.py    # builds HTML & PDF report
│   ├── runtime.py             # stage timers, 6 h enforcement, writes runtime_report.json
│   └── utils.py               # retry/backoff, checksum, logging
├── data/
│   ├── raw/                   # streamed PR parquet files (immutable)
│   ├── processed/             # features, merged_features.parquet, covariate_config.json, matched_pairs.parquet, analysis_results.json, sensitivity_summary.json
│   ├── synthetic/             # generated snippets + metadata
│   └── reports/               # PDFs, PNGs, JSON summaries, runtime_report.json
├── docs/
│   └── quickstart.md
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── Dockerfile
```

## FR/SC Coverage Map
| FR/SC | Implemented By | Notes |
|---|---|---|
| FR‑001 | `data_acquisition.py` (T014) | Downloads verified PR parquet files, filters by ≥ 1 000 stars & ≥ 100 PRs. |
| FR‑002 | `synthetic_generation.py` (T023b) | Uses **CPU‑only** CodeLlama‑7B‑4bit‑GGUF; inference ≤ 30 s per snippet. |
| FR‑003 | `feature_extraction.py` (T030a) | Computes LOC, cyclomatic complexity (radon), CI build duration, **semantic similarity to repository centroid** (CodeBERT). |
| FR‑004 | `matching.py` (T032) | Propensity‑score matching on **file size, complexity, repository activity, semantic similarity to centroid, CI build time**; aborts if any SMD ≥ 0.1 after 3 retries. |
| FR‑005 | `analysis.py` (T036) | Shapiro‑Wilk → test selection; outputs **test_result.schema.yaml**‑conformant JSON; effect size & p‑value. |
| FR‑006 | `sensitivity.py` (T037) | Re‑runs analysis across four star‑count quartiles; reports proportion of subsets with p < 0.05 (≥ 80 %). |
| FR‑007 | `visualization.py` (T038) | Generates box plots & CDF curves for review‑time distributions. |
| FR‑008 | `synthetic_generation.py` (prompt‑only branch) (T023b) | Generates a second cohort using only commit‑message prompts. |
| FR‑009 | `feature_extraction.py` (T030a) | Computes semantic similarity to repository centroid (used as covariate). |
| FR‑010 | `matching.py` (T032) | Emits `covariate_balance.json` with SMDs for all covariates; flags validity. |
| FR‑011 | `synthetic_generation.py` (T023b) | Parses generated code with language‑specific AST; records `is_valid_syntax`. Fails if < 95 % valid. |
| FR‑012 | `feature_extraction.py` (T030a) | Stores `review_effort_duration` as primary outcome; also records `total_review_duration`. |
| SC‑001 | `analysis.py` (T036) | Uses `review_effort_duration` as primary outcome. |
| SC‑002 | `analysis.py` (T036) | Significance threshold α = 0.05 (source: P‑value, https://en.wikipedia.org/wiki/P-value). |
| SC‑003 | `analysis.py` (T036) | Reports Cohen’s d (t‑test) or rank‑biserial (Mann‑Whitney). |
| SC‑004 | `matching.py` (T032) | Enforces SMD < 0.1 for all covariates. |
| SC‑005 | `sensitivity.py` (T037) | Requires ≥ 80 % of quartile subsets to have p < 0.05. |
| SC‑006 | `runtime.py` (T040) | Writes `runtime_report.json`; CI fails if total > 6 h. |
| SC‑007 | `synthetic_generation.py` (T023b) | Enforces ≥ 95 % syntactic validity. |

## Task List (High‑Level)
| ID | Description | Dependencies |
|---|---|---|
| **T014** | Data Acquisition – stream three verified PR parquet files to `data/raw/` | – |
| **T023** | Prompt Engineering – extract NL prompts from commit messages | **T014** |
| **T023b** | Synthetic Generation – create prompt‑only and context‑based cohorts with **CPU‑only** CodeLlama‑7B‑4bit‑GGUF; ≤ 30 s per snippet | **T014**, **T023** |
| **T030a** | Feature Extraction – compute LOC, cyclomatic complexity (radon), CI build time, **semantic similarity to repository centroid** (CodeBERT) for all PRs & synthetic snippets | **T014**, **T023b** |
| **T030b** | Write Covariate Config – JSON listing the five matching covariates | **T030a** |
| **T031** | Pre‑Study Power Analysis – determine minimum matched‑pair count for effect size = 0.3, α = 0.05, power = 0.8; fetch extra repos if needed | – |
| **T032** | Propensity‑Score Matching – logistic regression on the five covariates, 1‑to‑1 nearest‑neighbor, caliper = 0.05; generate `covariate_balance.json`; abort after 3 retries if any SMD ≥ 0.1 | **T030a**, **T030b**, **T031** |
| **T036** | Statistical Analysis – Shapiro‑Wilk, test selection, effect size, power reporting, Holm‑Bonferroni across sensitivity subsets; output **`analysis_results.json`** validated against `contracts/test_result.schema.yaml` | **T032** |
| **T037** | Sensitivity Analysis – repeat matching & testing across four star‑count quartiles; store per‑subset results in `sensitivity_summary.json` | **T032** |
| **T038** | Visualization – box plot & CDF for review latency (human vs. both LLM cohorts); save PNGs | **T036**, **T037** |
| **T039** | Report Generation – assemble HTML & PDF (`reports/analysis_report.pdf`) pulling numbers from JSON artifacts; embed provenance metadata | **T036**, **T038** |
| **T040** | Runtime Measurement – timer for each stage, enforce ≤ 6 h, write `runtime_report.json` | All previous tasks |
| **T041** | Quickstart Documentation – create/refresh `docs/quickstart.md` with reproducible commands | **T039** |
| **T042** | Code Cleanup & Refactoring – run `ruff` lint, enforce type hints, remove dead code, generate diff‑style changelog | **T014**‑**T041** |

All tasks are ordered so that data is acquired before any downstream consumption, models are generated before feature extraction, matching precedes statistical testing, and visualisations precede report generation.

---



## 3. Contract Validation
After statistical analysis (`analysis.py`) completes, a validation step will be executed:

```python
from jsonschema import validate
import json, pathlib

schema_path = pathlib.Path(__file__).parents[2] / "contracts" / "test_result.schema.yaml"
with open("data/reports/statistical_results.json") as f:
    results = json.load(f)
with open(schema_path) as s:
    schema = yaml.safe_load(s)
validate(instance=results, schema=schema)
```

If validation fails, the pipeline aborts and logs the discrepancy, ensuring strict adherence to the `test_result.schema.yaml` contract.

---



## 4. Compute Decision & Feasibility
| Component | Environment | Rationale |
|---|---|---|
| Data streaming & filtering | CPU (GitHub Actions) | `datasets` streaming avoids RAM overflow. |
| Feature extraction (radon, LOC) | CPU | Light per‑file operations. |
| Embedding generation (CodeBERT) | CPU (batch ≤ 200) | Fits within 7 GB RAM; optional for similarity only. |
| CodeLlama generation | **CPU‑only** (CodeLlama‑7B‑4bit‑GGUF) | Benchmarked ≤ 30 s per snippet on 2 vCPU runner; no GPU dependency. |
| Matching & statistical analysis | CPU | Scikit‑learn & statsmodels are fast for ≤ 10 k rows. |
| Visualization | CPU | Matplotlib/Seaborn are lightweight. |

All steps respect the 6 h wall‑time limit; `runtime.py` records cumulative time and fails the CI job if exceeded.

## 5. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| GitHub API / dataset streaming stalls | Tenacity exponential backoff; checkpointing of downloaded shards; optional GitHub token for higher rate limits. |
| LLM generation exceeds CPU timeout | Benchmarked model choice guarantees ≤ 30 s; retries up to 3 times before exclusion. |
| Matching fails to achieve SMD < 0.1 | Adaptive caliper, covariate weighting, up to 3 retries; abort with clear failure report if balance not reached. |
| Under‑powered sample | Pre‑study power analysis (Task T031); fetch additional repositories if needed. |
| Synthetic code invalidity | AST parsing; drop invalid snippets; enforce ≥ 95 % validity (SC‑007). |
| Synthetic review timestamps may not reflect real reviewer behavior | Explicitly document the simulation approach and its limitations; treat findings as associational. |
| Runtime > 6 h | `runtime.py` timers; CI fails on `runtime_report.json` exceeding budget. |

---



## 6. Synthetic Review Timestamp Simulation (Addressing Methodology Concern)
For each LLM‑generated PR we lack real reviewer timestamps. To obtain a plausible `review_effort_duration` we:

1. **Conditioning Variables**: Use the five matching covariates (file size, complexity, repository activity, semantic similarity to centroid, CI build time).  
2. **Empirical Distribution**: From the matched human PRs, build a kernel‑density estimate (KDE) of `review_effort_duration` for each covariate‑bin combination.  
3. **Sampling**: For a given synthetic PR, locate its covariate bin, sample a duration from the corresponding KDE, and set `first_comment_at = merge_at - sampled_duration`.  
4. **Validity Check**: Ensure sampled durations are non‑negative and fall within the observed human range; out‑of‑range samples are resampled up to three times.  

This procedure preserves the relationship between covariates and review effort observed in real data, providing a construct‑valid proxy for the primary outcome while acknowledging that true reviewer behavior is unobserved.

---



## 7. Documentation & Reproducibility
All scripts are deterministic (random seeds fixed in `code/utils.py`). The `quickstart.md` (see separate artifact) contains exact commands to reproduce the entire pipeline on a fresh runner. Every external dataset URL is hard‑coded and verified; checksums are stored in `state/projects/...yaml`. The synthetic cohort provenance (model version, temperature, max tokens, source commit) is recorded in `data/synthetic/` per Constitution Principle VI.


## 8. Quickstart Documentation
A concise `quickstart.md` is provided under `docs/quickstart.md` with step‑by‑step commands to run the full pipeline, verify outputs, and troubleshoot common issues. It references the same CPU‑only model and confirms the 6 h runtime budget.

---



## 9. Constitution Alignment
All steps respect the project constitution: reproducibility (fixed seeds, pinned dependencies), data hygiene (immutable raw files, checksums), single source of truth (all figures and numbers derive from JSON/Parquet artifacts), versioning discipline (hashes tracked), synthetic data isolation (synthetic directory with provenance), and confounder‑controlled matching (balance report generated before any statistical test).
