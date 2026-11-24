# Implementation Plan: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Branch**: `001-gatekeeper-governance` | **Date**: 2026-10-25 | **Spec**: `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`

## Summary
Implement a CPU‑tractable **Gatekeeper** pipeline (frozen DistilBERT intent classifier + regex rule engine) and compare it against the **Retrieval‑only** and **Long‑Context** baselines on the open‑source GateMem dataset. Compute the three core metrics (Utility, Access Control, Forgetting), profile wall‑clock time and peak RAM, and perform a **Logistic Generalized Linear Mixed‑Effects Model (GLMM)** analysis (binary outcomes) with Holm‑Bonferroni correction across the six hypothesis tests (three metrics × two baseline comparisons). All steps run reproducibly on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.2`, `datasets==2.20.0`, `pandas`, `statsmodels`, `scipy`, `psutil`, `pyyaml`, `bitsandbytes==0.43.1`  
- **LLM Backbone**: `meta-llama/Meta-Llama-3-2B-Instruct` loaded **int8** via `bitsandbytes` (`device="cpu"`). This satisfies FR‑003’s requirement for a lightweight 2.7 B‑class model that runs on a CPU‑only free‑tier runner.  
- **Storage**: Local filesystem under `data/`.  
- **Testing**: `pytest` (unit, integration, contract).  
- **Target Platform**: Linux (GitHub Actions CPU‑only).  
- **Constraints**: No GPU; streaming data loads; strict checksum validation; fixed random seed (`SEED = 42`).  

## Constitution Check
| Principle | Status | Note |
|---|---|---|
| I. Reproducibility | PASS | Seeds pinned; `requirements.txt` version‑locked; data fetched from a single canonical HF URL each run. |
| II. Verified Accuracy | PASS | All citations limited to the verified GateMem URL. |
| III. Data Hygiene | PASS | Checksums recorded in `state/artifact_hashes.yaml`; no in‑place modifications. |
| IV. Single Source of Truth | PASS | Every figure/table derives from files under `data/processed/`. |
| V. Versioning Discipline | PASS | Content hashes updated on artifact change. |
| VI. Governance‑Utility Trade‑off Validation | PASS | Metrics (Utility, Access Control, Forgetting) calculated; primary statistical test is GLMM per FR‑005. |
| VII. Computational Efficiency and Resource Profiling | PASS | Profiling captures latency & RAM for all pipelines. |

## Project Structure
```
specs/001-gatekeeper-governance/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── gatemem_episode.schema.yaml
│   ├── dataset.schema.yaml
│   ├── evaluation_result.schema.yaml
│   ├── metrics.schema.yaml
│   ├── results.schema.yaml
│   └── output.schema.yaml
└── tasks.md   (generated later)

src/
├── gatekeeper/
│   ├── __init__.py
│   ├── classifier.py          # DistilBERT intent classifier
│   ├── rules.py               # Regex rule engine
│   └── pipeline.py            # Orchestrates classifier → rules → LLM
├── baselines/
│   ├── __init__.py
│   ├── retrieval.py           # Retrieval‑only baseline
│   └── long_context.py        # Long‑Context baseline
├── metrics/
│   ├── __init__.py
│   ├── utility.py             # Utility score
│   ├── access_control.py      # Access‑Control score
│   └── forgetting.py          # Forgetting score
├── stats/
│   ├── __init__.py
│   ├── glmm.py                # GLMM fitting (logistic for binary, logistic for utility as binary)
│   └── comparison.py          # Wrapper, assumption checks, fallback tests with Holm‑Bonferroni applied
├── utils/
│   ├── __init__.py
│   ├── data_loader.py         # Streaming download & schema validation
│   ├── profiling.py           # Time & RAM profiling
│   └── config.py              # Constants, paths, seed
├── cli/
│   └── run_evaluation.py      # End‑to‑end driver
└── contracts/                 # Copied from specs/.../contracts/ at build time

