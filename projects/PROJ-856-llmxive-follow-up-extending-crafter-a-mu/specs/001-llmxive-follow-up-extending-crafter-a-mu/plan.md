# Implementation Plan: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

**Branch**: `001-llmxive-cognitive-load` | **Date**: 2026-10-16 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-cognitive-load/spec.md`

## Summary
The project must (1) curate a reproducible set of a representative sample of failed figure instances (or a synthetic equivalent), (2) provide two editing interfaces (structured harness & chat), (3) instrument automatic millisecond‑precision logging, (4) validate success via **either** an exact vector match **or** a semantic similarity score ≥ 0.95, (5) run a paired Wilcoxon signed‑rank test on “time‑to‑success” and “iteration count”, and (6) generate a final report containing descriptive statistics, confidence intervals, and independent success‑rate breakdowns. All steps are designed to run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `opencv-python==4.9.*` (for image handling), `torchvision==0.18.*` (lightweight visual similarity model, CPU‑only), `fastapi==0.111.*` (interface stubs), `uvicorn==0.30.*` (dev server)  
**Storage**: File‑system under `data/` (raw figures, ground‑truth vectors, logs)  
**Testing**: `pytest==8.2.*` plus contract‑based validation (`jsonschema`)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Library + CLI utilities (data curation, simulation, analysis)  
**Performance Goals**: End‑to‑end pipeline ≤ 6 h wall‑clock on 2 CPU cores, ≤ 7 GB RAM  
**Constraints**: Must obey Constitution Principles I‑VII; all random seeds pinned; no external authentication required.  
**Scale/Scope**: Multiple figure tasks × A sufficient number of simulated participants. ≈ 1 500 logged sessions (synthetic) for pipeline validation; real‑world study later uses same code.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All scripts are deterministic (seed = 42), data fetched from open URLs or generated synthetically, and full command line documented in `quickstart.md`. |
| II. Verified Accuracy | No external citations are introduced beyond the spec; any future citation will be validated by the Reference‑Validator. |
| III. Data Hygiene | Checksums recorded in `data/checksums.txt`; every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Every figure statistic originates from the JSON logs in `data/logs/` and is referenced directly in the report. |
| V. Versioning Discipline | All artifacts are version‑controlled; the plan references content hashes via the CI‑generated `state/projects/...yaml`. |
| VI. Human‑Subject Interaction Logging | Logging schema (`contracts/interaction_log.schema.yaml`) enforces immutable raw logs before aggregation. |
| VII. Ground‑Truth Validation Protocol | Validation step (`run_validation.py`) records **both** exact vector comparison **and** semantic similarity; a trial is marked *success* if **either** criterion passes, satisfying the dual‑check requirement while keeping the metrics independent. |

## Project Structure
### Documentation (this feature)
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

### Source Code (repository root)
```
src/
├── curators/
│   └── curate_failed_figures.py      # downloads / synthesizes 50 figures
├── interfaces/
│   ├── structured_harness.py         # FastAPI endpoint stub
│   └── chat_interface.py             # FastAPI endpoint stub
├── logger/
│   └── interaction_logger.py         # JSON log writer
├── validation/
│   ├── vector_match.py               # exact comparison
│   └── semantic_similarity.py        # lightweight CNN similarity (CPU)
├── analysis/
│   └── wilcoxon_analysis.py          # paired test & CI report generator
├── simulation/
│   └── simulate_participants.py      # synthetic driver
└── utils/
    └── seeds.py                      # central seed management
```

### Tests
```
tests/
├── contract/
│   └── test_contracts.py
└── integration/
    └── test_end_to_end.py
```

## Complexity Tracking
No constitution violations identified; the plan adheres to all non‑negotiable principles.

## Phase‑by‑Phase Task Breakdown (maps to FR/SC)

| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **0 – Setup** | Pin dependencies, create `requirements.txt`, set random seed. | I, II, III, V |
| **1 – Data Curation** | `curate_failed_figures.py` either downloads verified subset (none found → synthetic generation) and injects localized errors; produces `data/figures/` and `data/ground_truth/`. | FR‑001, SC‑004 |
| **2 – Interface Provisioning & Task Randomization** | FastAPI stubs for Structured Harness & Chat Interface; expose `/init_session` (randomized, counterbalanced order). Additionally, per‑session shuffle of the 50 figure tasks to counterbalance fatigue/learning effects. | FR‑002, methodology‑d0e858cf |
| **3 – Logging Instrumentation** | `interaction_logger.py` writes per‑edit JSON entries with millisecond timestamps, iteration count, payload. | FR‑003, VI |
| **4 – Power Analysis (a priori)** | Compute required N for a medium effect (d≈0.5) at α=0.05 using `statsmodels.stats.power.TTestPower`; abort if planned N < required. | methodology‑ef8d85e0 |
| **5 – Success Validation** | Run `vector_match.py` **or** (`semantic_similarity.py` score ≥ 0.95). Record both outcomes in a `SemanticValidation` JSON line (see new contract). A trial is marked *success* if **either** condition passes. | FR‑004, FR‑005, VII, scientific_soundness‑473faa82 |
| **6 – Simulation of Participants** | Synthetic driver (`simulate_participants.py`) iterates over participants, randomizes interface and task order, and generates realistic edit sequences. | SC‑004 (synthetic N = 30) |
| **7 – Retention Check** | After simulation, verify that ≥ 25 of the 30 sessions contain at least one non‑aborted successful trial; if not, raise a warning and halt analysis. | spec_coverage‑e27c0ff2 |
| **8 – Statistical Analysis** | `wilcoxon_analysis.py` reads logs and SemanticValidation records, computes paired differences for `time_to_success` & `iteration_count`, performs Wilcoxon signed‑rank test (no normality check), applies Bonferroni correction for two outcomes, calculates effect size *r* and bootstrap 95 % CI. | FR‑006, SC‑001, SC‑002, SC‑003 |
| **9 – Report Generation** | `generate_report.py` produces `outputs/report.md` with tables, p‑values, effect sizes, confidence intervals, and **independent** success‑rate breakdowns (vector‑match success, semantic‑similarity success). | FR‑007, SC‑005 |
| **10 – Validation & Contracts** | Contract tests ensure logs conform to `interaction_log.schema.yaml`, `semantic_validation.schema.yaml`, and analysis output to `analysis_result.schema.yaml`. | All FR/SC (ensures integrity) |

---

