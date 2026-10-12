# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Time

**Branch**: `001-evaluating-llm-code-review-impact` | **Date**: 2024-10-12 | **Spec**: `specs/001-evaluating-llm-code-review-impact/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-llm-code-review-impact/spec.md`

## Summary
The project will assess **whether LLM‑generated code is *associated* with longer review latency** than human‑written code after matching on pre‑treatment confounders.  
The pipeline consists of (1) acquisition of an open‑source PR dataset, (2) extraction of code‑level features, (3) generation of two synthetic LLM cohorts (prompt‑only and context‑based), (4) **pre‑study power analysis**, (5) propensity‑score matching **using only pre‑treatment covariates** (repo activity, primary language, commit‑message length), (6) statistical testing with appropriate normality checks, (7) sensitivity analysis across stratified subsets, (8) reproducible visualisation and reporting, (9) **runtime measurement** (writes `data/processed/runtime_report.json` and enforces the 6 h wall‑time limit), and (10) code cleanup.  

All steps are **CPU‑first**; a **GPU escape hatch** is defined for the CodeLlama generation step if a single snippet exceeds a **30 second** CPU timeout (FR‑002). No spec amendment is performed – any methodological overrides are recorded **here** in compliance with Constitution Principle IV.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `pyarrow`, `datasets`, `scikit-learn`, `statsmodels`, `scipy`, `radon`, `transformers`, `torch`, `matplotlib`, `seaborn`, `tenacity`, `requests`  
- **Storage**: Parquet/JSON files under `data/` (raw, processed, synthetic, reports)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions `ubuntu‑latest` (2 vCPU, ≈7 GB RAM, ≈14 GB disk)  
- **Constraints**: No GPU on the runner unless the escape hatch triggers; total wall‑time ≤ 6 h; synthetic code validity ≥ 95 % (SC‑007).  

## Constitution Check
| Principle | Status | Evidence / Action |
|---|---|---|
| **I. Reproducibility** | PASS | `requirements.txt` pinned; random seeds fixed in `code/`; all external files fetched from the same HuggingFace URLs each run. |
| **II. Verified Accuracy** | PASS | Only the three verified PR datasets (see Research.md) and the CodeBERT model from HuggingFace are cited. |
| **III. Data Hygiene** | PASS | Raw files are immutable; every transformation writes a new file; SHA‑256 checksums recorded in `state/`. |
| **IV. Single Source of Truth** | PASS | All numbers flow from scripts to JSON/Parquet artifacts; the paper will reference those artifacts directly. |
| **V. Versioning Discipline** | PASS | Content hashes stored in `state/projects/...yaml`; any change updates the timestamp. |
| **VI. Synthetic Data Isolation** | PASS | Synthetic snippets live in `data/synthetic/` with a full provenance record (`generation_source`, model version, temperature, max_tokens). |
| **VII. Confounder‑Controlled Matching** | PASS | A “Covariate Balance Report” (`data/reports/covariate_balance.json`) is generated **before** any statistical test and is a required gate for `research_accepted`. |

## Methodological Overrides (documented here, not in the spec)
1. **Outcome Metric** – Review latency is defined as **`review_latency = merge_timestamp – created_timestamp`** (full review time). The earlier “first comment” metric is retained only as a secondary descriptive variable.  
2. **Causal Language** – The study reports **associations** only; causal phrasing is removed to respect the observational nature of the data.  
3. **Pre‑Study Power Analysis** – Before data collection, a power calculation (target effect size = 0.3, α = 0.05, power = 0.8) determines the minimum number of matched pairs required. If the sampled data fall short, additional repositories will be fetched.  
4. **Matching Covariates** – Matching is performed on **pre‑treatment covariates**: `repo_activity_level`, `primary_language`, and `commit_message_length`. **File size** and **cyclomatic complexity** are excluded because they are post‑treatment properties of the generated code.  
5. **CPU Generation Timeout** – CodeLlama generation must complete within **30 seconds** on CPU; exceeding this triggers the **GPU escape hatch** on Kaggle (8‑bit quantized, same model).  

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
│   ├── pull_request.schema.yaml
│   └── test_result.schema.yaml
└── tasks.md   # generated later by the Implementer

