# Implementation Plan: Automated Detection of Algorithmic Bias in Public Code Repositories

**Branch**: `001-auto-detect-bias` | **Date**: 2026-08-18 | **Spec**: `specs/001-auto-detect-bias/spec.md`

## Summary

This feature implements a static analysis pipeline to detect "Textual Bias Scores" in Python repositories and correlates them with simulated fairness metrics. The approach strictly adheres to the project constitution: (1) Static parsing via `ast` (no code execution), (2) Synthetic data generation from domain-neutral distributions (no circularity), and (3) Statistical correlation with Bonferroni correction. The pipeline runs on CPU-first infrastructure, streaming repository data and sampling synthetic datasets to fit within GitHub Actions free-tier limits (2 cores, 7 GB RAM, 6h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `ast` (stdlib), `nltk` (VADER), `pandas`, `numpy`, `scipy`, `fairlearn`, `datasets` (HuggingFace), `requests`  
**Storage**: Local `data/` directory (checksummed), `state/` YAML for artifact tracking  
**Testing**: `pytest` (unit), `pytest-cov`  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Research CLI / Data Pipeline  
**Performance Goals**: Process 500 repos in ≤6h; Memory ≤7 GB; No GPU required.  
**Constraints**: No execution of repo code; No external API keys beyond public GitHub rate limits; Synthetic data must be statistically independent of source text.  
**Scale/Scope**: 500 public Python repositories; 200 manually labeled comments for validation.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Check | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned in `code/simulation.py`; `requirements.txt` pins versions; `data/` checksums recorded in `state/`. |
| **II. Verified Accuracy** | PASS | Citations (VADER, Fairlearn) verified against HuggingFace/official docs. No fabricated URLs. |
| **III. Data Hygiene** | PASS | Raw repo clones saved to `data/raw/`; processed artifacts to `data/derived/`; checksums computed via `sha256sum`. No in-place edits. |
| **IV. Single Source of Truth** | PASS | All stats in `plan.md` derived from `data/derived/correlation_results.csv`. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` updated on every artifact write; content hashes tracked. |
| **VI. Synthetic Data Independence** | PASS | Synthetic data generated via `numpy.random` with fixed seeds; explicit string-hash verification (FR-015) ensures zero token overlap with source code. |
| **VII. Static Analysis Fidelity** | PASS | Parsing uses `ast.parse()` only; no `exec()` or `eval()` on repo code. |

## Project Structure

### Documentation (this feature)
```text
specs/001-auto-detect-bias/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)
```text
projects/PROJ-059-automated-detection-of-algorithmic-bias-/
├── code/
│   ├── __init__.py
│   ├── config.py                # Constants, seeds, thresholds
│   ├── data_ingestion.py        # GitHub API wrapper, repo cloning
│   ├── static_analysis.py       # AST parsing, VADER scoring (FR-001, FR-002, FR-003)
│   ├── simulation.py            # Synthetic data, bias injection (FR-004, FR-005, FR-011)
│   ├── validation.py            # VADER threshold check, Kappa score (FR-010, FR-013)
│   ├── correlation.py           # Spearman, Bonferroni, sensitivity analysis (FR-006, FR-007, FR-008)
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Cloned repos (git refs), VADER parquet (streamed)
│   ├── derived/
│   │   ├── repo_scores.csv      # Aggregated Textual Bias Scores
│   │   ├── simulation_results.csv # Fairness metrics per repo
│   │   ├── validation_metrics.json # Kappa scores
│   │   └── correlation_results.csv # Final stats
│   └── curated/
│       ├── validation_comments.csv # 200 manually labeled comments
│       └── error_injection_set.csv # 100 repos with syntax errors
├── tests/
│   ├── unit/
│   │   ├── test_static_analysis.py
│   │   ├── test_simulation.py
│   │   └── test_correlation.py
│   └── contract/
│       └── test_schema_validation.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to minimize overhead and align with the CLI nature of the research pipeline. All processing is sequential and stateless between phases, allowing a single entry point (`main.py`).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The pipeline is linear: Ingest → Analyze → Simulate → Correlate. No complex architecture is required. | A microservice architecture would add unnecessary network overhead and deployment complexity for a batch research job. |
