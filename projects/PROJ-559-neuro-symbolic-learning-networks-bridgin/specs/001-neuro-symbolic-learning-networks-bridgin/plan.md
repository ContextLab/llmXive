# Implementation Plan: Neuro-Symbolic Learning Networks

**Branch**: `[PROJ-559-neuro-symbolic]` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/PROJ-559-neuro-symbolic/spec.md`

## Summary

This project implements a lightweight neuro-symbolic explanation framework to evaluate the pedagogical impact of three explanation types (neural-only, symbolic-only, neuro-symbolic) on student performance. The system ingests mathematics problems from public datasets (**ASSISTments as the sole verified source**; Khan Academy is attempted but excluded if no direct download URL exists), generates explanations using a quantized small LLM (neural) and a rule-based solver (symbolic), and combines them via a translation layer. A BKT-based student simulator, calibrated strictly against real human pilot data (or scope-reduced if unavailable), generates interaction logs. The pipeline culminates in a mixed-effects regression analysis comparing the three conditions, incorporating real student data where available, while strictly adhering to CPU-first constraints (2 cores, 7 GB RAM) and reproducibility standards.

**Critical Design Decision & Scope Limitation**: The study employs a **between-subjects design** where each simulated student is assigned to exactly one explanation condition per problem to avoid carryover effects. **Crucially, due to the lack of a verified, direct-download URL for the full Khan Academy dataset in the `# Verified datasets` block, the study is scoped to the ASSISTments dataset only.** External validity claims regarding "general mathematics education" are restricted to the ASSISTments domain. If a second verified dataset becomes available, the Scope Reduction Protocol is lifted; otherwise, the final report will explicitly state that findings are limited to the ASSISTments corpus to maintain scientific integrity (Constitution Principle II).

## Technical Context

