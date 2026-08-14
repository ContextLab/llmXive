# Implementation Plan: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Branch**: `001-evaluating-code-summarization-bug-localization` | **Date**: 2025-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary
This project implements a human-subject study and statistical analysis pipeline to evaluate whether code summaries (LLM-generated vs. rule-based) improve bug localization accuracy and speed compared to a baseline. The system downloads the Defects4J dataset, generates summary variants (with fallback logic), simulates/participates in a data collection loop, and executes a rigorous statistical analysis (GLMM for accuracy, LME for speed) with bootstrapped confidence intervals and multiple-comparison correction. The entire analysis pipeline is designed to run on CPU-only GitHub Actions free-tier runners within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, scikit-learn, statsmodels, requests, numpy, datasets (HuggingFace), srcml (via subprocess), scipy, linearmodels  
**Storage**: Local CSV files (interaction logs), Parquet (Defects4J), JSON (config)  
**Testing**: pytest (unit), pytest-cov (coverage), custom CI workflows for reproducibility  
**Target Platform**: Linux (GitHub Actions free-tier runner), CPU-only  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Analysis pipeline completes in ≤6h; Timestamp precision ≤100ms; LLM inference timeout ≤30s (with fallback)  
**Constraints**: No GPU in CI; ≤7GB RAM; ≤14GB disk; Anonymized data only in VCS; DefectsJ v2.0 pinned  
**Scale/Scope**: A stratified sample of buggy methods; participants (simulated for CI); A substantial number of task observations  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

- **I. Reproducibility**: All random seeds pinned in `code/`; Defects4J version pinned in `data/defects4j_version.txt`; `requirements.txt` ensures isolated environment.
- **II. Verified Accuracy**: The Reference-Validator Agent runs on every artifact write that introduces or modifies citations (triggered by the `Reference-Validator` CI job). It verifies that all citations in `research.md` match the verified HuggingFace URLs provided in the prompt. If any citation is unreachable or mismatched, the build fails.
- **III. Data Hygiene**: Raw Defects4J data checksummed; derived summaries written to new files; PII removed from interaction logs before commit.
- **IV. Single Source of Truth**: All statistics in `paper/` trace to `data/analysis_results.csv`; no hand-typed numbers.
- **V. Versioning Discipline**: The Advancement-Evaluator Agent updates the `state/projects/PROJ-140-.../updated_at` timestamp and content hashes in the state file whenever any artifact under `code/`, `data/`, or `specs/` changes. This ensures the versioning discipline is enforced automatically.
- **VI. Human‑Subject Data Protection**: `data/interaction_logs/` contains only anonymized IDs; `data/consent/` excluded from VCS via `.gitignore`.
- **VII. Benchmark Dataset Integrity**: Defects4J v2.0 pinned; summaries saved as separate plain-text/CSV; original source unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-code-summarization-bug-localization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── interaction.schema.yaml
    ├── interaction_log.schema.yaml
    ├── analysis.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Load settings, seeds, paths
├── download.py          # Defects4J fetcher
├── summarize.py         # LLM (with fallback) and rule-based summary generators
├── simulate_study.py    # Simulates participant interactions for CI testing
├── analysis.py          # GLMM, LME, bootstrapping, correction
├── utils/
│   ├── pii.py           # Anonymization logic
│   └── timing.py        # Latency calibration
└── main.py              # Entry point for full pipeline

data/
├── raw/                 # Downloaded Defects4J (parquet)
├── processed/           # Extracted methods, summaries
├── interaction_logs/    # Anonymized CSV logs
├── consent/             # .gitignored
└── defects4j_version.txt

tests/
├── unit/
│   ├── test_download.py
│   ├── test_summarize.py
│   └── test_analysis.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

.github/
└── workflows/
    ├── ci.yml           # Runs tests and analysis
    ├── test_reproducibility.yml # Verifies CI run matches local run
    └── validate_citations.yml   # Runs Reference-Validator Agent
