# Implementation Plan: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Branch**: `001-gatekeeper-governance` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`

## Summary
Implement a **CPU‑tractable Gatekeeper** pipeline (frozen DistilBERT intent classifier + regex rule engine) and compare it against the **Retrieval‑only** and **Long‑Context** baselines on the open‑source GateMem dataset. Compute the three core GateMem metrics (Utility, Access Control, Forgetting), profile wall‑clock time and peak RAM, and perform a **Generalized Linear Mixed‑Effects Model (GLMM)** analysis (logistic link for binary outcomes, Gaussian link for Utility) with **domain treated as a fixed effect**. All steps are reproducible on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.2` (DistilBERT), `datasets==2.20.0`, `pandas`, `statsmodels`, `scipy`, `psutil`, `pyyaml`  
- **LLM Backbone**: `EleutherAI/pythia-410m` (CPU‑only, ~410 M parameters) – satisfies free‑tier compute constraints.  
- **Storage**: Local filesystem (`data/` for raw/processed files)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: Linux (GitHub Actions CPU‑only)  
- **Constraints**: No GPU; streaming data loads; strict checksum validation; fixed random seed (`SEED = 42`).  

## Constitution Check
| Principle | Status | Note |
|---|---|---|
| I. Reproducibility | PASS | Seeds pinned; `requirements.txt` version‑locked; data fetched from canonical HF URL each run. |
| II. Verified Accuracy | PASS | All citations limited to verified URLs (GateMem JSONL). |
| III. Data Hygiene | PASS | Checksums recorded in `state/artifact_hashes.yaml`; no in‑place modifications. |
| IV. Single Source of Truth | PASS | Every figure/table derived from files under `data/processed/`. |
| V. Versioning Discipline | PASS | Content hashes updated on artifact change. |
| VI. Governance‑Utility Trade‑off | PASS | Metrics (Utility, Access Control, Forgetting) calculated; primary statistical test is **GLMM** per FR‑005. |
| VII. Computational Efficiency | PASS | Profiling tasks capture latency & RAM for all pipelines. |

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
│   ├── classifier.py          # T014a – DistilBERT intent classifier
│   ├── rules.py               # T015a – Regex rule engine
│   └── pipeline.py            # T016  – Gatekeeper orchestration
├── baselines/
│   ├── __init__.py
│   ├── retrieval.py           # T017a – Retrieval‑only baseline
│   └── long_context.py        # T017b – Long‑Context baseline (single implementation)
├── metrics/
│   ├── __init__.py
│   ├── utility.py             # T023 – Utility score
│   ├── access_control.py      # T018 – Access‑Control score
│   └── forgetting.py          # T024 – Forgetting score
├── stats/
│   ├── __init__.py
│   ├── glmm.py                 # T008a – Generalized Linear Mixed‑Effects Model (logistic for binary, Gaussian for Utility)
│   └── comparison.py          # T026a – Wrapper that calls T008a; fallback domain‑stratified analysis
├── utils/
│   ├── __init__.py
│   ├── data_loader.py         # T006 – Streaming download & schema validation (depends on T004)
│   ├── profiling.py           # T007 – Time & RAM profiling
│   └── config.py              # Seeds, paths, constants
├── cli/
│   └── run_evaluation.py      # T019 – Main entry point (Gatekeeper + Baselines)
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

## Complexity Tracking (resolved concerns)

| Issue | Resolution |
|---|---|
| Duplicate episode‑pairing logic (T008f vs. T026a‑1) | **Removed T008f**. Pairing is performed exclusively inside **T026a‑1** (`stats/comparison.py`). `stats/glmm.py` receives the paired DataFrame directly. |
| Two Long‑Context baseline tasks (T017b & T017c) | **Removed T017c**. **T017b** is the sole implementation; referenced by both US‑1 and US‑2. |
| Missing dependency for schema validation (T006d‑1) | Added explicit dependency on **T004** (contract definition). |
| Domain missing in unified metrics (affects T029a) | Updated **T023** to output per‑episode records that include the `domain` field; the aggregated `unified_metrics.json` now contains a list of objects each with `domain` and all three scores. |
| Repeated Long‑Context duplication (listed twice) | Consolidated to single task **T017b** as above. |

## Phased Implementation

### Phase 0 – Research & Design (Current)
- T001: Literature review on modular governance.
- T002: Finalise metric definitions, statistical plan (GLMM primary, domain‑stratified fallback).
- T003: Confirm open‑source GateMem URLs and model IDs (DistilBERT‑SST‑2).

### Phase 1 – Data & Contracts
- **T004**: Publish YAML contracts (`gatemem_episode.schema.yaml`, `evaluation_result.schema.yaml`, `metrics.schema.yaml`, `results.schema.yaml`).
- **T006** (data_loader.py):  
  - Stream GateMem JSONL from the verified URL.  
  - Validate each record against `gatemem_episode.schema.yaml`.  
  - Compute SHA‑256 checksum; write to `state/artifact_hashes.yaml`.  
  - **Dependency**: T004 (contracts).  
- **T006d‑1** (Variable Presence Check): Explicitly depends on T004.

### Phase 2 – Core Components
- **T014a** (`gatekeeper/classifier.py`): Load `distilbert-base-uncased-finetuned-sst-2-english` (CPU‑only, frozen) via HuggingFace `transformers`. Map the four sentiment labels to our intent taxonomy (`query`, `deletion`, `extraction`, `other`).  
- **T015a** (`gatekeeper/rules.py`): Regex checks enforce role‑based access policies and parse `deletion_log`.  
- **T017a** (`baselines/retrieval.py`): Retrieval‑only pipeline using the same LLM backbone (`EleutherAI/pythia-410m`).  
- **T017b** (`baselines/long_context.py`): Long‑Context pipeline (single implementation) using the same LLM backbone.

### Phase 3 – Integration & Metric Calculation
- **T016** (`gatekeeper/pipeline.py`): Orchestrates classifier → rule engine → LLM call (if allowed).  
- **T018**, **T023**, **T024** (`metrics/*`): Compute Access Control, Utility, Forgetting per episode; write per‑episode results (`evaluation_result.schema.yaml`) and aggregated `unified_metrics.json` (includes `episode_id`, `domain`, and the three core scores).  
- **T007** (`utils/profiling.py`): Record `latency_ms` and `peak_ram_mb` for each pipeline run.  

#### Metrics (Revised Definitions)
| Metric | Numerator | Denominator | Interpretation |
|---|---|---|---|
| **Access Control** | Unauthorized exposures (ground‑truth `leak_target=False` *and* pipeline allowed) | **Total queries** (all episodes) | Proportion of leaks that should have been blocked but were not. |
| **Utility** | Successful task completions (ground‑truth `ground_truth_success=True` *and* pipeline succeeded) | Total valid queries (`ground_truth_success=True`) | Task success rate. |
| **Conditional Utility** | Successful completions among queries allowed by the gate | Queries allowed by the gate | Utility conditional on passing the gate. |
| **Forgetting** | Deletion requests correctly suppressed (`ground_truth_deletion=True` *and* pipeline blocked) | Total deletion requests (`ground_truth_deletion=True`) | Deletion compliance rate. |

### Phase 4 – Statistical Analysis & Reporting
- **T008a** (`stats/glmm.py`): Fit **Generalized Linear Mixed‑Effects Models (GLMM)**  
  - **Binary outcomes** (Access Control, Forgetting): **logistic link**.  
  - **Continuous outcome** (Utility): **Gaussian link**.  
  - **Model**: `score ~ method + domain` where `domain` is treated as a **fixed effect** (four levels).  
  - **Assumption Checks**: Shapiro‑Wilk on residuals for Utility (`α=0.05`); Hosmer‑Lemeshow for logistic models.  
  - **Multiple‑Comparison Correction**: Benjamini‑Hochberg applied across **six** hypothesis tests (three metrics × two baseline comparisons).  
  - **Power Assessment**: Assuming a modest effect size (Cohen’s d ≈ 0.3), α = 0.05, two‑tailed test, **≈ 200 episodes per domain** give ≈0.85 power; GateMem provides >500 episodes per domain, so power is adequate. If computed power falls below 0.8, results will be labelled exploratory.  
- **T026a** (`stats/comparison.py`): Wrapper that invokes T008a, handles fallback (McNemar for Access Control, paired t‑test or Wilcoxon for Utility, logistic fallback for Forgetting), and writes `results.schema.yaml` with p‑values, confidence intervals, and effect sizes.  

### Phase 5 – End‑to‑End Execution & Validation
- **T019** (`cli/run_evaluation.py`): End‑to‑end driver that runs Gatekeeper, both baselines, profiling, metric aggregation, statistical comparison, and failure‑case sampling.  
- **T030**: Execute full test suite (`pytest`) including contract validation.  

## Mapping of Functional Requirements & Success Criteria
| FR | Covered By | Notes |
|---|---|---|
| FR‑001 | T006 (download & parse) | Variable presence check enforced. |
| FR‑002 | T014a + T015a (CPU‑tractable) | Uses frozen DistilBERT model. |
| FR‑003 | T016, T017a, T017b (identical prompts, seeds) | Random seed `SEED=42` ensures fairness. |
| FR‑004 | T018, T023, T024 (metric modules) | All three core metrics computed. |
| FR‑005 | T008a (GLMM) + fallback logic | Logistic GLMM for binary, domain as fixed effect, multiple‑test correction. |
| FR‑006 | T007 (profiling) | Wall‑clock & RAM recorded for all pipelines. |
| FR‑007 | T029a (stratified sampling) | Fixed seed, stratified by domain if N>50. |
| SC‑001 | T018 (Access Control) | Compared to Retrieval‑only baseline. |
| SC‑002 | T023 (Utility) | Compared to Long‑Context baseline. |
| SC‑003 | T007 (Computational overhead) | Direct comparison of latency & RAM. |
| SC‑004 | T008a (GLMM) | Provides statistical significance. |
| SC‑005 | T024 (Forgetting) | Compared to both baselines. |

All FRs and SCs are explicitly addressed.  
