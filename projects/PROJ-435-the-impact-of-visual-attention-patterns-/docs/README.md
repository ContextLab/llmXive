# The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Project Overview
This research project investigates the relationship between visual attention patterns (measured via eye-tracking), headline valence, cognitive reflection scores, and susceptibility to misleading news headlines. The study employs a mixed-effects regression approach to test for a three-way interaction between source fixation duration, headline valence, and cognitive reflection.

## Research Questions
1. How does visual attention to source attribution vs. headline body affect belief ratings?
2. Does headline valence moderate the relationship between attention and belief?
3. Do individuals with higher cognitive reflection scores show different attention-belief patterns?
4. Is there a three-way interaction between fixation duration, valence, and cognitive reflection?

## Methodology
- **Data Source**: Eye-tracking data from the Dundee Eye-Tracking Corpus (or equivalent verified dataset)
- **Analysis**: Mixed-effects regression with random intercepts for participants and headlines
- **Key Variables**:
 - Dependent: `belief_rating`
 - Independent: `fixation_duration`, `valence`, `cognitive_reflection_score`
 - Interaction: `fixation_duration * valence * cognitive_reflection_score`
- **Controls**: `headline_length`, `total_fixation_duration`, `lexicon_used`

## Pipeline Structure
The analysis pipeline consists of the following stages:

### Phase 1: Setup
- Project initialization and directory structure
- Environment configuration and dependency installation
- Linting and formatting setup

### Phase 2: Foundational
- Data ingestion and validation
- Configuration management
- Logging infrastructure

### Phase 3: User Story 1 - Core Data Preprocessing
- I-VT fixation detection
- ROI mapping (source attribution vs. headline body)
- Participant filtering based on data quality
- Data quality reporting

### Phase 4: User Story 2 - Mixed-Effects Regression
- Data merging and outlier capping
- Valence calculation (NRC/VADER lexicons)
- Mixed-effects model fitting
- Holm-Bonferroni correction for multiple comparisons

### Phase 5: User Story 3 - Robustness Analysis
- Threshold sensitivity analysis (50ms, 100ms, 150ms)
- Stability verification of interaction effects
- Robustness reporting

## Directory Structure
```
code/
├── 01_extract_empirical_outcome.py
├── 02_data_quality_report.py
├── 03_data_merge.py
├── 03_valence_calculation.py
├── 04_data_merge.py
├── 05_regression_analysis.py
├── 06_apply_holm_correction.py
├── 06_generate_regression_results.py
├── 06_measure_runtime.py
├── 07_generate_causal_framing.py
├── 07_stability_check.py
├── utils/
│ ├── config_loader.py
│ ├── data_loading.py
│ ├── fixation_detection.py
│ ├── logging_config.py
│ ├── logging_init.py
│ ├── roi_mapping.py
│ └── validate_dataset_schema.py
└── models/
 ├── participant.py
 ├── stimulus.py
 └── gaze_event.py

data/
├── raw/
│ └── eye_tracking_raw.parquet
├── derived/
│ ├── empirical_outcomes.csv
│ ├── preprocessed_gaze.csv
│ ├── valence_scores.csv
│ ├── merged_dataset_full.csv
│ ├── regression_results.csv
│ └── robustness_report.csv
└── synthetic/
 └── ground_truth.csv

output/
├── exclusion_log.txt
├── data_quality_report.csv
├── stability_check.json
└── causal_framing_statement.txt

state/
├── data_hashes.json
├── runtime_events.json
├── runtime_metrics.json
└── schema_validation.json

tests/
├── contract/
│ ├── test_ingestion_schema.py
│ ├── test_regression_schema.py
│ └── test_robustness_schema.py
└── integration/
 ├── test_ivt_preprocessing.py
 ├── test_mixed_effects_recovery.py
 └── test_sensitivity_analysis.py
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Initialize project structure: `python code/setup_data_structure.py`
3. Configure logging: `python code/utils/logging_init.py`
4. Ingest and preprocess data: `python code/02_preprocess_gaze.py`
5. Run full pipeline: See `quickstart.md` for complete execution order

## Key Findings
The analysis will produce:
- Regression coefficients with Holm-Bonferroni corrected p-values
- Stability analysis across different fixation thresholds
- A causal framing statement describing the three-way interaction effect

## Reproducibility
- All random seeds are pinned in `code/config.yaml`
- All data artifacts are checksummed in `state/data_hashes.json`
- Runtime metrics are recorded in `state/runtime_metrics.json`
- Lexicon choice (NRC vs. VADER) is tracked as a covariate

## References
- I-VT Fixation Detection: Salvucci & Goldberg (2000)
- Mixed-Effects Modeling: Bates et al. (2015)
- Holm-Bonferroni Correction: Holm (1979)
- NRC Lexicon: Mohammad & Turney (2013)
- VADER Sentiment: Hutto & Gilbert (2014)