```

**Structure Decision**: Single-project structure (`code/`) chosen to simplify the research pipeline. All scripts are CLI-driven and modular. Tests are separated by type (unit, integration, contract). CI workflows explicitly handle the reproducibility check and citation validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| GPU Escape Hatch for LLM | LLM inference (CodeLlama-7B) cannot run on CPU within 30s timeout; requires 8-bit quantization on GPU. | CPU-only LLM inference is too slow (>30s) and violates the fallback constraint; simulation is insufficient for the "real" study, but CI uses simulation. |
| Dual Data Path (Real vs. Sim) | CI must run without human participants; real study needs real data. | A single path would either fail CI (no humans) or fail the study (no real data). The pipeline dynamically switches based on `--mode=sim` or `--mode=real`. This is mandated by US-1 and FR-003. |
| Statistical Rigor (Bootstrapping) | Required for effect size CIs with small N; standard asymptotic CIs are unreliable. | Simpler CIs (normal approximation) are invalid for small sample sizes and non-normal distributions of time-to-decision. |

## Implementation Tasks

### Phase 1: Data Acquisition & Preparation

- [ ] **T-001**: Download Defects4J v2.0 dataset from verified HuggingFace source.
- [ ] **T-002**: Extract stratified sample of buggy methods across Chart, Time, Math projects.
- [ ] **T-003**: Generate rule-based summaries using srcML.
- [ ] **T-010**: Implement local loopback latency test (FR-003) to verify ≤100ms timestamp precision.
- [ ] **T-014**: Implement LLM summary generation with fallback logic (FR-002). Logs errors and falls back to rule-based if timeout/empty.

### Phase 2: Study Execution (Simulation for CI)

- [ ] **T-020**: Generate Latin-square design for a cohort of participants × 30 tasks.
- [ ] **T-021**: Simulate participant interactions (clicks, timestamps) with noise.
- [ ] **T-022**: Anonymize participant IDs and log to `data/interaction_logs/anonymized_logs.csv`.

### Phase 3: Statistical Analysis

- [ ] **T-025**: Implement Holm-Bonferroni correction for primary tests (FR-006).
- [ ] **T-026**: Implement cluster bootstrap (resampling participants) for CIs with resamples and fixed seed (FR-005).
- [ ] **T-027**: Create `.github/workflows/test_reproducibility.yml` to verify CI results match local runs within tolerance (SC-004).
- [ ] **T-031b**: Implement `code/utils/verify_pii_removal.py` to scan `data/interaction_logs/` for PII and verify `data/consent/` is excluded from VCS.
- [ ] **T-035**: Implement compute feasibility verification (runtime, RAM, disk) to ensure ≤6h, ≤7GB RAM (SC-005).
- [ ] **T-036**: Implement reproducibility gate workflow to compare local vs. CI results (SC-004).

### Phase 4: Offline GPU Execution (Manual)

- [ ] **T-014-real**: **OFFLINE MANUAL STEP**. Execute `scripts/run_llm_gpu.sh` on a machine with CUDA (Kaggle/Local GPU).
  - **Deliverable**: `data/summaries/llm_summaries_real.csv`.
  - **Verification**: Script checks file exists and has N rows.
  - **Note**: This task is NOT [P] (parallel-safe) as it is a manual offline step. It is excluded from the automated CI flow.
  - **Dependency**: T-015-llm depends on this file for real mode, or falls back to T-014 sim data for CI.

### Phase 5: Integration & Reporting

- [ ] **T-040**: Generate final analysis report (JSON/CSV).
- [ ] **T-041**: Prepare reproducibility package for OSF.

## Detailed Task Descriptions (Selected)

### T-014-real: GPU Escape Hatch Script
**Status**: Offline Manual
**Description**: Run LLM inference on a GPU machine using 8-bit quantization.
**Script**: `scripts/run_llm_gpu.sh`
**Input**: `data/processed/methods.csv`
**Output**: `data/summaries/llm_summaries_real.csv`
**Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/summaries/llm_summaries_real.csv'); assert len(df) == 60"`
**Note**: This task is manually triggered and not part of the automated CI dependency graph.

### T-015-llm: Load Summaries
**Status**: Automated
**Description**: Load LLM summaries for analysis.
**Logic**:
- If `mode=real`: Check if `data/summaries/llm_summaries_real.csv` exists. If yes, load it. If no, raise error: "Real LLM summaries not found. Run T-014-real manually."
- If `mode=sim`: Load `data/summaries/llm_summaries_sim.csv` (generated by T-014).
**Dependency**: T-014 (sim) or T-014-real (real).

### T-027: Reproducibility Workflow
**Status**: Automated
**Description**: Create `.github/workflows/test_reproducibility.yml`.
**Content**: Runs the analysis script in a fresh GitHub Actions environment, compares output hash with a known-good reference hash stored in `data/reproducibility_ref.json`. Fails if mismatch > tolerance.

### T-031b: PII Verification
**Status**: Automated
**Description**: Run `code/utils/verify_pii_removal.py`.
**Logic**:
1. Scan `data/interaction_logs/anonymized_logs.csv` for PII patterns (email, name, IP).
2. Verify `data/consent/` is listed in `.gitignore` and not tracked by git.
3. Fail if PII found or `data/consent/` is tracked.

## Risk Mitigation

- **Risk**: LLM inference fails frequently.
  - **Mitigation**: Fallback to rule-based summaries (T-014). Log fallback count. Sensitivity analysis excludes fallback tasks.
- **Risk**: Small sample size (N=12).
  - **Mitigation**: Power analysis acknowledges limitation. Report effect sizes with wide CIs. Use cluster bootstrap.
- **Risk**: Compute limits on CI.
  - **Mitigation**: Streaming data load. Simulation for CI. Real LLM inference offloaded to GPU (T-014-real).