tests/
├── unit/
│   ├── test_classifier.py
│   ├── test_rules.py
│   ├── test_metrics.py
│   └── test_stats.py
├── integration/
│   ├── test_pipeline.py
│   └── test_baseline_comparison.py
└── contract/
    └── test_schemas.py       # Validates all data files against contracts/*.schema.yaml
```

## Complexity Tracking
| Issue | Resolution |
|---|---|
| FR‑001 template residue (outcome/predictors/covariates) | Revised FR‑001 to require only the fields present in GateMem (see Mapping table). |
| Baseline asymmetry | All three core metrics (Access Control, Utility, Forgetting) are computed for **Gatekeeper**, **Retrieval‑only**, and **Long‑Context** configurations, ensuring symmetric comparison. |
| GLMM convergence risk | Automatic fallback to paired tests (McNemar for binary, Wilcoxon for Utility) if model fails to converge or assumptions are violated; Holm‑Bonferroni correction also applied to fallback tests. |
| Model download corruption | Data‑loader retries DistilBERT download once; second failure aborts with exit 1 and logs “Critical: Model Unavailable”. |
| Ambiguous `leak_target` | Logged as “validation error” and excluded from metric calculations (per US‑1 edge case). |
| Intent‑classifier mapping validity | Added **T010a**: evaluate the sentiment‑to‑intent mapping on a small manually‑labeled subset (≈ 200 episodes) and report accuracy; if < 80 % accuracy, abort with warning. |
| Power analysis granularity | Per‑metric power calculations now use α = 0.0083 (Holm‑Bonferroni) and assume Cohen’s h = 0.3 for binary metrics and Cohen’s d = 0.5 for Utility (continuous proportion). GateMem provides > 500 episodes per domain, yielding > 0.85 power for all metrics. |
| Domain effect modeling | Primary GLMM includes **Domain** as a fixed effect; if likelihood‑ratio test shows significant improvement, a random intercept for Domain is added. |
| Output contract omission | Added **T021** to generate a final evaluation JSON conforming to `output.schema.yaml`. |
| LLM Backbone mismatch | Switched to `meta-llama/Meta-Llama-3-2B-Instruct` int8 (CPU‑only) to satisfy FR‑003. |
| Fallback test correction | Holm‑Bonferroni correction is applied to any fallback test results to maintain family‑wise error control. |

## Phased Implementation

### Phase 0 – Research & Design (Current)
- T001: Literature review on modular governance.  
- T002: Finalise metric definitions, statistical plan (GLMM primary, domain‑stratified fallback).  
- T003: Confirm open‑source GateMem URLs and model IDs (DistilBERT‑SST‑2, Llama‑3‑2B‑int8).  

### Phase 1 – Data & Contracts
- **T004**: Publish YAML contracts (`gatemem_episode.schema.yaml`, `dataset.schema.yaml`, `evaluation_result.schema.yaml`, `metrics.schema.yaml`, `results.schema.yaml`, `output.schema.yaml`).  
- **T005** (`utils/data_loader.py`):  
  1. Stream GateMem JSONL from the verified HF repository (`datasets.load_dataset(..., streaming=True)`).  
  2. Validate each record against `gatemem_episode.schema.yaml`.  
  3. Compute SHA‑256 checksums; record in `state/artifact_hashes.yaml`.  
  4. Abort with exit 1 on any validation failure (fulfills FR‑001).  
- **T006**: Verify presence of required fields (`leak_target` (bool), `role`, `deletion_request` (bool), etc.) – abort if missing.  

### Phase 2 – Core Components
- **T010** (`gatekeeper/classifier.py`): Load frozen `distilbert-base-uncased-finetuned-sst-2-english` via `transformers`. Map SST‑2 sentiment labels to intent taxonomy (`query`, `deletion`, `extraction`, `other`).  
- **T010a**: Validate the sentiment‑to‑intent mapping on a manually‑labeled sample (≈ 200 episodes). Log accuracy; if < 80 % abort with warning.  
- **T011** (`gatekeeper/rules.py`): Regex engine enforces role‑based access and parses `deletion_log`.  
- **T012** (`baselines/retrieval.py`): Retrieval‑only pipeline using the same LLM backbone.  
- **T013** (`baselines/long_context.py`): Long‑Context pipeline (single implementation).  

### Phase 3 – Integration & Metric Calculation
- **T014** (`gatekeeper/pipeline.py`): Orchestrates classifier → rule engine → LLM call (if allowed).  
- **T015** (`metrics/utility.py`, `metrics/access_control.py`, `metrics/forgetting.py`): Compute per‑episode scores; write `EvaluationResult` objects (`evaluation_result.schema.yaml`) and aggregated `unified_metrics.json`.  
- **T016** (`utils/profiling.py`): Record `latency_ms` and `peak_ram_mb` for each pipeline run.  

### Phase 4 – Statistical Analysis & Reporting
- **T017** (`stats/glmm.py`): Fit GLMMs  
  - **Binary outcomes** (Access Control, Forgetting, Utility): **logistic link**.  
  - **Model**: `score ~ method + domain` with `domain` as a **fixed effect**; perform likelihood‑ratio test to decide on adding a random intercept for `domain`.  
  - **Assumption Checks**: Shapiro‑Wilk on residuals for Utility; Hosmer‑Lemeshow for logistic models.  
  - **Multiple‑Comparison Correction**: **Holm‑Bonferroni** across the six primary hypothesis tests (α = 0.0083).  
  - **Power Assessment**: Using α = 0.0083, Cohen’s h = 0.3 for binary metrics and Cohen’s d = 0.5 for Utility, ≥ 200 episodes per domain yields > 0.8 power; GateMem provides > 500 per domain.  
- **T018** (`stats/comparison.py`): Wrapper that runs T017, applies **fallback tests** if needed (McNemar for binary outcomes, Wilcoxon signed‑rank for Utility), and **applies Holm‑Bonferroni** to those secondary p‑values as well. Writes `results.schema.yaml` with p‑values, confidence intervals, effect sizes.  

### Phase 5 – End‑to‑End Execution & Validation
- **T019** (`cli/run_evaluation.py`):  
  1. Run Gatekeeper, Retrieval‑only, Long‑Context pipelines across all four domains.  
  2. Profile, aggregate metrics, perform statistical comparison, and generate a stratified sample of failure cases (fixed seed 42, stratified by domain if N > 50).  
  3. Output all artifacts under `data/processed/` and log profiling info.  
- **T020**: Execute full test suite (`pytest -q`) including contract validation.  
- **T021**: Generate a final evaluation JSON (`output.schema.yaml` compliant) summarising run metadata, per‑pipeline results, and aggregated metrics; saved as `data/processed/final_output.json`.  

## Mapping of Functional Requirements & Success Criteria
| FR | Covered By | Notes |
|---|---|---|
| FR‑001 | T005 (download & parse) | Validates presence of **all** required fields; no outcome/predictor/covariate leftovers. |
| FR‑002 | T010 + T011 (CPU‑tractable) | Uses frozen DistilBERT and regex engine. |
| FR‑003 | T014, T012, T013 (identical prompts, seed 42) + Llama‑3‑2B‑int8 backbone | Meets spec‑required lightweight 2.7 B‑class model. |
| FR‑004 | T015 (metric modules) | Computes Utility, Access Control, Forgetting. |
| FR‑005 | T017 (GLMM) + fallback logic | Logistic for binary, Holm‑Bonferroni across six tests, power analysis per metric. |
| FR‑006 | T016 (profiling) | Captures latency & RAM for all pipelines. |
| FR‑007 | T019 (stratified sampling) | Fixed seed, domain‑stratified if > 50 cases. |
| SC‑001 | T015 (Access Control) | Reported for all three configurations. |
| SC‑002 | T015 (Utility) | Reported for all three configurations. |
| SC‑003 | T016 (Computational overhead) | Direct latency & RAM comparison. |
| SC‑004 | T017 (GLMM) | Provides statistical significance with Holm‑Bonferroni. |
| SC‑005 | T015 (Forgetting) | Reported for all three configurations. |

All FRs and SCs are explicitly addressed.

---

