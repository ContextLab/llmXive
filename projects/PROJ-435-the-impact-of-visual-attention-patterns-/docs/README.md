# The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Project Overview
This project implements an automated scientific pipeline to investigate how visual attention patterns (specifically fixation duration on source attribution vs. headline body) interact with headline valence and cognitive reflection scores to predict belief ratings of potentially misleading headlines.

## Pipeline Architecture

The pipeline is organized into the following phases:

### Phase 1: Setup
- Project structure initialization (`code/`, `data/`, `tests/`, `state/`)
- Python environment configuration with required dependencies
- Linting and formatting tool setup

### Phase 2: Foundational Infrastructure
- **Data Ingestion**: Fetches real eye-tracking data from the Dundee Eye-Tracking Corpus
- **Schema Validation**: Verifies required columns and ROI definitions
- **Logging Configuration**: Global logger setup with audit trails
- **Fixation Detection**: Implements I-VT (I-VT) algorithm with configurable thresholds
- **ROI Mapping**: Assigns gaze points to defined regions of interest

### Phase 3: User Story 1 - Core Data Preprocessing
- Ingests raw eye-tracking data
- Applies fixation detection algorithms
- Filters low-quality participants (>20% data loss)
- Maps gaze points to ROIs (source_attribution, headline_body)
- Generates data quality reports

### Phase 4: User Story 2 - Mixed-Effects Regression Analysis
- Merges preprocessed gaze data with empirical outcomes and valence scores
- Applies outlier capping to cognitive reflection scores
- Fits mixed-effects regression model:
 `belief_rating ~ fixation_duration * valence * crt + headline_length + total_fixation_duration + (1|participant_id) + (1|headline_id)`
- Applies Holm-Bonferroni correction to primary hypothesis family
- Validates coefficient recovery on synthetic data

### Phase 5: User Story 3 - Robustness and Sensitivity Analysis
- Executes threshold sweep across multiple fixation durations (50ms, 100ms, 150ms)
- Verifies stability of three-way interaction term across thresholds
- Generates robustness report with consistency metrics

### Phase N: Final Reporting and Documentation
- Generates causal framing statements from regression results
- Updates documentation with final study scope
- Validates quickstart execution
- Verifies artifact checksums

## Directory Structure

```
PROJ-435-the-impact-of-visual-attention-patterns-/
├── code/ # Main pipeline scripts
│ ├── 01_extract_empirical_outcome.py
│ ├── 01_ingest_and_preprocess.py
│ ├── 02_data_quality_report.py
│ ├── 02_preprocess_gaze.py
│ ├── 03_data_merge.py
│ ├── 03_valence_calculation.py
│ ├── 04_data_merge.py
│ ├── 05_regression_analysis.py
│ ├── 05_synthetic_data_generator.py
│ ├── 06_apply_holm_correction.py
│ ├── 06_generate_regression_results.py
│ ├── 06_measure_runtime.py
│ ├── 07_generate_causal_framing.py
│ ├── 07_stability_check.py
│ ├── 07_verify_interaction_consistency.py
│ ├── 08_verify_artifacts_checksums.py
│ ├── 09_performance_optimization.py
│ ├── config/
│ │ ├── config.yaml
│ │ └── logging_config.yaml
│ ├── models/
│ │ ├── gaze_event.py
│ │ ├── participant.py
│ │ └── stimulus.py
│ ├── utils/
│ │ ├── config_loader.py
│ │ ├── data_loading.py
│ │ ├── environment_manager.py
│ │ ├── fixation_detection.py
│ │ ├── logging_config.py
│ │ ├── logging_init.py
│ │ ├── roi_edge_cases.py
│ │ ├── roi_mapping.py
│ │ └── validate_dataset_schema.py
│ └── robustness_*.py
├── data/
│ ├── raw/ # Original downloaded data
│ ├── derived/ # Processed intermediate data
│ └── synthetic/ # Synthetic test data
├── docs/ # Documentation
│ └── README.md
├── output/ # Final outputs and reports
│ ├── exclusion_log.txt
│ ├── data_quality_report.csv
│ ├── verification_log.txt
│ ├── stability_check.json
│ └── causal_framing_statement.txt
├── paper/ # Research paper artifacts
│ └── abstract.md
├── state/ # Runtime state and checksums
│ ├── data_hashes.json
│ ├── runtime_events.json
│ ├── runtime_metrics.json
│ └── schema_validation.json
├── tests/ # Test suite
│ ├── contract/
│ └── integration/
├── requirements.txt
└── quickstart.md
```

## Key Fixed Effects
The study focuses on the following fixed effects in the mixed-effects regression model:
- **Source Fixation**: Duration of visual attention on source attribution
- **Valence**: Emotional tone of headlines (NRC/VADER lexicons)
- **Cognitive Reflection**: Individual CRT scores

These three factors are tested for a three-way interaction effect on belief ratings.

## Execution Flow

1. **Initialize**: Run `code/setup_data_structure.py` and `code/setup_environment.py`
2. **Ingest**: Execute `code/utils/data_loading.py` to fetch real eye-tracking data
3. **Preprocess**: Run `code/02_preprocess_gaze.py` with fixation detection
4. **Validate**: Execute `code/02_data_quality_report.py` for quality metrics
5. **Calculate Valence**: Run `code/03_valence_calculation.py` for headline sentiment
6. **Merge**: Execute `code/04_data_merge.py` to combine datasets
7. **Regress**: Run `code/05_regression_analysis.py` for mixed-effects modeling
8. **Correct**: Execute `code/06_apply_holm_correction.py` for p-value adjustment
9. **Robustness**: Run `code/robustness_sweep.py` for threshold sensitivity
10. **Stability**: Execute `code/07_stability_check.py` for consistency verification
11. **Report**: Run `code/07_generate_causal_framing.py` for final statement
12. **Verify**: Execute `code/08_verify_artifacts_checksums.py` for data integrity

## Dependencies
- pandas
- numpy
- scikit-learn
- statsmodels
- nltk
- scipy
- datasets (Hugging Face)
- pyyaml

## Reproducibility
All random seeds are pinned in `code/config.yaml` (seed = 42). Every artifact is checksummed in `state/` with SHA-256 hashes for data hygiene compliance.
