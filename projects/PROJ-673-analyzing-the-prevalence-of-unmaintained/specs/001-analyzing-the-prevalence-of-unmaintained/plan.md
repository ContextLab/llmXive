# Implementation Plan: Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

**Branch**: `001-analyzing-unmaintained-dependencies` | **Date**: 2026-06-26 | **Spec**: `specs/001-analyzing-the-prevalence-of-unmaintained/spec.md`

## Summary

This project investigates the correlational relationship between the age of unmaintained NPM dependencies (measured by days since last release) and their exposure to unpatched security vulnerabilities (measured by count of currently unpatched CVEs). The approach involves programmatically collecting data from the NPM registry and GitHub APIs for the top downloaded packages, aggregating dependency metadata, and performing a Spearman rank correlation analysis with a Zero-Inflated Negative Binomial (ZINB) sensitivity analysis. The study adheres to an observational framework, avoiding causal claims, and strictly respects the GitHub Actions free-tier compute constraints (CPU-only, 6h runtime, <7GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests` (API interaction), `pandas` (data manipulation), `scipy` (statistical testing), `statsmodels` (ZINB regression), `matplotlib` (visualization), `pyyaml` (schema handling).  
**Storage**: Local CSV/JSON files under `data/` (checksummed per Constitution).  
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Data Analysis Pipeline / CLI Tool.  
**Performance Goals**: Complete full data collection and analysis within 6 hours on 2 vCPU.  
**Constraints**: No GPU; no large LLM inference; strict rate-limiting handling (exponential backoff); all data must be reproducible from cached snapshots.  
**Scale/Scope**: Top [deferred] NPM packages (e.g., top [deferred]–[deferred] by weekly downloads) and their transitive dependencies (estimated < 50k unique packages).

> **Note**: Specific counts for package scope and dataset sizes are deferred to the research/implementation phase to allow for adaptive sampling based on API rate limits and runtime budgets.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds pinned in `code/`. External datasets (NPM/GitHub) cached as immutable snapshots in `data/` before analysis.
- **II. Verified Accuracy**: All dataset references in `research.md` are verified URLs from the provided "Verified datasets" block. No fabricated URLs.
- **III. Data Hygiene**: **Principle III** requires that datasets be checksummed and no data modified in place. All raw API responses saved with checksums. Derived datasets (e.g., `dependencies_cleaned.csv`) generated with new filenames.
- **IV. Single Source of Truth**: All statistics in the final report trace to `data/` rows and `code/` execution blocks.
- **V. Versioning Discipline**: **Principle V** requires every artifact carries a content hash. Artifacts carry content hashes. State file updated on changes.
- **VI. API Snapshot Integrity**: NPM/GitHub queries cached. Analysis re-runs use these snapshots to ensure temporal consistency.
- **VII. Transitive Resolution Completeness**: **Principle VII** states: "Vulnerability density calculations MUST account for the full transitive dependency tree. Incomplete traversal of dependency graphs invalidates the correlation analysis." The plan implements recursive traversal ensuring full tree resolution; incomplete trees are flagged or excluded per FR-002/FR-007.

## Project Structure

### Documentation (this feature)

```text
specs/001-analyzing-unmaintained-dependencies/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── models/              # Data models (Pydantic/Dict schemas)
├── services/            # API clients (NpmClient, GithubClient, AuditClient)
├── analysis/            # Statistical logic (correlation, stratification, ZINB)
├── cli/                 # Entry point script
└── utils/               # Logging, backoff, checksum helpers

tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests (mocked APIs)
└── unit/                # Logic tests (e.g., age calculation)

data/
├── raw/                 # Cached API snapshots (immutable)
└── processed/           # Derived datasets (checksummed)
```

**Structure Decision**: Single-project structure with clear separation of concerns (Services for data, Analysis for logic). This minimizes overhead and aligns with the CLI nature of the tool.

## Complexity Tracking

No violations requiring justification. The single-project structure is sufficient for the scope (data collection + statistical analysis).