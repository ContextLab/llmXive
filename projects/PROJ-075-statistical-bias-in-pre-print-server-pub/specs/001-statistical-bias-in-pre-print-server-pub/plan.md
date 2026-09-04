# Implementation Plan: Statistical Bias in Pre-Print Server Publication Trends

**Branch**: `001-statistical-bias-in-pre-print-server-pub` | **Date**: 2026-08-13 | **Spec**: `spec.md`

## Summary

This feature implements a reproducible, CPU-first pipeline to quantify statistical reporting bias between pre-print and peer-reviewed versions of the same study. The system matches papers via OpenAlex (using `datasets` library for streaming), extracts p-values and effect sizes from PDFs (handling inequalities as interval-censored data for general reporting and **incorporating them into p-curve estimation via survival analysis**), and performs **Tobit regression** (primary) and sensitivity sweeps. The pipeline is designed to run on a GitHub Actions free-tier runner (2 CPU, ~7GB RAM) using lightweight Python libraries (`requests`, `pandas`, `scipy`, `statsmodels`, `pdfplumber`, `datasets`, `lifelines`). The primary analysis **models sample size (N) as a covariate** rather than excluding pairs with >20% N increase, and **includes identical p-values** to measure the rate of correction. The initial CI run targets N=200 pairs, with a plan for chunked execution to reach N=1000 on a dedicated runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pandas`, `scipy`, `statsmodels`, `pdfplumber`, `numpy`, `tqdm`, `pyyaml`, `datasets`, `lifelines` (for survival/Tobit)  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `data/results/`); no external database.  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`), CPU-only.  
**Project Type**: Data pipeline / CLI research tool.  
**Performance Goals**: Process N=200 pre-print/journal pairs within 6 hours for CI (target match rate ≥ 80%); N=1000 on dedicated runner via chunked execution. Memory usage < 6GB during extraction.  
**Constraints**: No GPU; no external API keys (except public OpenAlex S3); strict reproducibility (random seeds pinned).  
**Scale/Scope**: Initial corpus: N=1000 pre-prints from arXiv/bioRxiv (2018–2023); target match rate ≥ 80% (minimum acceptable SC-001: ≥ 60%).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan enforces pinned `requirements.txt`, deterministic random seeds in `code/`, and re-fetching of OpenAlex metadata from the canonical S3 bucket on every run. No cached artifacts are assumed.
- **II. Verified Accuracy**: All citations in `research.md` and `paper/` will be validated by the Reference-Validator Agent against primary sources. Title overlap ≥ 0.7 required. **The Reference-Validator Agent runs as a blocking gate on the `research_review` -> `research_accepted` transition.**
- **III. Data Hygiene**: All files in `data/` will be checksummed (SHA-256) and recorded in `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml`. Raw data is immutable; derivations create new files.
- **IV. Single Source of Truth**: All figures and statistics in the final paper will trace to exactly one row in `data/processed/matched_pairs.csv` and one block in `code/analysis/`.
- **V. Versioning Discipline**: Every artifact under `code/`, `data/`, and `specs/` carries a content hash. The `state/` YAML file tracks `updated_at` timestamps for all changes. **A post-processing script `code/utils/update_state.py` will be invoked after each major step to update the `updated_at` timestamp in `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml`, ensuring it is the Single Source of Truth.**
- **VI. Paired-Artifact Integrity**: The `MatchedPaperPair` entity enforces a verified, immutable link between pre-print and journal versions via **DOI cross-checking against OpenAlex canonical source AND content hashing of the pair's metadata. Any pair without a confirmed DOI match or content hash is excluded from analysis, preventing cross-manuscript contamination.**
- **VII. Distributional Shift Quantification**: The analysis prioritizes effect sizes of the difference ($\Delta$ES) and density ratio magnitudes over binary p-value significance. Models output magnitude and direction of shift.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-bias-in-pre-print-server-pub/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Target artifact for the next stage (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-075-statistical-bias-in-pre-print-server-pub/
├── code/
│   ├── __init__.py
│   ├── config.py           # Paths, seeds, thresholds
│   ├── fetch/
│   │   ├── __init__.py
│   │   ├── openalex_loader.py  # OpenAlex S3/HTTP fetcher (using datasets)
│   │   └── arxiv_biorxiv_scraper.py # Pre-print metadata scraper
│   ├── match/
│   │   ├── __init__.py
│   │   └── fuzzy_matcher.py    # Title/author similarity matching + DOI verification
│   ├── extract/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py       # PDF text extraction & regex parsing
│   │   └── stats_extractor.py  # P-value & effect size extraction
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── p_curve.py          # P-curve analysis (including censored data via survival analysis)
│   │   ├── effect_size.py      # Tobit regression, weighted t-test
│   │   └── sensitivity.py      # Threshold sweep
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging & error handling
│       └── update_state.py     # Updates state YAML timestamps
├── data/
│   ├── raw/
│   │   ├── openalex_metadata/
│   │   ├── arxiv_metadata/
│   │   └── biorxiv_metadata/
│   ├── processed/
│   │   └── matched_pairs.csv
│   └── results/
│       ├── p_curve_results.json
│       ├── effect_size_results.json
│       └── sensitivity_results.json
├── tests/
│   ├── unit/
│   │   ├── test_fuzzy_matcher.py
│   │   └── test_stats_extractor.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schema_validation.py
├── requirements.txt
└── README.md
```

**Structure Decision**: The single-project structure is selected to minimize overhead. The `code/` directory is modularized by function (fetch, match, extract, analysis) to support independent testing and reproducibility. The `data/` directory follows the raw/processed/results hierarchy to ensure data hygiene.

## Complexity Tracking

No complexity violations detected. The pipeline is linear: fetch → match → extract → analyze. No parallel processing is required for the initial N=200 sample size for CI, and the CPU-first design ensures feasibility within the GitHub Actions limits.

## Methodology

### 1. Matched Dataset Construction
- **Input**: List of pre-print IDs (arXiv/bioRxiv) from 2018–2023.
- **Process**: 
  1. Fetch pre-print metadata via APIs.
  2. Query OpenAlex (streamed) to find matching journal DOIs using fuzzy title/author similarity (threshold ≥ 0.9).
  3. **Secondary Verification**: Cross-reference the match against the OpenAlex canonical DOI for the pre-print ID (if available) to confirm the match. Matches without a DOI or with low canonical confidence are flagged for exclusion.
  4. Filter to pairs where the journal version is within 2 years of the pre-print.
  5. **Exclude case studies, theoretical papers, and pairs where the primary statistical method changes** (specifically tracking t-test, ANOVA, Chi-square, Regression, and Wilcoxon methods).
- **Output**: `matched_pairs.csv` with columns: `preprint_id`, `journal_doi`, `title`, `authors`, `preprint_date`, `journal_date`, `match_score`, `doi_verified`.
- **Target**: N=1000 pre-prints queried to achieve ≥ 80% match rate (SC-001).

### 2. Statistical Metric Extraction
- **Input**: PDFs of pre-print and journal versions (Open Access only via Unpaywall/CORE).
- **Process**:
  1. Extract text from PDFs using `pdfplumber`.
  2. Parse p-values (exact and inequalities) and effect sizes (Cohen's d, Hedges' g, odds ratios, etc.) using regex and context-aware NLP.
  3. Handle inequalities as interval-censored data (e.g., `p < 0.05` → `[0, 0.05]`) for general reporting.
  4. **P-Curve Inclusion**: Incorporate interval-censored p-values into p-curve estimation using survival analysis techniques (e.g., Turnbull estimator) rather than discarding them.
  5. **Include identical p-values** to measure the rate of correction (zero change).
  6. **Flag pairs where N increases by > 20%** (FR-006) but **do not exclude** them from the primary analysis; instead, model N as a covariate.
- **Output**: `extracted_metrics.csv` with columns: `pair_id`, `version` (preprint/journal), `metric_type`, `value`, `inequality_flag`, `interval_bounds`, `stat_method`, `n_sample`.

### 3. Distributional & Magnitude Analysis
- **P-Curve Analysis**: Perform separate p-curve analyses on pre-print and journal p-values (including censored values via survival analysis). Compare the estimated power and p-hacking prevalence parameters. **Compare findings against meta-analytic consensus or replication studies where available for independent validation.**
- **Effect Size Comparison**: Calculate $\Delta$ES = ES_journal - ES_preprint.
  - **Primary Method**: Use **Tobit regression** (via `lifelines` or `statsmodels`) to handle censored effect sizes and account for heteroscedasticity due to changing N. **Model N as a covariate.**
  - **Stratified Analysis**: Perform stratified analysis by research field (e.g., Quantitative Biology) as required by US-2.
- **Null Distribution**: Generate a null distribution for the density ratio via **permutation testing** (shuffling venue labels) to validate observed shifts (SC-002).
- **Output**: `p_curve_results.json`, `effect_size_results.json` with test statistics, p-values, and confidence intervals.

### 4. Sensitivity Analysis
- **Input**: Extracted p-values.
- **Process**: Sweep significance thresholds across conventional levels. Calculate "significance flip rate" (proportion of pairs where p crosses the threshold in opposite directions) at each threshold.
- **Robustness Check**: Account for **reporting precision artifacts** (e.g., rounding differences) in the flip rate calculation.
- **Direction Consistency**: Explicitly check that the **direction of the bias** (pre-print > journal or vice versa) remains consistent across all thresholds (SC-004).
- **Output**: `sensitivity_results.json` with flip rates and bias direction consistency.