# Quickstart Guide for PROJ-179: The Influence of Metacognitive Awareness on Reality Testing

## Overview

This project analyzes the relationship between metacognitive awareness (Type-2 AUC) and reality testing accuracy (d') using behavioral data. The analysis follows a hold-out design to ensure independence between predictor and outcome measures.

## Prerequisites

- Python 3.8+
- Required packages listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Data Availability Warning

This project requires a valid behavioral dataset containing `confidence_rating` and `source_label` columns. If no valid dataset is found, the pipeline will abort with an error.

## Running the Analysis

Execute the full analysis pipeline:

```bash
python code/analysis.py
```

This command will:
1. Validate data availability (T004)
2. Download the dataset (T005)
3. Validate data fields (T006)
4. Preprocess trial data (T012)
5. Compute correlation metrics (T014)
6. Run bootstrap analysis (T015)
7. Perform hierarchical regression (T020)
8. Filter by modality (T026)
9. Run robustness analysis (T027)
10. Generate reports (T016, T022, T028)

## Output Files

After successful execution, the following files will be generated:

### Data Files
- `data/derived/trial_data.csv` - Preprocessed trial-level data
- `data/derived/visual_trials.csv` - Visual modality trials
- `data/derived/auditory_trials.csv` - Auditory modality trials

### Results Files
- `data/results/bootstrap_config.json` - Bootstrap configuration and runtime info
- `data/results/primary_analysis.json` - Primary correlation analysis results
- `data/results/regression_analysis.json` - Hierarchical regression results
- `data/results/robustness_analysis.json` - Modality-specific robustness analysis

## Validation

To validate all output files:

```bash
python code/quickstart_validator.py
```

## Troubleshooting

### Data Download Failed

If the download fails, check your internet connection and ensure the dataset URLs are accessible. The pipeline will attempt multiple sources before failing.

### Missing Required Columns

If validation fails due to missing columns, ensure the dataset contains:
- `participant_id`
- `trial_id`
- `stimulus_modality`
- `source_label`
- `participant_response`
- `confidence_rating`

### Runtime Exceeded

If bootstrap analysis exceeds 5.5 hours, the count will be automatically reduced to 500 resamples.

## License

This project is part of the llmXive automated science pipeline.
