# Implementation Plan: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

**Branch**: `001-llmxive-cognitive-load` | **Date**: 2026-10-17 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-cognitive-load/spec.md`

## Summary
The study compares a structured typed-edit harness against a natural-language chat interface to measure cognitive load (latency and iterations) when correcting scientific figures. The plan implements a full instrumentation and analysis pipeline. **Crucially**, the pipeline distinguishes between *Software Verification* (using synthetic data/participants to test code logic) and *Research Execution* (using real CrafterBench data and human participants to generate results). All components run on the GitHub Actions free-tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `opencv-python==4.9.*`, `torchvision==0.18.*` (CPU-only ResNet-18), `fastapi==0.111.*`, `uvicorn==0.30.*`, `pytest==8.2.*`, `jsonschema==4.22.*`, `statsmodels==0.14.*`  
- **Storage**: File-system under `data/`  
- **Testing**: `pytest` with contract validation (`tests/contract/`)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: End-to-end pipeline ≤ 6 h wall-clock, ≤ 7 GB RAM, ≤ 2 CPU cores  
- **Constraints**: Must satisfy all Constitution Principles I-VII; random seeds pinned (`seed=42`).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All scripts are deterministic (global seed 42). Data are fetched from canonical sources or generated via fixed seeds for verification. |
| II. Verified Accuracy | The plan explicitly flags the CrafterBench source as 'Unverified' in `research.md` and treats the lack of a verified URL as a blocking issue for final research results. |
| III. Data Hygiene | `data/checksums.txt` records SHA-256 checksums for every file. Transformations create new files with provenance metadata. |
| IV. Single Source of Truth | Every figure statistic originates from immutable JSON logs in `data/logs/` and is referenced directly in `outputs/report.md`. |
| V. Versioning Discipline | All artifacts live under version control; CI generates content hashes stored in `state/projects/...yaml`. |
| VI. Human‑Subject Interaction Logging | `contracts/interaction_log.schema.yaml` enforces immutable raw logs. Real human sessions provide the only valid data for cognitive load inference. |
| VII. Ground‑Truth Validation Protocol | `run_validation.py` executes both exact vector comparison **and** semantic similarity; success requires **both** to pass. |

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
│   └── curate_failed_figures.py          # Real data curation; --verify-only for synthetic
├── interfaces/
│   ├── structured_harness.py             # FastAPI endpoint /edit (typed commands)
│   ├── chat_interface.py                 # FastAPI endpoint /edit (natural language)
│   └── session.py                        # /init_session returns counterbalanced order
├── logger/
│   └── interaction_logger.py             # JSONL writer, millisecond timestamps
├── validation/
│   ├── vector_match.py                   # exact JSON vector equality (no hard-coding)
│   ├── semantic_similarity.py            # ResNet-18 cosine similarity (no hard-coding)
│   └── run_validation.py                 # orchestrates both; writes SemanticValidation records
├── analysis/
│   ├── wilcoxon_analysis.py              # paired Wilcoxon, Bonferroni, effect size, CI
│   └── retention_check.py                # verifies ≥25 of 30 sessions have ≥1 success
├── simulation/
│   ├── power_analysis.py                 # Wilcoxon-appropriate power analysis
│   ├── simulate_participants.py          # high-volume synthetic driver for CI verification
│   └── human_data_collection.py          # stub for real participant data ingestion
├── utils/
│   ├── seeds.py                          # central seed management
│   └── checksums.py                      # helper to compute SHA-256
└── run_pipeline.py                       # orchestrates all steps in order
```

## Phase‑by‑Phase Task Breakdown

| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **0 – Environment Setup** | Create `requirements.txt`, pin seed = 42, add `state/` checksum logic. | I, III, V |
| **1 – Data Curation** | `curate_failed_figures.py` attempts to download the real CrafterBench subset. If no verified URL is found, the script exits with an error (blocking FR-001). A `--verify-only` flag allows generation of a deterministic synthetic surrogate (seed=42) for software testing only. | FR-001 (real required), SC-004 |
| **2 – Interface Provisioning** | `session.py` implements `/init_session` (counterbalanced order). `structured_harness.py` and `chat_interface.py` expose `/edit` endpoints. **Verification**: Implementer must provide logs showing 200 OK responses via `curl` for both interfaces. | FR-002, VI |
| **3 – Logging Instrumentation** | `interaction_logger.py` writes JSONL logs with millisecond precision. **Verification**: Implementer must demonstrate a log entry produced by a real `/edit` call that matches `interaction_log.schema.yaml`. | FR-003, VI |
| **4 – Power Analysis** | `power_analysis.py` computes minimum required N for Wilcoxon (effect size d≈0.5, α=0.05). Pipeline aborts if planned N < required. | SC-004 |
| **5 – Success Validation** | `run_validation.py` iterates over tasks. `vector_match.py` and `semantic_similarity.py` MUST compute actual results (hard-coded booleans are forbidden). Success requires **both** checks to pass. Results written to `SemanticValidation` records. | FR-004, FR-005, VII |
| **6 – Human Data Collection** | `human_data_collection.py` provides a CLI stub for ingesting logs from the actual study. This is the **only** phase that produces research-valid "objective latency" results. | VI, SC-001, SC-002 |
| **7 – Pipeline Verification (CI)** | `simulate_participants.py` generates [deferred] deterministic log entries (30 sessions) using the logger to verify the pipeline's capacity and schema compliance. These are **not** used for research inference. | SC-004 (verification) |
| **8 – Retention Check** | `retention_check.py` parses logs, counts sessions with ≥1 success, and fails if < 25. Must handle default log directory paths to avoid argparse errors. | SC-004 |
| **9 – Statistical Analysis** | `wilcoxon_analysis.py` runs paired Wilcoxon tests on `time_to_success` and `iteration_count` without normality pre-tests. Applies Bonferroni correction and calculates effect size *r*. | FR-006, SC-001, SC-002, SC-003 |
| **10 – Report Generation** | `generate_report.py` consumes `analysis_results.jsonl` to produce `outputs/report.md` containing medians, p-values, and success-rate tables. | FR-007, SC-005 |
| **11 – Contract Validation** | `pytest -q tests/contract` validates all JSONL files against schemas. | All FR/SC |
