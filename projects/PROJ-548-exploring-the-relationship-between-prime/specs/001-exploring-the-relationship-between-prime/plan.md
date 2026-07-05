# Implementation Plan: Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis

**Branch**: `001-exploring-the-relationship-between-prime` | **Date**: 2026-07-05 | **Spec**: `specs/001-exploring-the-relationship-between-prime/spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-relationship-between-prime/spec.md`

## Summary

This project implements a statistical analysis pipeline to test the distributional alignment between **normalized maximal prime gaps** and the **GUE-predicted extreme value distribution** (derived from the Montgomery-Odlyzko conjecture). The approach relies on a segmented sieve to generate primes up to $N=10^{10}$ within strict memory constraints (Addresses FR-001, SC-004), ingesting verified zeta zero data from the LMFDB API (Addresses FR-002), and performing Kolmogorov-Smirnov (KS) tests of the maximal gap distribution against the theoretical GUE-derived extreme value CDF (Addresses FR-004, SC-001). The plan strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and computational feasibility on CPU-only CI.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `requests`, `pyyaml`  
**Storage**: Local CSV/JSON files in `data/` (no external database)  
**Testing**: `pytest` (unit tests for sieve logic, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Computational research pipeline  
**Performance Goals**: Complete full pipeline (sieve + analysis) in < 6 hours (Addresses SC-004); peak RAM < 7 GB (Addresses SC-004).  
**Constraints**: No GPU; no local generation of zeta zeros unless verified source is unreachable (per Constitution Principle II); strict memory chunking for sieve (Addresses FR-001).  
**Scale/Scope**: ~664 million primes up to $10^{10}$; ~+ zeta zeros (depending on verified source availability).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail | Linked SC | Measurement Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/analysis.py`; external datasets fetched from canonical LMFDB API; `requirements.txt` pins versions. | SC-004 | Re-run pipeline on fresh runner; verify output hashes match. |
| **II. Verified Accuracy** | **Pass** | Zeta zero ingestion logic includes a "Verified Source Check" that validates the URL against the `research.md` list. If no verified source exists, the pipeline halts with a "Data Unavailable" flag. Local `mpmath` generation is **disabled**. | SC-001, SC-003 | Log check result; halt if no verified source found. |
| **III. Data Hygiene** | **Pass** | All data files (`primes_gaps.csv`, `zeta_zeros.csv`) will be checksummed (SHA-256) upon generation/download. Raw data is immutable; derivations go to new files. | SC-004 | Verify checksums in `state/` map. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `results/` trace directly to `code/` execution. No hand-typed numbers in `paper/`. | SC-001, SC-002 | Traceback check in review. |
| **V. Versioning Discipline** | **Pass** | Content hashes recorded in `state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml` upon artifact write. | SC-004 | Check hash update in state file. |
| **VI. Extreme-Value Statistical Rigor** | **Pass** | Analysis explicitly normalizes gaps by $\log^2 p$ and compares the *empirical CDF of maximal gaps* to the *theoretical GUE-derived CDF of maximal gaps*. Permutation tests included for null distribution. | SC-001, SC-003 | Verify KS test input distributions are Max Gap CDFs. |
| **VII. Deterministic Sieve Implementation** | **Pass** | Segmented sieve implemented in chunks to ensure $<7$ GB RAM usage. Deterministic order guaranteed. | SC-004 | Monitor RAM usage logs; verify output determinism. |

## Project Structure

### Documentation (this feature)

```text
specs/001-exploring-the-relationship-between-prime/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── generate_primes.py      # Segmented sieve (FR-001, SC-004)
│   ├── ingest_zeros.py         # Zeta zero ingestion from LMFDB API (FR-002, SC-001)
│   └── preprocess.py           # Gap calculation & normalization (FR-003, SC-002)
├── analysis/
│   ├── distribution_test.py    # KS test & GUE Max Gap CDF comparison (FR-004, SC-001)
│   ├── monte_carlo.py          # Cramér model simulation (FR-005, SC-003)
│   └── robustness.py           # Sensitivity analysis (FR-006, SC-002)
├── utils/
│   ├── config.py               # Constants, seeds, paths
│   └── io.py                   # Checksumming, logging
└── cli/
    └── run_pipeline.py         # Orchestrator

tests/
├── contract/
│   └── test_schemas.py         # Validates against contracts/*.yaml
├── integration/
│   └── test_pipeline.py        # End-to-end small scale run
└── unit/
    ├── test_sieve.py
    └── test_stats.py

data/
├── raw/                        # Downloaded/generated raw data (checksummed)
├── processed/                  # Normalized gaps, zero spacings
└── results/                    # JSON outputs, plots

results/
└── correlation_results.json
```

**Structure Decision**: Single-project structure selected to minimize overhead. `src/data` handles ingestion, `src/analysis` handles the statistical core. This separation ensures data generation can be re-run independently of analysis changes, supporting reproducibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Segmented Sieve | Required to fit $10^{10}$ primes in < 7GB RAM (FR-001, SC-004). | A standard sieve (e.g., `primesieve` or full array) would require > 15GB RAM, violating CI constraints. |
| Chunked Processing | Required to prevent OOM during gap calculation (FR-001, SC-004). | Loading all gaps into memory at once exceeds available RAM. |
| KS Test (Distributional) | Required by spec (FR-004) to compare bulk distributions of *maximal gaps*, not pointwise. | Pointwise correlation is mathematically invalid due to lack of index mapping between primes and zeros. |

## Methodological Correction & Scope

**Note on Methodology**: The plan explicitly addresses the methodological concerns regarding the comparison of maximal gaps to GUE.
1.  **Target**: The primary analysis compares the **Empirical CDF of Normalized Maximal Gaps** (from sliding windows) against the **Theoretical CDF of Maximal Gaps derived from GUE** (via Extreme Value Theory integration of the pair-correlation function).
2.  **Null Hypothesis**: $H_0$: The distribution of normalized maximal gaps follows the GUE-predicted extreme value distribution.
3.  **Fallback**: If the full $N=10^{10}$ sieve exceeds the 6-hour CI limit, the pipeline will automatically switch to a "subsampled" mode ($N=10^9$) and log this limitation, ensuring the pipeline completes (Addresses SC-004).
