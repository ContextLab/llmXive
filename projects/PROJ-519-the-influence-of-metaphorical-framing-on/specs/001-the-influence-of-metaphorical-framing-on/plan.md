# Implementation Plan: The Influence of Metaphorical Framing on Attitudes Towards Mental Health Treatment

**Branch**: `001-metaphor-framing-attitudes` | **Date**: 2026-08-13 | **Spec**: `specs/001-metaphor-framing-attitudes/spec.md`
**Input**: Feature specification from `specs/001-metaphor-framing-attitudes/spec.md`

## Summary

This feature implements a dual-stream research pipeline: (1) a controlled vignette experiment to measure the causal effect of metaphorical framing ("Battle", "Journey", "Medical") on stigma (CAMI scale) and help-seeking intent, and (2) a **Methodological Feasibility Demonstration** for the observational analysis component. 

**Critical Scope Note on US-2**: Due to the absence of a verified, open-access public mental health discourse corpus (e.g., Reddit posts) in the provided source list, the observational analysis (US-2) is **reframed** as a pipeline stress test. It uses a synthetic corpus to validate the *methodological logic* (regex extraction, VADER scoring, robust regression) and to verify the system's ability to correctly detect a **null correlation** (as expected from independent random variables) and a **known correlation** (in a stress-test subset). This component does **not** claim to answer the ecological research question regarding naturalistic discourse.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `vaderSentiment`, `seaborn`, `matplotlib`, `pytest`  
**Storage**: Local CSV/Parquet files under `data/` (raw and derived), checksummed.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational Research Pipeline (CLI/Script-based).  
**Performance Goals**: Complete data processing, modeling, and visualization within 6 hours; memory usage < 6 GB.  
**Constraints**: No GPU; no access to gated clinical datasets; VADER used strictly for polarity, not stigma; causal claims restricted to experimental arm.  
**Scale/Scope**: Simulated experimental data (N=159+); Discourse corpus (synthetic fallback for pipeline validation).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | Random seeds pinned in `code/`. Experimental data fetched from canonical HuggingFace sources (if available) or generated with pinned seeds. Synthetic data parameters stored in `config/simulation_config.yaml`. US-2 uses synthetic data (non-canonical source) but is versioned. | ✅ Plan Compliant (Experimental), ⚠️ Partially Compliant (US-2 Synthetic) |
| **II. Verified Accuracy** | Citations in `research.md` restricted to verified HuggingFace URLs provided in the spec context. No invented URLs. US-2 data source is synthetic (no external URL). | ✅ Plan Compliant (Experimental), ⚠️ Partially Compliant (US-2 Synthetic) |
| **III. Data Hygiene** | Raw data checksummed; derivations written to new files. No in-place modification. PII scan enabled. | ✅ Plan Compliant |
| **IV. Single Source of Truth** | All figures/stats trace to `data/` rows and `code/` blocks. No hand-typed numbers in output. | ✅ Plan Compliant |
| **V. Versioning Discipline** | Artifacts carry content hashes. State file updated on artifact change. Synthetic generator config pinned in `config/simulation_config.yaml` to ensure bit-for-bit reproducibility of synthetic data. | ✅ Plan Compliant |
| **VI. Linguistic Stimulus Integrity** | Vignette texts stored as immutable raw assets. Derived processed texts (if any) have distinct filenames. Original conditions preserved. | ✅ Plan Compliant |
| **VII. Psychometric Measurement Separation** | CAMI scores and sentiment scores stored as distinct columns/tables from stimulus metadata. Input text does not dictate output metric mechanically. | ✅ Plan Compliant |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-influence-of-metaphorical-framing-on/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── experimental-data.schema.yaml
│   ├── discourse-data.schema.yaml
│   └── statistical-result.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-519-the-influence-of-metaphorical-framing-on/
├── code/
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data_ingestion.py       # Download/stream discourse, load vignettes
│   │   ├── vignette_engine.py      # Generate experimental conditions
│   │   ├── sentiment_analysis.py   # VADER processing (with bias control)
│   │   ├── statistical_modeling.py # ANOVA, Robust Regression
│   │   └── visualization.py        # Plot generation
│   └── tests/
│       ├── test_vignette_engine.py
│       ├── test_sentiment.py
│       └── test_statistical_modeling.py
├── config/
│   └── simulation_config.yaml      # Pinned parameters for synthetic data
├── data/
│   ├── raw/                        # Downloaded discourse (if static), vignette templates
│   ├── processed/                  # Cleaned datasets with checksums
│   └── derived/                    # Model outputs, figures
└── state/
    └── projects/PROJ-519-the-influence-of-metaphorical-framing-on.yaml
```

**Structure Decision**: Single project structure with clear separation of `src` (logic), `data` (inputs/outputs), and `tests` (validation). This minimizes overhead for a research pipeline and aligns with the "CLI/Script-based" project type.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual-Stream Architecture** | The spec requires both a causal experiment (US-1) and an observational correlation (US-2). | Merging them would conflate experimental controls with observational noise, violating Principle VII (Psychometric Measurement Separation). |
| **Robust Regression (Huber-White)** | Discourse data often exhibits heteroscedasticity; OLS assumptions may be violated. | Standard OLS would produce biased standard errors, failing SC-002 and FR-006. |
| **Streaming/Sampling for Discourse** | Full Reddit corpora may exceed 7 GB RAM. | Loading full raw data would crash the runner. Streaming allows processing the *real* data without synthetic substitution (if available). |
| **Synthetic Fallback for US-2** | No verified open discourse corpus exists in the provided source list. | Using a real dataset is impossible without fabricating a URL. The synthetic fallback is a necessary deviation to test the pipeline logic and is explicitly documented as a scope reduction. |