# Implementation Plan: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2024-05-21 | **Spec**: `specs/001-visual-salience-moral-judgments/spec.md`
**Input**: Feature specification from `specs/001-visual-salience-moral-judgments/spec.md`

## Summary

This project implements a computational pipeline to investigate whether enhancing the visual salience (luminance contrast/brightness) of target objects in morally ambiguous scenarios influences participants' blame ratings. The technical approach involves: (1) **Manual Curation** of text-based morally ambiguous scenarios, (2) **Image Generation/Selection** to visualize these scenarios, (3) **Salience Manipulation** of target regions, (4) **Human Validation** of ambiguity and narrative preservation, (5) **Survey Deployment** (Pilot Mode), and (6) **Statistical Analysis** using Linear Mixed-Effects Models (LMM) with Marginal/Conditional R².

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pillow`, `torch` (CPU-only), `transformers`, `diffusers` (CPU), `opencv-python`, `simr` (or `statsmodels.stats.power`)  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/results`), CSV/Parquet formats  
**Testing**: `pytest` (unit tests for manipulation logic, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU)  
**Project Type**: Computational research pipeline (data processing, experimental design, statistical analysis)  
**Performance Goals**: Full pipeline execution ≤ 6 hours; image manipulation ≤ 500ms per image; statistical analysis ≤ 30 mins for N=100 participants  
**Constraints**: No GPU usage; memory footprint < 6 GB; dataset subset to a representative range of scenarios; **No external API calls for survey** (local deployment or simulated data for testing)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All scripts will pin random seeds (`numpy.random.seed`, `torch.manual_seed`). External datasets will be fetched via verified HuggingFace URLs. `requirements.txt` will pin exact versions.
- **II. Verified Accuracy**: Citations in `research.md` will strictly adhere to the "Verified datasets" block provided in the prompt. No fabricated URLs. **Note**: The primary data source is now "Manual Curation" (text narratives), which does not require a URL, thus adhering to the block by not violating it.
- **III. Data Hygiene**: Raw data (curated text, generated images) will be stored in `data/raw` with checksums. Manipulated images and analysis results will be written to new files in `data/processed` and `data/results` respectively. No in-place modifications.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated programmatically from `data/results` and `code/` outputs. No hand-typed numbers.
- **V. Versioning Discipline**: **Any change to the data model entities (Scenario, Stimulus Variant, Response) or their attributes will trigger a state file update.** Artifacts will carry content hashes. The `state` file will be updated upon artifact changes.
- **VI. Stimulus-Control Integrity**: Image manipulation scripts will explicitly log contrast/brightness parameters and verify semantic preservation via CLIP cosine similarity (≥ 0.95) **AND** a separate **Human Manipulation Check** (≥80% agreement on narrative preservation). Results of these checks are stored in `data/processed/stimuli/stimuli_manifest.csv`.
- **VII. Behavioral Response Validation**: Survey data structure will link each response to the specific stimulus version (image ID, salience level) to ensure distinct predictor/predicted sources.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-salience-moral-judgments/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-507-the-influence-of-visual-salience-on-mora/
├── code/
│   ├── 01_data_curation.py         # Manual curation of text narratives & image selection/generation
│   ├── 02_human_coding.py          # Script for human ambiguity coding (real or simulation mode)
│   ├── 03_salience_manipulation.py # Luminance contrast/brightness enhancement
│   ├── 04_manipulation_check.py    # Pilot human check for narrative preservation (separate panel)
│   ├── 05_survey_deployment.py     # Survey logic (randomization, data collection)
│   ├── 06_data_cleaning.py         # Straight-lining detection, variance checks
│   ├── 07_statistical_analysis.py  # LMM, Bonferroni correction, R² effect sizes
│   ├── 08_power_analysis.py        # A priori & post-hoc power analysis (G*Power equivalent)
│   └── 09_report_generation.py     # Generate final report with figures
├── data/
│   ├── raw/                        # Curated text narratives, source images
│   ├── processed/                  # Manipulated images, metadata, validation metrics
│   └── results/                    # Survey responses, analysis outputs
├── tests/
│   ├── test_manipulation.py        # Verify CLIP similarity, RMS contrast
│   └── test_analysis.py            # Verify LMM output on synthetic data
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) chosen for simplicity and alignment with computational research workflows. This avoids unnecessary complexity of web-service or mobile-app structures, focusing on the data pipeline and statistical analysis.

## Phase Definition

### Phase 0: Research & Design
- **Goal**: Validate dataset strategy and power analysis.
- **Output**: `research.md`, `data-model.md`, `quickstart.md`, `contracts/`.
- **Key Task**: Perform **A Priori Simulation-Based Power Analysis** to determine required N.

### Phase 1: Data Curation & Stimulus Generation
- **Goal**: Create a set of morally ambiguous scenarios with manipulated variants.
- **Output**: `data/raw/scenarios.csv`, `data/processed/stimuli/`.
- **Key Task**: Manual curation of text narratives; Image generation/selection; Salience manipulation.

### Phase 2: Human Validation (Pilot)
- **Goal**: Confirm ambiguity and narrative preservation.
- **Output**: `data/processed/human_codes/ambiguity.csv`, `data/processed/human_codes/narrative_check.csv`.
- **Key Task**: Recruit ≥3 annotators for ambiguity; Recruit separate panel for narrative check (≥80% agreement).

### Phase 3: Survey Deployment (Pilot Mode)
- **Goal**: Collect blame ratings from N=60-100 participants.
- **Output**: `data/processed/survey_responses.csv`.
- **Key Task**: Deploy survey with randomized within-subject design.

### Phase 4: Analysis & Reporting
- **Goal**: Test hypothesis and generate report.
- **Output**: `data/results/analysis_output.json`, `data/results/report.md`.
- **Key Task**: LMM analysis with R²; Bonferroni correction; Post-hoc power analysis; Precision threshold check (CI width ≤ 0.3).

## Execution Modes

- **Simulation Mode**: Uses synthetic data (random ratings) to test pipeline logic (randomization, cleaning, analysis). **Not for scientific claims.**
- **Pilot Mode**: Uses real human data collected via the survey. **Required for scientific claims.**
- **Default**: The pipeline defaults to Simulation Mode for CI testing. Pilot Mode is triggered by a configuration flag and requires a priori power analysis completion.

## Complexity Tracking

No violations of the Constitution Check were identified that require complex justifications. The chosen structure is minimal and sufficient for the project's scope.