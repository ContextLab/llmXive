# Implementation Plan: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Branch**: `001-gatekeeper-governance` | **Date**: 2026-10-22 | **Spec**: `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`

## Summary
Implement a **CPU‑tractable Gatekeeper** pipeline (frozen DistilBERT intent classifier + regex rule engine) and compare it against the **Retrieval‑only** and **Long‑Context** baselines on the open‑source GateMem dataset. Compute the three core GateMem metrics (Utility, Access Control, Forgetting), profile wall‑clock time and peak RAM, and perform a **Generalized Linear Mixed‑Effects Model (GLMM)** analysis with Holm‑Bonferroni correction across the six hypothesis tests (three metrics × two baseline comparisons). All steps run reproducibly on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.2`, `datasets==2.20.0`, `pandas`, `statsmodels`, `scipy`, `psutil`, `pyyaml`  
- **LLM Backbone**: `EleutherAI/pythia-410m` (CPU‑only, ~410 M parameters) – meets the free‑tier compute budget.  
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
│   ├── evaluation_result.schema.yaml
│   ├── metrics.schema.yaml
│   └── results.schema.yaml
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
│   ├── glmm.py                # GLMM fitting (logistic & Gaussian)
│   └── comparison.py          # Wrapper, assumption checks, fallback tests
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

data/
├── raw/
├── processed/
└── samples/
```

## Complexity Tracking
| Issue | Resolution |
|---|---|
| FR‑001 template residue (outcome/predictors/covariates) | Revised FR‑001 wording to require only the fields actually present in GateMem (see Mapping table). |
| Baseline asymmetry | All three core metrics (Access Control, Utility, Forgetting) are computed for **Gatekeeper**, **Retrieval‑only**, and **Long‑Context** configurations, ensuring symmetric comparison. |
| GLMM convergence risk | Automatic fallback to paired tests (McNemar, paired t‑test/Wilcoxon) if model fails to converge or assumptions are violated. |
| Model download corruption | Data‑loader retries DistilBERT download once; second failure aborts with error code 1 and logs “Critical: Model Unavailable”. |
| Ambiguous `leak_target` | Logged as “validation error” and excluded from metric calculations (per US‑1 edge case). |

## Phased Implementation

### Phase 0 – Research & Design (Current)
- T001: Literature review on modular governance.  
- T002: Finalise metric definitions, statistical plan (GLMM primary, domain‑stratified fallback).  
- T003: Confirm open‑source GateMem URLs and model IDs (DistilBERT‑SST‑2).  

### Phase 1 – Data & Contracts
- **T004**: Publish YAML contracts (`gatemem_episode.schema.yaml`, `evaluation_result.schema.yaml`, `metrics.schema.yaml`, `results.schema.yaml`).  
- **T006** (`utils/data_loader.py`):  
  1. Stream GateMem JSONL from the verified HF repo (`datasets.load_dataset(..., streaming=True)`).  
  2. Validate each record against `gatemem_episode.schema.yaml`.  
  3. Compute SHA‑256 checksums; record in `state/artifact_hashes.yaml`.  
  4. Abort with exit 1 on any validation failure (fulfills FR‑001).  
- **T006d‑1**: Variable presence check – explicit dependency on T004.  

### Phase 2 – Core Components
- **T014a** (`gatekeeper/classifier.py`): Load frozen `distilbert-base-uncased-finetuned-sst-2-english` via `transformers`. Map the four sentiment labels to the intent taxonomy (`query`, `deletion`, `extraction`, `other`).  
- **T015a** (`gatekeeper/rules.py`): Regex engine enforces role‑based access and parses `deletion_log`.  
- **T017a** (`baselines/retrieval.py`): Retrieval‑only pipeline using the same LLM backbone.  
- **T017b** (`baselines/long_context.py`): Long‑Context pipeline (single implementation).  

### Phase 3 – Integration & Metric Calculation
- **T016** (`gatekeeper/pipeline.py`): Orchestrates classifier → rule engine → LLM call (if allowed).  
- **T018**, **T023**, **T024** (`metrics/*`): Compute per‑episode Access Control, Utility, Forgetting; write `EvaluationResult` objects (`evaluation_result.schema.yaml`) and aggregated `unified_metrics.json`.  
- **T007** (`utils/profiling.py`): Record `latency_ms` and `peak_ram_mb` for each pipeline run.  

### Phase 4 – Statistical Analysis & Reporting
- **T008a** (`stats/glmm.py`): Fit GLMMs  
  - Binary outcomes → logistic link.  
  - Utility → Gaussian link.  
  - Model: `score ~ method + domain` (domain as fixed effect).  
  - Assumption checks: Shapiro‑Wilk (Utility), Hosmer‑Lemeshow (logistic).  
  - Multiple‑comparison correction: **Holm‑Bonferroni** across six tests (α = 0.0083).  
  - Power assessment: ≥ 200 episodes per domain gives ≈ 0.85 power for Cohen’s h = 0.3; GateMem provides > 500 per domain.  
- **T026a** (`stats/comparison.py`): Wrapper that runs T008a, applies fallback tests if needed, and writes `results.schema.yaml` with p‑values, confidence intervals, effect sizes.  

### Phase 5 – End‑to‑End Execution & Validation
- **T019** (`cli/run_evaluation.py`):  
  1. Run Gatekeeper, Retrieval‑only, Long‑Context pipelines across all four domains.  
  2. Profile, aggregate metrics, perform statistical comparison, and generate a stratified sample of failure cases (fixed seed 42, stratified by domain if N > 50).  
  3. Output all artifacts under `data/processed/` and `data/samples/`.  
- **T030**: Execute full test suite (`pytest -q`) including contract validation.  

## Mapping of Functional Requirements & Success Criteria
| FR | Covered By | Notes |
|---|---|---|
| FR‑001 | T006 (download & parse) | Validates presence of **all** required fields; no outcome/predictor/covariate leftovers. |
| FR‑002 | T014a + T015a (CPU‑tractable) | Uses frozen DistilBERT and regex engine. |
| FR‑003 | T016, T017a, T017b (identical prompts, seed 42) | Guarantees fair comparison. |
| FR‑004 | T018, T023, T024 (metric modules) | Computes Utility, Access Control, Forgetting. |
| FR‑005 | T008a (GLMM) + fallback logic | Logistic for binary, Gaussian for Utility; Holm‑Bonferroni across six tests. |
| FR‑006 | T007 (profiling) | Captures latency & RAM for all pipelines. |
| FR‑007 | T019 (stratified sampling) | Fixed seed, domain‑stratified if > 50 cases. |
| SC‑001 | T018 (Access Control) | Reported for Gatekeeper, Retrieval‑only, Long‑Context. |
| SC‑002 | T023 (Utility) | Reported for all three configurations. |
| SC‑003 | T007 (Computational overhead) | Direct latency & RAM comparison. |
| SC‑004 | T008a (GLMM) | Provides statistical significance with correction. |
| SC‑005 | T024 (Forgetting) | Reported for all configurations. |

All FRs and SCs are explicitly addressed.

---
