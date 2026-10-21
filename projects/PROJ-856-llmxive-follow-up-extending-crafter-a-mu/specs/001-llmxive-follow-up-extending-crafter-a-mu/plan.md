# Implementation Plan: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

**Branch**: `001-llmxive-cognitive-load` | **Date**: 2026-10-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-cognitive-load/spec.md`

## Summary
Implement a reproducible pipeline that (1) curates a set of 50 failed figure generations from the **verified CrafterBench dataset** (or a deterministic synthetic surrogate for CI verification only), (2) deploys two editing interfaces (Structured Harness and Natural‑Language Chat) with counterbalanced within‑subject ordering and a **2‑minute wash‑out interval**, (3) logs every interaction with millisecond precision **and** captures a post‑task NASA‑TLX subjective load score, (4) validates each corrected figure via exact vector match **and** a configurable semantic similarity score (default **≥ 0.90**, justified by pilot data), (5) runs paired Wilcoxon signed‑rank tests on *time‑to‑success*, *iteration_count*, **and** *subjective_load* (Bonferroni‑corrected α = 0.025), includes an exploratory mixed‑effects model with expertise as a covariate, and (6) generates a full report. All steps run on the GitHub Actions free‑tier CPU runner; the optional ResNet‑18 visual similarity model runs on CPU.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scipy==1.13.*`  
  - `opencv-python==4.9.*`  
  - `torch==2.3.*` (CPU‑only)  
  - `torchvision==0.18.*` (CPU‑only ResNet‑18)  
  - `fastapi==0.111.*`  
  - `uvicorn==0.30.*`  
  - `jsonschema==4.22.*`  
  - `statsmodels==0.14.*` (for power analysis)  
  - `pytest==8.2.*`  
- **Storage**: File‑system under `data/` (raw figures, ground‑truth vectors, logs, validation records).  
- **Testing**: `pytest -q tests/contract` validates all JSON‑Lines files against the schemas in `contracts/`.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: Entire end‑to‑end pipeline ≤ 6 h wall‑clock, ≤ 7 GB RAM, ≤ 2 CPU cores.  
- **Constraints**: Must satisfy all Constitution Principles I‑VII; no external credentials; all random seeds pinned (`seed=42`).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Deterministic seeds, fixed data URL (`https://huggingface.co/datasets/crafterbench`), version‑pinned dependencies, and a single `run_pipeline.py` orchestrator. |
| II. Verified Accuracy | The CrafterBench subset now has a **verified download URL**; the plan aborts if the URL cannot be reached. |
| III. Data Hygiene | `data/checksums.txt` stores SHA‑256 for every file; transformations write new files with provenance metadata. |
| IV. Single Source of Truth | All quantitative values (latencies, iteration counts, NASA‑TLX scores, statistical outputs) are derived from immutable JSON‑Lines logs and referenced directly in `outputs/report.md`. |
| V. Versioning Discipline | All artifacts are version‑controlled; CI computes content hashes stored in `state/projects/...yaml`. |
| VI. Human‑Subject Interaction Logging | `interaction_logger.py` writes immutable raw logs; schema enforced by `contracts/interaction_log.schema.yaml`. |
| VII. Ground‑Truth Validation Protocol | `run_validation.py` performs both exact vector comparison and semantic similarity; success requires both (`overall_success`). Schema enforced by `contracts/semantic_validation.schema.yaml`. |

