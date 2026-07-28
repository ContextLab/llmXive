# Implementation Plan: Linguistic Accommodation and Speaker Emotional Intensity

**Branch**: `001-linguistic-accommodation-empathy` | **Date**: 2024-05-21 | **Spec**: [spec.md]
**Input**: Feature specification from `specs/001-the-impact-of-linguistic-accommodation-o/spec.md`

## Summary

This feature implements a computational pipeline to analyze the relationship between **linguistic accommodation** (lexical and syntactic similarity between adjacent dialogue turns) and **dialogue-level emotional intensity** in human-human dialogue. Using the **canonical DailyDialog** dataset, the system computes Jaccard similarity metrics for lexical overlap and POS-tag overlap between turns, assigns the dialogue-level emotion label to all turns within that dialogue, and performs robust statistical analysis (Spearman correlation, Ordinal Logistic Regression with dummy-coded covariates, bootstrap confidence intervals) to test the associational hypothesis. 

A critical **Phase 1 Validation** step is included: a small subset of dialogues (n=50) will be manually annotated by human raters for emotional intensity to validate the mapping rule (Joy=5, etc.) against ground truth. The pipeline adheres to strict data hygiene, reproducibility, and statistical validity principles defined in the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (for streaming HF data), `pandas`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `nltk` (for POS/dependency parsing), `pyyaml` (for config/contract loading), `scikit-posthocs` (for ordinal regression).  
**Storage**: Local `data/` directory (raw zip/parquet, processed CSV/JSON), `artifacts/` for plots/reports  
**Testing**: `pytest` (unit tests for metric computation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions CPU runner: 2 cores, 7GB RAM)  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Complete full analysis on DailyDialog (~13k dialogues) within 6 hours on CPU. Memory usage < 6GB.  
**Constraints**: No GPU required (CPU-tractable statistical methods). Must handle missing emotion labels gracefully.  
**Scale/Scope**: [deferred] dialogue pairs (DailyDialog test set), ~100k turns.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**:
  - **Pass**: Plan mandates pinned `requirements.txt`, random seed fixation in `code/`, and deterministic data fetching from verified HuggingFace URLs.
  - **Action**: Scripts will include `np.random.seed(42)` and `torch.manual_seed(42)` (if applicable, though none here).
- **II. Verified Accuracy**:
  - **Pass**: All dataset URLs are drawn from the verified list. Citations for statistical methods (e.g., Bonferroni, Cohen) will be validated against primary sources in `research.md`.
  - **Action**: The **Reference-Validator Agent** will run on `research.md` and `plan.md` artifacts before the `research_accepted` transition to ensure all citations are verified against primary sources.
- **III. Data Hygiene**:
  - **Pass**: Raw data will be downloaded to `data/raw/` and checksummed. Processed data will be written to `data/processed/` with new filenames. No in-place modification.
- **IV. Single Source of Truth**:
  - **Pass**: All statistics in the final report will be generated programmatically from `data/processed/` and stored in a machine-readable format (JSON/CSV) before being rendered to Markdown/PDF.
- **V. Versioning Discipline**:
  - **Pass**: Content hashes will be recorded in the state file upon artifact creation.
- **VI. Human Subject Ethics**:
  - **Pass**: The main analysis uses the public, anonymized DailyDialog corpus (no IRB required). 
  - **Action**: The **Phase 1 Validation** involves new human data collection (annotating 50 dialogues). This will be conducted under **IRB exemption criteria** (minimal risk, anonymized data, secondary analysis of public data) or with explicit informed consent from annotators. Anonymized responses will be stored in `data/processed/validation_ground_truth.csv` with no PII.
- **VII. Statistical Validity**:
  - **Pass**: Plan explicitly includes Bonferroni correction for multiple comparisons, bootstrap resampling for CIs, and pre-registered hypotheses (Spearman correlation vs. null). It also includes a Chi-Square Goodness-of-Fit test for literature grounding (FR-010).

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-linguistic-accommodation-o/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Static design schemas (Phase 1 output)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-391-the-impact-of-linguistic-accommodation-o/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters (uses pyyaml)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingestion.py       # DailyDialog download & parsing
│   │   └── preprocessing.py   # Normalization, metric computation
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── stats.py           # Correlation, regression, bootstrap
│   │   └── viz.py             # Plot generation
│   ├── models/
│   │   └── schemas.py         # Pydantic models for validation
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded DailyDialog files
│   ├── processed/             # Computed metrics CSVs
│   └── artifacts/             # Plots, reports
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (Option 1) is selected. The project is a linear data pipeline (Ingest -> Process -> Analyze -> Visualize) rather than a service or library with complex API boundaries. Separation into `data`, `analysis`, and `models` packages ensures modularity and testability while keeping the footprint small for CPU execution.

## Implementation Phases

### Phase 0: Data Ingestion & Preprocessing
1. Download canonical DailyDialog (test set) from verified HuggingFace source.
2. Parse dialogue turns and normalize text (Unicode NFKC).
3. Compute turn-level metrics: Lexical Overlap (Jaccard), Syntactic Similarity (POS Jaccard), Bigram Overlap, Positional Overlap.
4. Assign dialogue-level emotion label to all turns within the dialogue.
5. Output: `data/processed/turn_metrics.csv`.

### Phase 1: Validation & Ground Truth (FR-010)
1. **Literature Grounding**: Perform Chi-Square Goodness-of-Fit test comparing DailyDialog emotion distribution to ISEAR corpus distribution.
2. **Human Annotation**: Select a stratified random sample of dialogues. Annotate with multiple raters for 'Emotional Intensity' using a multi-point Likert scale..
3. **Validation**: Compute Krippendorff's Alpha. If Alpha >= 0.6, compute correlation between mapped scores and mean human ratings. If r < 0.3, flag mapping as invalid.
4. Output: `data/processed/validation_ground_truth.csv`, `validation_report.json`.

### Phase 2: Statistical Analysis
1. **Correlation**: Spearman rank correlation between accommodation metrics and emotional intensity.
2. **Regression**: Ordinal Logistic Regression (Proportional Odds Model) with accommodation metrics as predictors, emotion intensity as outcome, and one-hot encoded Topic (LDA) + Word Count as covariates.
3. **Bootstrap**: Resample multiple times to estimate confidence intervals for correlation coefficients.
4. **Sensitivity**: Compare POS-based metrics against dependency-parse-based metrics.
5. Output: `data/artifacts/correlation_report.json`, `regression_summary.json`.

### Phase 3: Visualization & Reporting
1. Generate scatter plots (Accommodation vs. Intensity) with regression lines and CI shading.
2. Generate effect size histograms.
3. Compile final report.
4. Output: `data/artifacts/*.png`, `final_report.md`.

## Success Criteria

- **SC-001**: The Spearman correlation coefficient between lexical overlap and emotional intensity is measured against the null hypothesis of zero correlation.
- **SC-002**: The stability of the correlation coefficient is measured against the 95% confidence interval derived from bootstrap iterations.
- **SC-003**: The effect size is considered significant if the confidence interval excludes the null value AND the lower bound exceeds a small effect threshold per Cohen.., OR if the one-sample test against 0.10 yields p < 0.05. (Note: Comparison to Giles r=0.15 removed due to construct mismatch).
- **SC-004**: The proportion of variance explained is measured using **McFadden's Pseudo-R2** from the Ordinal Logistic Regression model, as standard R-squared is not applicable to ordinal outcomes.
- **SC-005**: The false discovery rate is measured against a Bonferroni-corrected alpha threshold (0.05 / 4 = 0.0125).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |