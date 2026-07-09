# Implementation Plan: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Branch**: `001-self-compassion-feedback` | **Date**: 2026-06-28 | **Spec**: `specs/001-self-compassion-feedback/spec.md`
**Input**: Feature specification from `/specs/001-self-compassion-feedback/spec.md`

## Summary

This feature implements a rigorous statistical pipeline to test whether self-compassion (SCS) buffers the adverse psychological impact of negative feedback on anxiety, rumination, and self-efficacy. The approach involves downloading a verified OSF dataset, performing strict data validation (column presence, sample size power check), cleaning (listwise deletion), and fitting ANCOVA models with interaction terms. The pipeline includes robustness checks (VIF, bootstrap, alternative moderators), generates simple-slope visualizations, and produces a comprehensive HTML report.

**Critical Data Contingency**: The hypothesis requires an experimental dataset with feedback manipulation and pre/post outcomes. The OSF ID `3k9r2` is the *only* identified source. The pipeline is designed as a **Conditional Validation Pipeline**: if this specific source is unavailable or lacks required columns, the system **MUST** abort immediately with a specific error code. No alternative datasets are used, as they lack the necessary experimental design, preventing the execution of a "zombie" experiment.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `seaborn`, `matplotlib`, `requests`, `pyyaml`, `jinja2`.
**Storage**: Local filesystem (`data/` for raw/cleaned CSVs, `output/` for plots and HTML).
**Testing**: `pytest` (unit tests for data validation, integration tests for pipeline execution).
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).
**Project Type**: Computational research pipeline (CLI-based).
**Performance Goals**: Complete full analysis (download, clean, model, plot, report) within 45 minutes on free-tier CPU.
**Constraints**: 
- NO GPU usage.
- NO large model training.
- Memory footprint < 4 GB during peak execution.
- Strict adherence to FR-001 (column check) and FR-017 (randomization check).
- All stochastic operations seeded with a fixed value to ensure reproducibility.

### Data Availability Protocol (Hard Gate)
The pipeline enforces a strict "Data First" protocol:
1.  **Fetch**: Attempt to download `https://osf.io/3k9r2/`.
2.  **Verify**: Check for HTTP 200 and presence of required columns (`stai_post`, `rrs_post`, `gse_post`, `scf_total`, `feedback_cond`).
3.  **Abort on Failure**: If the file is missing, inaccessible, or columns are absent, the pipeline **MUST** exit with code 1 and the exact error message: `[DATA_UNAVAILABLE: Required columns missing from dataset. Expected: [list of missing columns]]` or `[DATA_UNAVAILABLE: Dataset source unreachable or missing. The pipeline cannot proceed.]`.
4.  **No Substitution**: The pipeline does **NOT** attempt to fetch alternative datasets (e.g., SCS-only datasets) as they cannot test the feedback moderation hypothesis. This aligns with Constitution Principle II (Verified Accuracy) by ensuring no results are generated from unverified or unsuitable data sources.

### Randomization Verification Mechanism
To satisfy FR-017, the `data_loader.py` script performs the following:
1.  Fetches `README.md` and `metadata.json` from the OSF repository alongside the CSV.
2.  Parses these files for keywords: "randomized", "experimental", "random assignment", "between-subjects".
3.  **Logic**:
    - If keyword found: Set `randomization_confirmed = True`.
    - If files missing or keywords absent: Set `randomization_confirmed = False`.
4.  **Reporting**: The final report explicitly states "Findings are **Associational**" if `randomization_confirmed` is False, and "Findings are **Causal**" only if True.

### Bootstrap Convergence Criteria & Time Budget
To ensure computational feasibility on CPU:
1.  **Primary Run**: 5,000 resamples (seed=42).
2.  **Convergence Metric**: Coefficient of Variation (CV) of the standard error across the last multiple resamples.
    - **Pass**: CV < 0.05.
    - **Retry**: If CV >= 0.05, retry with 2,000 resamples.
3.  **Fallback**: If CV >= 0.05 after 2,000 resamples, log a warning `[BOOTSTRAP_CONVERGENCE_WARNING: Using parametric CIs due to instability]` and proceed with parametric CIs.
4.  **Hard Timeout**: The modeling phase has a fixed time limit. If exceeded, the pipeline aborts with `[TIMEOUT: Modeling phase exceeded 30 mins]`.