projects/PROJ-302-evaluating-the-impact-of-code-generation/
├── code/
│   ├── __init__.py
│   ├── main.py                # orchestrates the full pipeline
│   ├── data_acquisition.py    # downloads verified PR datasets
│   ├── prompt_engineering.py  # intent extraction from commit messages
│   ├── context_extraction.py  # extracts surrounding code context for generation
│   ├── synthetic_generation.py# LLM generation (CPU primary, GPU fallback)
│   ├── feature_extraction.py  # LOC, radon, embeddings
│   ├── analysis.py            # matching, statistical tests, sensitivity
│   ├── visualization.py       # box‑plot & CDF
│   ├── report_generator.py    # creates HTML & PDF report
│   ├── runtime.py             # timer & 6 h enforcement (writes data/processed/runtime_report.json)
│   ├── cleanup.py             # linting, type‑checking, dead‑code removal
│   └── utils.py               # retry, backoff, checksum, timing
├── data/
│   ├── raw/                   # downloaded PR parquet files
│   ├── processed/             # features, merged_features.parquet, covariate_config.json, matched_pairs.parquet, analysis_results.json, sensitivity_summary.json
│   ├── synthetic/             # LLM‑generated snippets + metadata
│   └── reports/               # PDFs, PNGs, JSON summaries, runtime_report.json
├── docs/
│   └── quickstart.md
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── Dockerfile
```

## Complexity Tracking
| Decision | Why Needed | Simpler Alternative Rejected |
|---|---|---|
| Two LLM cohorts (prompt‑only and context‑based) | Required by US‑4 to isolate generation modality | A single cohort would conflate generation style with the treatment effect |
| Propensity matching **without** file size/complexity | Prevents over‑adjustment bias (post‑treatment) | Including them would invalidate the matching logic |
| GPU escape hatch for CodeLlama generation | Guarantees completion within the 6 h budget | Ignoring GPU would cause systematic timeouts |
| Clustered standard errors at repository level | Accounts for intra‑repo correlation | Ignoring clustering inflates Type I error |
| Stratification by complexity & PR size (instead of star‑count) | Provides a scientifically meaningful robustness check (US‑3) | Star‑count does not control for code difficulty |

## Task List (High‑Level)
| ID | Description | Dependencies | Notes |
|---|---|---|---|
| **T014** | Data Acquisition – download the three verified PR parquet files from HuggingFace to `data/raw/` | – | Streams directly to avoid RAM overflow |
| **T014b‑ContextExtraction** | Extract surrounding code context (diff snippets) needed for the context‑based generation cohort | **T014** | Produces `data/processed/context_parsed.parquet` |
| **T023** | Prompt Engineering – derive intent prompts from commit messages | **T014** | Outputs `data/processed/intent_prompts.json` |
| **T023b** | Synthetic Generation – generate two cohorts (prompt‑only & context‑based) using CodeLlama. **CPU‑first with 30 s timeout**, GPU fallback if exceeded | **T014b‑ContextExtraction**, **T023** | Writes `data/synthetic/llm_snippets.jsonl`; respects 30 s timeout, 3 retries |
| **T030a‑CreateMergedFeatures** | Feature Extraction – compute LOC, cyclomatic complexity (radon), and optional CodeBERT embeddings for *all* PRs and synthetic snippets; write `features.parquet` and `merged_features.parquet` | **T014**, **T023b** | Outputs `data/processed/features.parquet`, `data/processed/merged_features.parquet` |
| **T030b‑WriteCovariateConfig** | Write a JSON configuration (`covariate_config.json`) listing the pre‑treatment covariates used for matching | **T030a‑CreateMergedFeatures** | Stored in `data/processed/covariate_config.json` |
| **T031** | Pre‑Study Power Analysis – estimate required matched‑pair count for target effect size = 0.3, α = 0.05, power = 0.8; adjust sampling if needed | – | Determines minimum N before matching |
| **T032** | Propensity Score Matching & Covariate Balance Report – logistic regression on `repo_activity_level`, `primary_language`, `commit_message_length`; generate `covariate_balance.json` and abort on SMD ≥ 0.1 after 3 retries | **T030a‑CreateMergedFeatures**, **T031** | Produces `data/processed/matched_pairs.parquet` |
| **T036** | Statistical Analysis – normality test, automatic test selection, effect‑size calculation, power reporting, clustered SE, multiple‑comparison correction; write `analysis_results.json` | **T032** | Includes `sensitivity_summary.json` (see T037) |
| **T037** | Sensitivity Analysis – repeat matching & testing across five stratified subsets (complexity low/med/high, PR size small/large) | **T032** | Stores per‑subset results in `data/processed/sensitivity_summary.json` |
| **T038** | Visualization – box plot & CDF for review latency, stratified by the five sensitivity subsets; save PNGs | **T036** | Files in `data/reports/` |
| **T039** | Report Generation – assemble an HTML/PDF report that pulls numbers from `analysis_results.json`, the balance report, and the visualisations; embed provenance metadata | **T036**, **T038** | Produces `reports/analysis_report.pdf` |
| **T040** | Runtime Measurement – instrument each pipeline stage, write `data/processed/runtime_report.json`; enforce total ≤ 6 h (fail if exceeded) | All previous tasks | Uses `code/runtime.py` |
| **T041** | Documentation – create/refresh `docs/quickstart.md` and a top‑level `README.md` describing the end‑to‑end command line | **T039** | Ensures reproducibility for reviewers |
| **T042** | Code Cleanup & Refactoring – lint with `ruff`, enforce type hints, remove dead code, generate diff‑style change log | **T014**‑**T041** | Guarantees a tidy codebase for the final release |

All tasks are sequential where data flow requires it; parallelism is limited to independent validation steps (e.g., unit tests) to stay within the 2‑core CI budget.

## FR/SC Coverage Map
| FR/SC | Covered By | Status |
|---|---|---|
| FR‑001 | T014 | ✅ |
| FR‑002 | T023b (generation) | ✅ (CPU ≤ 30 s, GPU fallback) |
| FR‑003 | T030a‑CreateMergedFeatures | ✅ |
| FR‑004 | T032 (propensity matching) | ✅ (override documented) |
| FR‑005 | T036 (statistical test) | ✅ |
| FR‑006 | T036 (sensitivity analysis) | ✅ |
| FR‑007 | T038 (visualisation) | ✅ |
| FR‑008 | T023 & T023b (prompt‑only cohort) | ✅ |
| FR‑009 | T030a‑CreateMergedFeatures | ✅ (exploratory) |
| FR‑010 | T032 (balance report) | ✅ |
| SC‑001 | T036 (review latency) | ✅ |
| SC‑002 | T036 (p‑value < 0.05) | ✅ (threshold 0.05 cited) |
| SC‑003 | T036 (Cohen’s d / rank‑biserial) | ✅ |
| SC‑004 | T032 (SMD < 0.1) | ✅ |
| SC‑005 | T037 (≥ 80 % subsets significant) | ✅ |
| SC‑006 | T040 (runtime ≤ 6 h) | ✅ |
| SC‑007 | T023b (syntactic validity ≥ 95 %) | ✅ |

---




## projects/PROJ-302-evaluating-the-impact-of-code-generation/specs/001-evaluating-the-impact-of-code-generation/research.md===
# Research: Evaluating the Impact of Code Generation on Code Review Time

## 1. Problem Statement & Hypotheses
- **Primary Hypothesis**: LLM‑generated code (both prompt‑only and context‑based cohorts) is **associated** with longer **review latency** than human‑written code after matching on pre‑treatment confounders.  
- **Null Hypothesis (H₀)**: No association between code origin (LLM vs. human) and review latency after propensity‑score matching.  

**Outcome Metric**: `review_latency = merge_timestamp – created_timestamp` (seconds). This captures the full time from PR opening to merge, a more complete proxy for reviewer effort than the first‑comment timestamp.

## 2. Dataset Strategy
The study uses only **verified open datasets** (see “Verified datasets” block in the spec). No gated or synthetic external sources are required.

| Dataset | Verified URL | What it provides |
|---|---|---|
| PR metadata (including `diff`) | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | Pull‑request IDs, timestamps, file diffs, repo metadata |
| Additional PR samples (author‑merged) | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | Enriches author‑level information |
| PR samples (full merged dataset) | https://huggingface.co/datasets/davanstrien/authors_merged_dataset_prs/resolve/main/data/train-00000-of-00001-d5c709e857d2ca0b.parquet | Larger pool for stratified sampling |
| LOC reference (unused for acquisition) | https://huggingface.co/datasets/LocalLLaMA/typed-decisions/resolve/main/agent_trace_observability/test-00000-of-00001.parquet | Demonstrates that LOC data can be streamed if needed |
| CDF visualisation reference (example) | https://huggingface.co/datasets/autoevaluate/autoeval-staging-eval-project-318525f4-cdf7-4888-965c-d4d9dfeeca48-5250/resolve/main/predictions.parquet | Provides a template for CDF plotting |

**Acquisition Procedure**
1. Stream each parquet file via `datasets.load_dataset(..., streaming=True)` to stay within RAM limits.  
2. Filter for repositories with **≥ 1 000 stars** and **≥ 100 PRs** (derived from the metadata).  
3. Retain only PRs that contain a non‑empty `diff` field (required for context‑based generation).  
4. Perform a **stratified random sample** based on **code complexity** (low/medium/high) and **PR size** (LOC quartiles) to obtain a balanced baseline cohort.

## 3. Methodology & Statistical Plan

### 3.1 Prompt Engineering & Synthetic Cohorts (FR‑002, FR‑008)
- **Prompt‑Only Cohort**: Commit message → intent extraction (simple rule‑based classifier) → natural‑language prompt fed to CodeLlama. No original code is supplied.  
- **Context‑Based Cohort**: Commit message + original `diff` supplied to CodeLlama to simulate “LLM‑assisted refactoring”.  

**Model**: CodeLlama‑7B‑quantized (CPU‑tractable).  
- **CPU‑first** inference; if a single generation exceeds **30 seconds**, the pipeline automatically switches to the Kaggle GPU escape hatch (8‑bit quantized, same model).  
- **Retries**: Up to 3 attempts per snippet; on persistent failure the snippet is dropped and logged.  

**Validity Check**: Parse generated code with Python’s `ast` (or language‑appropriate parser). Record `is_valid_syntax`. Target ≥ 95 % valid snippets (SC‑007).

### 3.2 Feature Extraction (FR‑003, FR‑009)
For every PR (human and synthetic):
- **LOC** via simple line count.  
- **Cyclomatic Complexity** via `radon`.  
- **Semantic Similarity** (optional) using CodeBERT embeddings; cosine similarity to the original human snippet. This metric is **exploratory only** and **not used for matching** (Methodological Override).  

All features stored in `data/processed/features.parquet`.

### 3.3 Pre‑Study Power Analysis (New Task)
Before matching, compute the minimum number of matched pairs needed to detect a medium effect size (Cohen’s d ≈ 0.3) with α = 0.05 and power = 0.8. If the sampled dataset yields fewer pairs, additional repositories are fetched. This ensures the study is adequately powered (addressing methodology‑21acc90a).

### 3.4 Propensity‑Score Matching (FR‑004, FR‑010)
- **Covariates** (pre‑treatment only): `repo_activity_level`, `primary_language`, `commit_message_length`.  
- **Model**: Logistic regression (`sklearn.linear_model.LogisticRegression`).  
- **Matching**: 1‑to‑1 nearest‑neighbor with caliper = 0.05.  
- **Balance Check**: Compute Standardized Mean Difference (SMD) for each covariate.  
  - **Success**: All SMD < 0.1 → `balance_verified = true`.  
  - **Failure**: If any SMD ≥ 0.1, retry up to **3** times with adjusted caliper or covariate weighting. After 3 attempts, abort and emit `matching_failure_report.json`.  

### 3.5 Statistical Testing (FR‑005)
1. **Normality**: Shapiro‑Wilk test on the paired differences of review latency.  
2. **Test Selection**:  
   - If `p_shapiro > 0.05` → paired **t‑test**.  
   - Else → **Mann‑Whitney U**.  
3. **Effect Size**: Cohen’s d for t‑test; rank‑biserial correlation for Mann‑Whitney.  
4. **Significance Threshold**: `α = 0.05` (source: P‑value, https://en.wikipedia.org/wiki/P-value).  
5. **Power Reporting**: Report achieved power; if power < 0.8, note “under‑powered” but still present results.  
6. **Multiple‑Comparison Correction**: Apply Holm‑Bonferroni across the five sensitivity subsets (Section 3.6).  

All results written to `data/reports/statistical_results.json`.

### 3.6 Sensitivity Analysis (FR‑006, SC‑005)
Repeat the full matching + testing pipeline across **five** stratified subsets:
1. **Complexity Low** (bottom [deferred] of complexity).  
2. **Complexity Medium** (40‑[deferred] percentile).  
3. **Complexity High** (top [deferred]).  
4. **PR Size Small** (LOC < 25 th percentile).  
5. **PR Size Large** (LOC > 75 th percentile).  

Report the proportion of subsets where `p < 0.05`. Requirement: ≥ 80 % (SC‑005). Store per‑subset results in `sensitivity_summary.json`.

### 3.7 Visualization (FR‑007)
- **Box Plot**: Review latency for human vs. each LLM cohort (overall).  
- **CDF**: Cumulative distribution of review latency for the same groups.  
- Saved as PNG files in `data/reports/`.

### 3.8 Report Generation (Implicit FR‑010)
Combine tables, balance report, statistical summary, and figures into an HTML and PDF report (`analysis_report.pdf`). The report includes provenance metadata (model version, seed commit IDs, dataset checksums).

## 4. Compute Decision & Feasibility
| Component | Execution Environment | Rationale |
|---|---|---|
| Data download & streaming | CPU (GitHub Actions) | `datasets` streaming avoids RAM blow‑up. |
| Feature extraction (radon, LOC) | CPU | Lightweight per‑file operations. |
| Embedding generation (CodeBERT) | CPU (batch ≤ 200) | Fits within 7 GB RAM; optional. |
| CodeLlama generation | **CPU‑first**; GPU escape if > 30 s | Guarantees completion within the 6 h budget; GPU fallback uses Kaggle free GPU (≤ 9 h wall‑time). |
| Matching & stats | CPU | Scikit‑learn & statsmodels are CPU‑native and fast for ≤ 10 k rows. |
| Visualization | CPU | Matplotlib/Seaborn are lightweight. |

## 5. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| GitHub API / dataset streaming stalls | Tenacity exponential backoff; configurable max retries; checkpointing of downloaded shards. |
| LLM generation exceeds CPU timeout | GPU escape hatch; log “GPU‑Offloaded” flag. |
| Matching fails to achieve balance | Adaptive caliper, covariate weighting, and up‑to‑3 retry policy; abort with clear failure report if still unbalanced. |
| Under‑powered sample | Pre‑study power analysis; if still insufficient, collect more data. |
| Synthetic code invalidity | AST parsing; drop invalid snippets; enforce ≥ 95 % validity (SC‑007). |
| Runtime exceeds 6 h | `utils.timer` records each stage; `runtime_report.json` triggers CI failure if limit breached. |

---



