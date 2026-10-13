# Implementation Plan: Mindfulness Components and Delivery Formats in ASD Social Skills

**Branch**: `feat/mindfulness-asd-meta-analysis` | **Date**: 2026-05-20
**Spec**: [spec.md]
**Input**: Feature specification for meta-analysis of mindfulness interventions for children (6-12) with ASD.

## Summary
This project implements a systematic data extraction and meta-analysis pipeline to evaluate the efficacy of mindfulness-based interventions on social skills in children with ASD. The technical approach involves programmatically querying ClinicalTrials.gov and OSF APIs, extracting intervention components and delivery formats via a structured keyword-based pipeline with manual verification, calculating Hedges' $g$ effect sizes with small-sample corrections, and performing random-effects meta-analysis with subgroup analyses for delivery formats and social skill domains.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `requests`, `pyyaml`, `jsonschema`
**Storage**: Local CSV/JSON files (`data/raw/`, `data/processed/`)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions Runner)
**Project Type**: research-pipeline
**Performance Goals**: Complete pipeline execution $\le 6$ hours.
**Constraints**: $\le 7$ GB RAM, $\le 14$ GB disk, CPU-only.
**Scale/Scope**: Meta-analysis of registered clinical trials (2015–2024).

## Constitution Check

| Principle | Requirement | Plan Mapping |
|-----------|-------------|--------------|
| I. Reproducibility | Fresh runner execution, pinned seeds, canonical sources. | All code in `code/`, seeds pinned in analysis scripts, sources limited to ClinicalTrials.gov/OSF. |
| II. Verified Accuracy | Citations verified against primary sources. | `research.md` uses verified registry sources; results trace to `data/processed/`. |
| III. Data Hygiene | Checksummed artifacts, no in-place modification. | Pipeline produces new files at each stage: `raw` $\rightarrow$ `processed` $\rightarrow$ `results`. |
| IV. Single Source of Truth | Figures/stats trace to one row/block. | Result tables generated programmatically from `effect_sizes.csv`. |
| V. Versioning Discipline | Content hashes for artifacts. | All outputs stored in versioned directories; state updated via platform runtime. |
| VI. Registry Integrity | Limited to ClinicalTrials.gov and OSF (2015-2024). | `code/data/collector.py` strictly filters by these registries and date range. |
| VII. Delivery Verification | Explicit tagging of `delivery_format`. | `code/data/cleaner.py` implements mandatory tagging for caregiver-mediated vs child-led formats. |

## Project Structure

### Source Code
```text
src/
├── data/
│   ├── collector.py      # API retrieval (FR-001, FR-002)
│   └── cleaner.py        # Cleaning, tagging, and splitting (FR-003, FR-008, FR-009, FR-010)
├── analysis/
│   ├── effect_sizes.py   # Hedges' g calculation (FR-004, FR-013)
│   └── meta_analysis.py   # Random-effects, subgroups, and bias (FR-005, FR-011, FR-012, FR-014)
├── viz/
│   └── plotting.py       # Forest and Funnel plots (FR-006)
└── lib/
    └── validation.py      # Schema validation (FR-007)
tests/
├── unit/                 # Tests for calculation logic
├── integration/          # End-to-end pipeline tests
└── contract/             # Schema validation tests
```

**Structure Decision**: Single project structure. Logic is split by the data lifecycle: Collection $\rightarrow$ Cleaning $\rightarrow$ Analysis $\rightarrow$ Visualization.

## Implementation Phases

### Phase 1: Foundation & Contracts
- **Task 1**: Define and implement `contracts/cleaned_study.schema.yaml` and `contracts/effect_size.schema.yaml` to ensure data integrity (FR-007).
- **Task 2**: Implement `src/lib/validation.py` to validate dataframes against these YAML schemas.

### Phase 2: Data Collection Pipeline (US1)
- **Task 3**: Implement `src/data/collector.py` to fetch records from ClinicalTrials.gov and OSF APIs with exponential backoff (FR-001, FR-002).
- **Task 4**: Implement `src/data/cleaner.py` to:
    - Filter by age (6-12) and ASD diagnosis.
    - Extract components (breathing, body scan, movement) and social skill domains using a structured keyword-based pipeline with confidence scoring; entries with low confidence are flagged for manual verification to ensure construct validity (addresses methodology-adaacf0e; overrides FR-003).
    - Tag `delivery_format` (caregiver-mediated vs child-led) per Constitution Principle VII.
    - Handle multi-arm studies by selecting a single primary control group per treatment arm to avoid double-counting participants and prevent unit-of-analysis error (addresses methodology-484666b9, scientific_soundness-6316c4f1; overrides FR-008).
    - Implement abstract-only fallback (FR-009).
- **Task 5**: Generate `data/raw/verified_snapshot_2026.json` as a canonical baseline for CI reproducibility (resolves circular dependency).

### Phase 3: Effect Size Calculation (US2)
- **Task 6**: Implement `src/analysis/effect_sizes.py` to compute Hedges' $g$ from summary statistics (means, SDs, N) with small-sample correction (FR-004, FR-013).
- **Task 7**: Produce `data/processed/effect_sizes.csv` and validate against the effect size schema.

### Phase 4: Meta-Analysis & Subgroups (US2)
- **Task 8**: Implement `src/analysis/meta_analysis.py` to perform random-effects meta-analysis (if $I^2 > 50\%$) and calculate heterogeneity statistics (FR-005).
- **Task 9**: Implement subgroup analysis for:
    - Social skill domains (FR-011).
    - Follow-up duration (3-month vs others) (FR-012).
    - Delivery format (caregiver-mediated vs child-led).
- **Task 10**: Implement conditional logic to suppress meta-regression and Egger's test if $N < 10$ (FR-014).

### Phase 5: Visualization & Reporting (US3)
- **Task 11**: Implement `src/viz/plotting.py` to generate forest plots (study CIs + pooled diamond) and funnel plots (if $N \ge 10$) (FR-006).
- **Task 12**: Implement final report generator that handles $N=0$ cases (stating "No studies found") and $N < 10$ cases (descriptive synthesis only) to ensure robust output.

## Risk Mitigation & Rigor

- **Small Sample Size**: If $N < 10$, the pipeline switches to descriptive synthesis and suppresses the funnel plot and Egger's test (FR-014).
- **Heterogeneity**: Random-effects is the default if $I^2 > 50\%$; otherwise, fixed-effects is reported as a sensitivity check.
- **Multi-comparison**: Bonferroni correction applied to p-values in subgroup analyses.
- **Data Sourcing**: Strictly limited to ClinicalTrials.gov and OSF (Constitution Principle VI).
- **CPU Feasibility**: All analysis uses `scipy` and `statsmodels` on CPU; no GPU required.