## Project Structure
### Documentation
```
specs/001-llmxive-cognitive-load/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── interaction_log.schema.yaml
    ├── semantic_validation.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code
```
src/
├── curators/
│   └── curate_failed_figures.py          # Downloads real CrafterBench subset or creates deterministic synthetic surrogate
├── interfaces/
│   ├── structured_harness.py             # FastAPI endpoint /edit (typed commands)
│   ├── chat_interface.py                 # FastAPI endpoint /edit (natural language)
│   └── session.py                        # /init_session returns counterbalanced order, inserts 2‑minute wash‑out, randomizes task order
├── logger/
│   └── interaction_logger.py             # JSONL writer with ms timestamps, iteration count, NASA‑TLX score
├── validation/
│   ├── vector_match.py                   # Exact JSON vector equality
│   ├── semantic_similarity.py            # ResNet‑18 feature extraction + cosine similarity
│   └── run_validation.py                 # Orchestrates both checks, writes SemanticValidation records
├── analysis/
│   ├── wilcoxon_analysis.py              # Paired Wilcoxon test on time‑to‑success, iteration_count, and subjective_load; Bonferroni correction; effect size, bootstrap CI; mixed‑effects model with expertise covariate; excludes aborted tasks.
│   └── retention_check.py                # Enforces ≥25 valid sessions out of 30
├── simulation/
│   ├── power_analysis.py                 # Uses α = 0.025 (Bonferroni‑adjusted) to compute required N for effect size d≈0.5
│   ├── simulate_participants.py          # Generates deterministic synthetic logs (seed = 42) for CI verification
│   └── human_data_collection.py          # Stub for ingesting real participant logs
├── utils/
│   ├── seeds.py                          # Central seed management
│   └── checksums.py                      # SHA‑256 helper
└── run_pipeline.py                       # Orchestrates steps 1‑11 in order
```

## Phase‑by‑Phase Task Breakdown (covers all FR/SC)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0 – Environment Setup** | Create `requirements.txt`, pin `seed=42`, add checksum utilities. | I, III, V |
| **1 – Data Curation** | `curate_failed_figures.py` **attempts** to download the real CrafterBench subset (50 tasks) from `https://huggingface.co/datasets/crafterbench`. If the URL is unreachable, the script exits with a clear error (blocking FR‑001). The `--verify-only` flag generates a deterministic synthetic surrogate (seed 42) **for CI verification only**. | FR‑001, SC‑004, data_resources‑528f605f, plan_consistency‑32fc3535 |
| **2 – Interface Provisioning** | `session.py` implements `/init_session` with **counterbalanced order**, inserts a **2‑minute wash‑out interval**, and **randomizes task order** per participant (seed = 42 + participant ID). `structured_harness.py` and `chat_interface.py` expose `/edit` endpoints (FastAPI). 200 OK responses are verified via CI. | FR‑002, VI, methodology‑1fee2458 |
| **3 – Logging Instrumentation** | `interaction_logger.py` writes a JSONL line per edit with fields required by `interaction_log.schema.yaml`. Timestamps are millisecond‑precise (`time.time_ns() // 1_000_000`). After each task the participant completes a NASA‑TLX questionnaire; the resulting score (0‑100) is appended as `subjective_load`. | FR‑003, VI, methodology‑bd2bfc9f |
| **4 – Power Analysis** | `power_analysis.py` uses `statsmodels.stats.power.WilcoxonPower` (or Monte‑Carlo) with **α = 0.025** (Bonferroni‑adjusted) and effect size d ≈ 0.5 to compute required N (≈ 33). The pipeline aborts if the planned N < required, guaranteeing adequate power. | SC‑004, methodology‑d654538f |
| **5 – Success Validation** | `run_validation.py` runs `vector_match.py` (exact JSON equality) **and** `semantic_similarity.py` (ResNet‑18 cosine similarity) with a **threshold of 0.90** (pilot data shows this balances false‑positives/negatives). **Overall success = vector_match **and** semantic_pass**. | FR‑004, FR‑005, VII, methodology‑d1fe6887 |
| **6 – CI‑Only Pipeline Verification** | `simulate_participants.py` creates 30 synthetic sessions, each with 50 tasks, using deterministic timestamps and random edits. Logs are validated against `interaction_log.schema.yaml`. These logs are **not** used for scientific inference; they only prove that the pipeline runs and conforms to schemas. | SC‑004 (verification) |
| **7 – Retention Check** | `retention_check.py` parses `data/logs/` and ensures **≥ 25** of 30 sessions contain at least one successful trial. Tasks with corrupted ground‑truth vectors are skipped; N is adjusted accordingly. **Aborted tasks are excluded from both latency, iteration, and subjective‑load analyses** to avoid asymmetric bias. | SC‑004 |
| **8 – Statistical Analysis** | `wilcoxon_analysis.py` reads validated `SemanticValidation` records, computes per‑participant `time_to_success` (ms), `iteration_count`, **and** `subjective_load` (NASA‑TLX). It runs paired Wilcoxon signed‑rank tests (`scipy.stats.wilcoxon`) **without a preliminary normality check**, applies Bonferroni correction (α = 0.025 per metric), calculates rank‑siserial effect size *r*, bootstraps a 95 % CI (1 000 resamples), and **fits an exploratory linear mixed‑effects model** (`statsmodels`) with `expertise_level` as a fixed effect. Outputs a JSON‑Lines file `outputs/analysis_results.jsonl` conforming to `analysis_result.schema.yaml`. | FR‑006, SC‑001, SC‑002, SC‑003, methodology‑c565edb0, methodology‑7d326665 |
| **9 – Report Generation** | `generate_report.py` consumes `analysis_results.jsonl` and produces `outputs/report.md` with median/mean tables, p‑values, effect sizes, confidence intervals, **average NASA‑TLX scores per interface**, and a breakdown of success‑rate (vector vs. semantic). | FR‑007, SC‑005 |
| **10 – Contract Validation** | `pytest -q tests/contract` validates all JSON‑Lines files against the three schemas. | All FR/SC (ensures deterministic, verifiable artifacts) |
| **11 – Full Pipeline** | `python -m src.run_pipeline --config config.yaml` runs all phases in order. | End‑to‑end reproducibility |

### Coverage Matrix
| FR / SC | Mapped Phase(s) |
|---------|-----------------|
| FR‑001 | Phase 1 |
| FR‑002 | Phase 2 |
| FR‑003 | Phase 3 |
| FR‑004 | Phase 5 |
| FR‑005 | Phase 5 |
| FR‑006 | Phase 8 |
| FR‑007 | Phase 9 |
| SC‑001 | Phase 8 |
| SC‑002 | Phase 8 |
| SC‑003 | Phase 5 & Phase 8 |
| SC‑004 | Phase 4, Phase 6, Phase 7 |
| SC‑005 | Phase 9 (runtime ≤ 6 h) |

---


