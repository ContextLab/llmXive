# Implementation Plan: Statistical Bias in Pre-Print Server Publication Trends

**Branch**: `001-statistical-bias-in-pre-print-server-pub` | **Date**: 2026-08-13 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-statistical-bias-in-pre-print-server-pub/spec.md`

## Summary

This project implements a statistical pipeline to detect bias in pre-print publication trends by comparing pre-print server versions (arXiv, bioRxiv) against their final peer-reviewed journal counterparts. The technical approach involves:
1.  **Data Acquisition**: Fetching OpenAlex metadata (via verified Hugging Face sources) to match pre-prints with DOIs, and scraping arXiv/bioRxiv IDs.
2.  **Extraction**: Parsing PDFs to extract p-values (handling inequalities as interval-censored data) and effect sizes.
3.  **Analysis**: Performing Kolmogorov-Smirnov tests and density ratio estimation on p-value distributions, and paired t-tests/Wilcoxon tests (with interval-censored bootstrapping) on effect size differences ($\Delta$ES), with sensitivity analysis across significance thresholds.
4.  **Output**: Generating a structured CSV dataset and statistical reports quantifying distributional shifts.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `numpy`, `requests`, `pdfplumber`, `datasets` (Hugging Face), `regex`, `rapidfuzz`  
**Storage**: Local CSV/Parquet files in `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, ~7GB RAM)  
**Project Type**: Data analysis pipeline / CLI tool  
**Performance Goals**: Process a representative sample (target ~500 matched pairs) within 6 hours.  
**Constraints**: CPU-first execution; no GPU required for statistical tests; PDF parsing must be robust to LaTeX formatting.  
**Scale/Scope**: A substantial set of initial queries to yield a sufficient number of valid matched pairs; processing time < 6h.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/`; external data fetched from verified Hugging Face URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | All dataset URLs in `research.md` sourced exclusively from the "Verified datasets" block. Citations validated against primary sources. |
| **III. Data Hygiene** | **Compliant** | Raw data stored in `data/raw/` with checksums; derivations in `data/processed/` with versioned filenames. |
| **IV. Single Source of Truth** | **Compliant** | All analysis outputs trace to `matched_pairs.csv`; no hand-typed statistics in reports. |
| **V. Versioning Discipline** | **Compliant** | Artifact hashes tracked in `state/` manifest; code changes trigger hash updates; **every research-stage artifact change updates `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml` `updated_at` timestamp** as mandated. |
| **VI. Paired-Artifact Integrity** | **Compliant** | Matching algorithm enforces 1:1 linkage; unmatched pairs excluded from paired analysis; methodological shifts flagged and excluded. |
| **VII. Distributional Shift Quantification** | **Compliant** | Analysis focuses on magnitude of shift (KS statistic, density ratios, $\Delta$ES) rather than binary significance; confidence intervals reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-bias-in-pre-print-server-pub/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── matched_pairs.schema.yaml
│   ├── analysis_results.schema.yaml
│   └── statistical_metric.schema.yaml  # Validates internal metrics.csv or JSON array
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-075-statistical-bias-in-pre-print-server-pub/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_fetch_and_match.py       # OpenAlex query & fuzzy matching
│   ├── 02_extract_stats.py         # PDF parsing & metric extraction
│   ├── 03_analysis.py              # KS tests, density ratios, paired tests, sensitivity analysis
│   ├── utils/
│   │   ├── pdf_parser.py
│   │   ├── matching.py
│   │   └── stats_helpers.py
│   └── main.py                     # Pipeline orchestration
├── data/
│   ├── raw/                        # OpenAlex dumps, scraped PDFs
│   └── processed/
│       ├── matched_pairs.csv       # Final dataset
│       ├── metrics.csv             # Extracted metrics (validated by statistical_metric.schema.yaml)
│       └── analysis_results.json   # Statistical outputs
├── tests/
│   ├── unit/
│   │   ├── test_matching.py
│   │   └── test_extraction.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── ...
```

**Structure Decision**: Single-project structure (Option 1) is selected. The project is a linear data pipeline (Fetch -> Extract -> Analyze), not a web service or mobile app. This minimizes overhead and aligns with the CPU-first, CI-runnable constraint.

## Complexity Tracking

No violations found. The complexity is driven by the need for robust PDF parsing and fuzzy matching, which are handled by established libraries (`pdfplumber`, `rapidfuzz`) without introducing architectural bloat.