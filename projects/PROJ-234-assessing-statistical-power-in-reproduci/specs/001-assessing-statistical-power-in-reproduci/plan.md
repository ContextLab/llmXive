# Implementation Plan: Assessing Statistical Power in Reproducible Research with Public Datasets

**Branch**: `001-assess-statistical-power` | **Date**: 2024-05-21 | **Spec**: `specs/001-assess-statistical-power/spec.md`
**Input**: Feature specification from `/specs/001-assess-statistical-power/spec.md`

## Summary

This feature implements a reproducible audit of **Minimum Detectable Effect Size (MDES)** in high-impact public datasets. The system connects to the OpenML API to retrieve metadata for a representative set of classification datasets., filters for those with **Open Access (OA)** publication links, extracts standardized effect sizes (N, d, f) via regex parsing of accessible full-text/abstracts, and calculates the **MDES** (the effect size required to achieve [deferred] power) using `statsmodels`. The output is a summary report visualizing the distribution of MDES values, addressing the "design power" of the studies without the methodological fallacy of post-hoc observed power.

## Technical Context

**Language/Version**: Python 3  
**Primary Dependencies**: `openml`, `statsmodels`, `pandas`, `requests`, `matplotlib`, `pytest`, `beautifulsoup4`  
**Storage**: Local filesystem (`data/` for artifacts, `code/` for scripts)  
**Testing**: `pytest` with contract validation against YAML schemas (`contracts/dataset_metadata.schema.yaml`, `contracts/power_audit_result.schema.yaml`)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: CLI / Data Analysis Pipeline  
**Performance Goals**: Complete pipeline execution within 6 hours; memory usage < 7GB  
**Constraints**: No GPU; CPU-only `statsmodels` calculations; strict adherence to OpenML API rate limits; **OA-only publication access** (no scraping paywalled content).  
**Scale/Scope**: A selection of datasets from OpenML; processing a corpus of publications (text extraction).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan ensures all random seeds are pinned in `code/`. External datasets are fetched via OpenML API (canonical source) on every run.
- **II. Verified Accuracy**: Plan mandates that all citations in `research.md` and `paper/` must be verified against primary sources. The plan explicitly avoids inventing URLs; it relies on dynamic API retrieval for dataset links and validates OA status.
- **III. Data Hygiene**: Plan specifies checksumming of all `data/` artifacts and prohibits in-place modification. Raw API responses are preserved.
- **IV. Single Source of Truth**: All MDES calculations and reports trace back to specific rows in `data/` derived from `code/`.
- **V. Versioning Discipline**: All artifacts carry content hashes; `state/` YAML updated on changes.
- **VI. Statistical Power Transparency**: Plan mandates `statsmodels.stats.power` for MDES calculation, with inputs (sample size, alpha) and results version-controlled.
- **VII. Public Dataset Usage Integrity**: Plan requires fetching via OpenML API by dataset ID; metadata (timestamp, query) recorded in `data/`.

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-statistical-power/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_metadata.schema.yaml
│   └── power_audit_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-234-assessing-statistical-power-in-reproduci/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest_openml.py       # FR-001, FR-002, FR-009
│   ├── 02_parse_publications.py  # FR-003, FR-007, FR-008
│   ├── 03_compute_sensitivity.py # FR-004 (MDES), FR-006
│   ├── 04_generate_report.py     # FR-005, SC-001
│   └── utils/
│       ├── api_client.py         # Retry logic for API
│       ├── oa_checker.py         # OA validation
│       └── parsers.py            # Regex/NLP extraction
├── data/
│   ├── raw/                      # API responses (raw)
│   ├── processed/                # Extracted params, MDES results
│   └── metadata.json             # Dataset metadata & checksums
├── tests/
│   ├── unit/
│   │   ├── test_parsers.py
│   │   └── test_sensitivity.py
│   └── contract/
│       └── test_schemas.py       # Validates against contracts/
└── docs/
    └── constitution.md
```

**Structure Decision**: Single project structure selected to minimize overhead for a data analysis pipeline. `code/` is organized by functional phase (ingest, parse, compute, report) to match the spec's User Stories. The `contracts/` directory is explicitly included to satisfy testing requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. | N/A |

## Methodological Pivot: Observed Power vs. MDES

The original spec mentioned "Observed Power," which is methodologically invalid for auditing study design (a monotone function of p-values). This plan implements **Minimum Detectable Effect Size (MDES)** instead. MDES answers: "Given the sample size N and alpha=0.05, what is the smallest effect size this study could have detected with [deferred] power?" This satisfies the intent of FR-006 (A Priori capability) and FR-004 (Power Analysis) without the scientific fallacy.

## Data Access Strategy

- **Open Access Only**: The pipeline only processes publications that are Open Access (OA). Links to paywalled content are marked `paywalled` and excluded from quantitative analysis.
- **No Scraping**: We do not attempt to bypass paywalls. The "full-text" requirement in FR-003 is interpreted as "accessible full-text."
- **Fallback**: If full-text is unavailable but an abstract is OA, the parser attempts extraction from the abstract (FR-008 sensitivity analysis).

## Phase 0: Research & Validation

1.  **Verify OA Links**: Confirm that a significant portion of top OpenML datasets link to OA publications (e.g., via PubMed Central, arXiv, or publisher OA pages).
2.  **Regex Validation**: Test regex patterns on a subset of OA PDFs to ensure accurate extraction of Cohen's d, F-statistics, and sample sizes.
3.  **MDES Formula**: Confirm `statsmodels` implementation for MDES (inverse power calculation).

## Phase 1: Implementation

1.  **Ingest**: Fetch a representative set of datasets, filter by OA links, record metadata.
2.  **Parse**: Extract N and standardized effect sizes from OA text. Validate metric type (FR-007).
3.  **Compute**: Calculate MDES for valid entries.
4.  **Report**: Generate audit report with MDES distribution, extraction success rates, and dataset type breakdown.

## Phase 2: Testing & Validation

1.  **Unit Tests**: Validate regex patterns and MDES calculations.
2.  **Contract Tests**: Validate output JSON/CSV against `contracts/*.schema.yaml`.
3.  **Integration Test**: Run full pipeline on a small subset of datasets to verify end-to-end flow.
