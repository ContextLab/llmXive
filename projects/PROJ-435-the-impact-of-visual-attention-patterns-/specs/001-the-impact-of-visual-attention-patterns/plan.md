# Implementation Plan: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

**Branch**: `001-impact-of-visual-attention-patterns` | **Date**: 2026-07-08 | **Spec**: `specs/001-impact-of-visual-attention-patterns/spec.md`
**Input**: Feature specification from `specs/001-impact-of-visual-attention-patterns/spec.md`

## Summary

This project implements a reproducible statistical analysis pipeline to test the hypothesis that visual attention patterns (fixation duration on source attribution) interact with headline emotional valence and cognitive reflection scores to predict susceptibility to misleading headlines. The pipeline ingests raw eye-tracking data, applies I-VT fixation detection, calculates valence using the NRC/VADER lexicons, and executes a mixed-effects regression model with multiple-comparison correction. The implementation prioritizes CPU-feasibility on GitHub Actions free-tier runners while ensuring strict adherence to the project constitution regarding data hygiene, reproducibility, and causal framing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `datasets` (Hugging Face), `nltk`, `pyyaml`, `ruff`, `pytest`, `vaderSentiment`  
**Storage**: Local file system (`data/raw/`, `data/derived/`, `data/processed/`)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data Science Pipeline / Statistical Analysis  
**Performance Goals**: Complete pipeline execution within 300 minutes (5 hours) on 2 CPU cores, 7 GB RAM.  
**Constraints**: No local GPU; data must be streamable or sampleable to fit memory; strict adherence to FR-001 through FR-007 and SC-001 through SC-005.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds will be pinned in `code/` scripts. External datasets will be fetched via `datasets.load_dataset` with explicit versioning. `requirements.txt` pins all dependencies.
- **II. Verified Accuracy**: All dataset references in `research.md` will cite ONLY the URLs provided in the "Verified datasets" block. No fabricated URLs.
- **III. Data Hygiene**: All files in `data/` will be checksummed (SHA-256) upon ingestion. No in-place modifications; derivations create new files. PII scan will be run on `data/` before commit. **Task**: "Checksum Data" and "Run PII Scan" are explicitly mapped to pipeline steps.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated directly from `data/processed/` outputs. No hand-typed numbers.
- **V. Versioning Discipline**: Every artifact will carry a content hash. The `state/` directory will track `updated_at` timestamps for all artifacts.
- **VI. Multi-Modal Data Integrity**: Gaze data (predictor) and belief ratings (outcome) will be processed in separate streams and merged only at the analysis stage to prevent circular computation of belief from gaze. **Prohibition**: Synthetic generation of belief ratings is strictly prohibited.
- **VII. Outcome-Neutral Validation**: The analysis protocol will be defined a priori to treat null results as informative. No post-hoc "p-hacking" or threshold sweeping to achieve significance.

## Project Structure

### Documentation (this feature)

```text
specs/001-impact-of-visual-attention-patterns/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── models/              # Participant, Stimulus, GazeEvent classes
├── services/            # Preprocessing, ValenceCalculation, Regression
├── cli/                 # Entry points for pipeline stages
└── lib/                 # Utility functions (logging, checksumming)

tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests
└── unit/                # Unit tests for services

data/
├── raw/                 # Ingested raw data (checksummed)
├── derived/             # Intermediate derived data (merged, filtered)
└── processed/           # Final analysis-ready datasets

state/
└── artifacts.yaml       # Hashes and timestamps
```

**Structure Decision**: The single-project structure (Option 1) is selected because the scope is a contained statistical analysis pipeline. The separation of `data/` into `raw`, `derived`, and `processed` enforces the Data Hygiene principle (Constitution III). The `src/` layout separates models, services, and CLI to ensure modularity and testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-Effects Regression | Required by FR-004 to account for random intercepts (participants, headlines) | Standard OLS regression would violate statistical assumptions due to non-independence of observations within participants and stimuli. |
| Single-Tool Valence (VADER fallback) | Required by FR-003 to handle low coverage without introducing a confound | Dual-lexicon fallback (NRC then VADER) creates a systematic confound correlated with headline complexity. |
| Robustness Sweep (/100/150ms) | Required by FR-005 to ensure findings are not artifacts | Single threshold analysis would fail to demonstrate robustness, violating FR-005 and SC-003. |
| Runtime Measurement | Required by SC-005 to ensure feasibility | Without explicit measurement, the 300-minute limit cannot be verified. |
| Headline Length Control | Required by FR-005 (US-3) to control for stimulus complexity | Omitting this control would leave a confound between headline length and belief susceptibility. |

