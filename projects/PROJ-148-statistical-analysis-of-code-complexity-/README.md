# Statistical Analysis of Code Complexity Metrics and Bug Prediction

A reproducible research pipeline to analyze the relationship between code complexity metrics and bug-proneness in Java projects.

## Overview

This project implements a complete data science pipeline to:
1. Download and process Java source code from GHTorrent
2. Extract complexity metrics using lizard
3. Label bug-fix occurrences
4. Perform statistical modeling and feature selection
5. Evaluate model performance and generate insights

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full data pipeline
python code/data/pipeline.py

# Run the modeling pipeline
python code/modeling/pipeline.py

# Generate the research report
python code/report/generate_report.py
```

## Implementation Strategy

This section maps high-level research steps to specific task IDs in the project.

### Phase 0: Contracts & Schemas (Foundational Artifacts)
- **T040**: Create dataset contract schema (`contracts/dataset.schema.yaml`)
- **T041**: Create model output contract schema (`contracts/model_output.schema.yaml`)
- **T042**: Author data-model design document (`data-model.md`)
- **T043**: Write quickstart guide (`quickstart.md`)
- **T044**: Update Implementation Strategy section to map high-level steps to task IDs (`README.md`)
- **T045**: Contract test for bug-label reliability validation script (`tests/contract/test_bug_label_validation.py`)

### Phase 1: Setup (Shared Infrastructure)
- **T001**: Create project directory layout
- **T002**: Initialize Python 3.11 project with pinned dependencies
- **T003**: Configure linting and formatting tools

### Phase 2: Foundational (Blocking Prerequisites)
- **T004**: Configuration module with random seed handling
- **T005**: Reusable logging utility
- **T006**: Helper for reproducible data-hashing and checksum verification
- **T050**: Fallback handling for lizard parse failures
- **T051**: Memory-aware, chunked processing of source files

### Phase 3: User Story 1 – Data Acquisition and Preprocessing
- **T010**: Download GHTorrent Java project list and archives
- **T011**: Extract Java source files and commit metadata
- **T012**: Compute complexity metrics with lizard
- **T013**: Label bug-fix vs. non-bug-fix units
- **T014**: Validate bug labels for reliability
- **T015**: Preprocess: impute missing values, log-transform, remove rows
- **T016**: Perform project-level stratified train/test split
- **T017**: Validate each project appears in only one split
- **T049**: Integrate bug-label reliability validation into pipeline
- **T052**: Document split proportions in pipeline configuration
- **T008**: Contract test for dataset schema
- **T009**: Integration test for end-to-end data pipeline

### Phase 4: User Story 2 – Statistical Modeling and Metric Selection
- **T053**: Perform collinearity diagnostics (VIF)
- **T054**: Contract test for collinearity diagnostics output
- **T020**: Train primary L1-logistic regression model
- **T021**: Train alternative Random Forest model
- **T022**: Extract and store coefficient vectors/feature importances
- **T023**: Compare model performance and compute Spearman correlation
- **T024**: Persist model artifacts and evaluation metrics
- **T018**: Contract test for model output schema
- **T019**: Integration test for training pipeline

### Phase 5: User Story 3 – Evaluation, Inference, and Reporting
- **T028**: Evaluate ROC-AUC, PR-AUC, and calibration plots
- **T029**: Apply Benjamini-Hochberg correction for multiple hypothesis testing
- **T030**: Generate partial dependence plots for top 3 metrics
- **T031**: Derive practical threshold values
- **T032**: Assemble research report with tables, plots, and interpretation
- **T025**: Contract test for evaluation metrics
- **T026**: Contract test for baseline ROC-AUC
- **T027**: Contract test for FDR after correction

### Phase N: Polish & Cross-Cutting Concerns
- **T033**: Update README with usage instructions
- **T034**: Add detailed documentation for each pipeline stage
- **T035**: Code cleanup and refactoring
- **T055**: Run black formatting
- **T056**: Run flake8 linting
- **T057**: Remove dead code
- **T036**: Add unit tests for utility modules
- **T037**: Cache lizard metric results
- **T038**: Security hardening with checksum verification
- **T039**: Run full test suite with coverage enforcement

## Data Sources

- **GHTorrent**: Java project archives downloaded from GHTorrent mirrors
- **Lizard**: Code complexity metrics extracted using the lizard library

## Output Artifacts

- `data/processed/bug_complexity_dataset.csv`: Preprocessed dataset
- `data/splits/train.csv`, `data/splits/test.csv`: Stratified train/test splits
- `data/model/primary.pkl`, `data/model/alternative.pkl`: Trained model artifacts
- `data/model/corrected_pvalues.csv`: BH-corrected p-values
- `figures/pdp_*.png`: Partial dependence plots
- `report/research_report.pdf`: Final research report

## Reproducibility

All random seeds are controlled via `code/utils/config.py`. Run with:
```bash
python code/utils/config.py --seed 42
```

Checksums for downloaded archives are verified using `code/utils/checksum.py`.

## License

This project is licensed under the MIT License.