**Language/Version**: Python 3.11 (primary logic, data processing), R 4.3+ (statistical analysis via `rpy2`), Bash (orchestration).
**Primary Dependencies**: `transformers` (quantized LLM), `scikit-learn` (simulator logic), `pandas`, `numpy`, `statsmodels` (mixed-effects), `pyyaml`, `datasets` (Hugging Face).
**Storage**: Local file system (`data/raw`, `data/processed`, `data/pilot`), CSV/Parquet formats.
**Testing**: `pytest` (unit/integration), `pytest-cov` (coverage), CI resource monitoring scripts.
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7 GB RAM).
**Project Type**: Data science research pipeline / CLI tool.
**Performance Goals**: < 6h total runtime; < 7 GB peak RAM; < 2 cores active average.
**Constraints**: No local GPU; strict timeout handling for downloads; deterministic seeding for reproducibility.
**Scale/Scope**: A large number of simulated interactions (multiple per condition) + ~200 real interactions; ~500-1,000 problem instances.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `config.yaml`. External datasets fetched via verified Hugging Face URLs. CI runs isolated `venv`. |
| **II. Verified Accuracy** | **PASS** | **Automated Gate**: The `Reference-Validator Agent` is implemented as a specific GitHub Actions step (`validate-citations`) that runs as a `pre-merge` check on PRs. It invokes `code/tools/reference_validator.py` which parses citations, checks reachability, calculates the `CITATION_TITLE_OVERLAP_THRESHOLD` (a configurable similarity threshold), and exits with code 1 if the threshold is not met or a source is unreachable. This physically blocks the pipeline transition. Dataset URLs are cross-referenced against the `# Verified datasets` block. |
| **III. Data Hygiene** | **PASS** | `data/raw` files are immutable. Checksums (SHA-256) generated and stored in `state/` upon download. Derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | Analysis scripts read directly from `data/processed`. No manual data entry in reports. |
| **V. Versioning Discipline** | **PASS** | **SSoT File**: `state/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin.yaml`. Updated by `state-updater.sh` after each phase with content hashes. |
| **VI. Educational Evaluation Rigor** | **PASS** | Mixed-effects model includes `explanation_condition`, `prior_knowledge`, and `problem_difficulty` as fixed effects (see `analysis/regression_analysis.py`). |
| **VII. Explanation Traceability** | **PASS** | Every generated explanation stored with metadata (problem_id, model_version, condition) in `data/traces/`. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-559-neuro-symbolic/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Schemas)
```

### Source Code (repository root)

```text
projects/PROJ-559-neuro-symbolic/
├── code/
│   ├── __init__.py
│   ├── config.yaml              # Global config, seeds, dataset URLs
│   ├── data/
│   │   ├── download_assistments.py
│   │   ├── download_khan.py
│   │   ├── unify_datasets.py    # Handles partial success if Khan missing
│   │   ├── validate_schema.py   # Reads from ../contracts/
│   │   └── download_utils.py    # Timeout handling, checksums
│   ├── generation/
│   │   ├── symbolic_solver.py   # Rule-based logic for math problems
│   │   ├── neural_generator.py  # Quantized LLM wrapper (small-scale/4-bit)
│   │   ├── neuro_symbolic.py    # Translation/merging layer
│   │   ├── batch_generate.py    # Orchestrates generation
│   │   └── quality_check.py     # T016: Coherence check
│   ├── simulation/
│   │   ├── bkt_model.py         # Bayesian Knowledge Tracing logic
│   │   ├── simulator.py         # Interaction loop
│   │   ├── pilot_calibrator.py  # Calibration against human pilot (T031)
│   │   └── run_simulation.py    # Main simulation driver
│   ├── analysis/
│   │   ├── merge_data.py        # Merge sim + real data (T060)
│   │   ├── regression_analysis.py # Mixed-effects model (statsmodels)
│   │   └── report_generator.py  # Markdown output
│   ├── tools/
│   │   └── reference_validator.py # Implements the Verified Accuracy gate
│   └── tests/
│       ├── test_download.py
│       ├── test_generation.py
│       └── test_simulation.py
├── data/
│   ├── raw/                     # Downloaded datasets (immutable)
│   ├── pilot/                   # Pilot calibration data (T030b)
│   ├── processed/               # Unified problems, logs
│   └── traces/                  # Explanation artifacts
├── contracts/                   # SCHEMAS (Root level)
│   ├── problem.schema.yaml
│   ├── interaction_log.schema.yaml
│   └── explanation.schema.yaml
├── state/                       # SSoT State File
│   └── projects/PROJ-559-neuro-symbolic-learning-networks-bridgin.yaml
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular monorepo structure was chosen to separate concerns. The `contracts/` directory is at the repository root to ensure `validate_schema.py` can easily locate schemas. The `state/` directory contains the Single Source of Truth file, updated by `state-updater.sh`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Neuro-Symbolic Translation Layer** | Required to fuse symbolic traces with neural narratives (FR-002, US-1). | A simple concatenation fails to provide the "reasoning" integration required for the "neuro-symbolic" condition, reducing validity. |
| **BKT Simulator + Calibration** | Required to generate realistic student responses without human cost (US-2, FR-010). | Pure random noise or static rules fail to model learning trajectories, invalidating the "response time" and "comprehension" metrics. **Must be calibrated on real human data (T030b) or scope reduced.** |
| **Hybrid Analysis (Sim + Real)** | Required to support generalizable claims (US-7, FR-011). | Relying solely on simulation is scientifically invalid for educational claims; real data is essential for the final conclusion. |
| **Partial Ingestion (Khan)** | Required to handle missing Khan data without aborting. | A hard abort would prevent the study from proceeding with ASSISTments, violating the "attempt" requirement of FR-001. **Scope Reduction Protocol now limits claims to ASSISTments if Khan is missing.** |

## Scope Reduction Protocol (Critical)

In the event that the **Khan Academy** dataset cannot be downloaded (due to lack of a verified URL or timeout), the system executes the following protocol to maintain scientific integrity:
1.  **Log Failure**: The `download_khan.py` script logs `ERROR: Failed to download Khan Academy within 300 seconds – aborting pipeline` and exits with code 0 (graceful skip) but sets a global flag `khan_available = False`.
2.  **Proceed with ASSISTments**: The pipeline continues using only the ASSISTments dataset.
3.  **Downgrade Claims**: The `report_generator.py` automatically detects `khan_available = False` and modifies the final report's "Limitations" section to state: *"Findings are generalizable only to the ASSISTments corpus; claims regarding broader mathematics education are not supported due to single-dataset constraints."*
4.  **No Fabrication**: No synthetic data or proxy datasets are used to replace Khan Academy.
5.  **Constitution Compliance**: This protocol satisfies Constitution Principle II (Verified Accuracy) by ensuring no false claims about dataset coverage are made.