> **Dataset Fit Note**: The "Verified datasets" block provided in the prompt **does not** contain a verified URL for OSF ID `3k9r2`. The plan explicitly acknowledges this gap. The pipeline relies *exclusively* on this OSF source. If the source is missing, the project halts. This is a deliberate design choice to prevent invalid analysis on unsuitable data.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` with pinned versions, seed=42, and deterministic OSF fetch with checksum. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will only reference the OSF source (if accessible) or standard psychometric literature. No fabricated URLs. Pipeline aborts if data is unverified. |
| **III. Data Hygiene** | **PASS** | FR-016 mandates SHA-256 checksum of raw data. Raw data preserved; cleaned data written to new file. |
| **IV. Single Source of Truth** | **PASS** | Report will dynamically pull stats from the `AnalysisResult` object, not hardcoded values. |
| **V. Versioning Discipline** | **PASS** | Plan includes state file update logic for artifact hashes. |
| **VI. Validated Instruments** | **PASS** | Spec confirms use of SCS, STAI, RRS, GSES (all validated). Plan will verify column names match these instruments. |
| **VII. Participant Well‑Being** | **WARN** | The dataset is historical; the pipeline cannot verify pre-screening or debriefing for every record. The report **MUST** explicitly flag this as a limitation ("Participant Well-Being protocols could not be verified for this historical dataset") rather than claiming full compliance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-self-compassion-feedback/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Existing design artifacts (referenced, not generated here)
│   ├── dataset.schema.yaml
│   └── analysis_output.schema.yaml
└── tasks.md             # (Generated in next stage if needed)
```

### Source Code (repository root)

```text
projects/PROJ-167-the-impact-of-self-compassion-on-resilie/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, thresholds
│   ├── data_loader.py         # OSF fetch, checksum, validation, randomization check
│   ├── preprocessing.py       # Cleaning, z-scoring, encoding
│   ├── models.py              # ANCOVA, VIF, Bootstrap, Robust SEs
│   ├── visualization.py       # Simple slopes
│   ├── robustness.py          # Sensitivity, alternative moderator
│   ├── report_generator.py    # HTML generation
│   └── main.py                # Orchestration
├── data/
│   ├── raw/                   # Downloaded CSV (checksummed)
│   └── processed/             # Cleaned CSV
├── output/
│   ├── plots/                 # PNGs
│   └── report.html
├── tests/
│   ├── test_data_loader.py
│   └── test_models.py
├── requirements.txt
└── state/
    └── projects/PROJ-167-...yaml
```

**Structure Decision**: Single project structure with modular scripts in `code/`. This minimizes overhead for CPU-only execution and simplifies dependency management on GitHub Actions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Bootstrap (5000 resamples)** | Required by FR-008 for robust CI estimation of interaction terms in small samples. | Parametric CIs alone are insufficient for non-normal residuals; bootstrap is the standard for robust inference here. Fallback to parametric only if convergence fails. |
| **HC3 Robust SEs** | Required by FR-009 to handle heteroskedasticity (Breusch-Pagan check). | Standard OLS SEs would be biased if heteroskedasticity is present, violating FR-006. |
| **Holm-Bonferroni** | Required by FR-011 for multiple comparisons (3 outcomes + 1 robustness). | Bonferroni is too conservative; Holm-Bonferroni maintains power while controlling FWER. |
| **Hard Data Gate** | Required to prevent "zombie" experiments on missing/unsuitable data. | Running on proxy datasets would invalidate the hypothesis (feedback manipulation). |

## Scientific Validity Gate

The pipeline explicitly acknowledges that the research question (moderation of *feedback* impact) is **untestable** without the specific experimental dataset.
- **If OSF 3k9r2 is available**: Proceed with full analysis.
- **If OSF 3k9r2 is missing**: Abort with `[DATA_UNAVAILABLE]`. This is a valid scientific outcome indicating the hypothesis cannot be tested with current resources.
- **No Alternative Path**: The plan does not reframe the question to match available data (e.g., correlational only) because the specific hypothesis requires the experimental manipulation.