## Pipeline Tasks

### Phase 0: Data Ingestion & Hygiene
- **T001**: Fetch dataset from verified source (Misleading Headlines Eye-Tracking).
- **T002**: **Checksum Data**: Calculate SHA-256 hash of raw data and record in `state/`.
- **T003**: **Run PII Scan**: Scan `data/raw/` for PII. Fail if found.
- **T004**: **Construct Validity Gate**: Verify dataset contains `headline_text`, `belief_rating`, `cognitive_reflection_score`, `fixation_duration`, AND pre-defined ROI bounding boxes (specifically "source_attribution" and "headline_body"). If ROI definitions are missing, halt and log error.

### Phase 1: Preprocessing
- **T005**: Apply I-VT fixation detection (threshold-based).
- **T006**: Filter participants with >20% data loss.
- **T007**: **Data Quality Report**: Generate summary of excluded participants (SC-001).
- **T008**: **ROI Mapping**: Map gaze points to ROIs using verified bounding boxes. Log warnings for missing coordinates. If "source_attribution" ROI is missing for a trial, exclude that trial but retain valid trials.

### Phase 2: Valence Calculation
- **T009**: Calculate valence using NRC lexicon.
- **T010**: If NRC coverage < 50%, switch to VADER for **ALL** headlines.
- **T011**: **Log Switch**: Record lexicon switch event in `output/runtime.log` and structured output.

### Phase 3: Analysis
- **T012**: Merge datasets (gaze, valence, cognitive reflection).
- **T013**: Calculate `total_fixation_duration` (sum of all fixations) and `headline_length` (word count).
- **T013b**: **Control Variable Check**: Ensure `total_fixation_duration` and `headline_length` are defined for all rows. If `total_fixation_duration` is missing due to ROI mapping issues, calculate it from raw gaze points before ROI filtering.
- **T014**: Run mixed-effects regression with fixed effects: source fixation duration, valence, cognitive reflection, `total_fixation_duration` (control), `headline_length` (control), and three-way interaction. Random intercepts for `Participant_ID` and `Headline_ID`.
- **T015**: Apply Holm-Bonferroni correction.
- **T016**: **Generate Causal Framing Statement**: Explicitly frame findings as causal or associational based on dataset design (FR-006).
- **T017**: **Measure Runtime**: Record wall-clock time and compare to 300-minute limit (SC-005).

### Phase 4: Robustness
- **T018**: Sweep fixation duration cutoffs (low, medium, high). **Reset random seed to fixed value before each iteration.**
- **T019**: **Stability Check**: Verify coefficient sign and CI overlap across thresholds.

## Success Criteria Verification

- **SC-001**: Verified by T007 (Data Quality Report).
- **SC-002**: Verified by T014 (Regression output).
- **SC-003**: Verified by T019 (Robustness analysis).
- **SC-004**: Verified by T015 (Multiple comparison correction) and output schema field.
- **SC-005**: Verified by T017 (Runtime measurement).

## Notes on Removed Content

- **Phase 6 (WYSIATI metrics)**: Removed. The specification (FR-004) strictly defines the fixed effects as source fixation duration, valence, and cognitive reflection. Introducing synthetic "confidence_score" or "override_time" variables contradicts the spec and violates Constitution Principle VI (Multi-Modal Data Integrity) by creating circular dependencies between predictors and outcomes.
- **Synthetic Data Generation for Outcome**: Removed. The outcome variable (`belief_rating`) must be empirical. Synthetic generation of belief ratings based on fixation data is prohibited to prevent circularity.