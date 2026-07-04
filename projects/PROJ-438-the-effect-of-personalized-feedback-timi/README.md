# The Effect of Personalized Feedback Timing on Skill Acquisition

This project analyzes the Open University Learning Analytics Dataset (OULAD) to investigate how the timing of personalized feedback affects learner skill acquisition.

## Project Structure

```
PROJ-438-the-effect-of-personalized-feedback-timi/
├── code/ # Python modules and scripts
│ ├── config.py # Configuration loader
│ ├── logging_config.py # Logging infrastructure
│ ├── checksums.py # Data integrity utilities
│ ├── schema.py # Data validation utilities
│ ├── download_data.py # OULAD data downloader
│ ├── preprocess.py # Data preprocessing
│ ├── apply_exclusions.py# Exclusion logic
│ ├── compute_intervals.py# Feedback interval calculation
│ ├── bin_feedback_groups.py# Student binning
│ ├── models.py # Cluster-Robust OLS model fitting
│ ├── posthoc_tukey.py # Tukey HSD post-hoc tests
│ ├── sensitivity.py # Sensitivity analysis
│ ├── calculate_stability.py# Significance stability calculation
│ ├── calculate_flip_rate.py# Significance flip rate calculation
│ ├── evaluate_effect_sizes.py# Effect size evaluation
│ ├── verify_flip_rate.py# Flip rate verification
│ ├── generate_*.py # Data generation wrappers
│ └── report.py # Final report generation
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed datasets and results
│ ├── cache/ # Cached intermediate files
│ └── checksums/ # Data integrity checksums
├── tests/ # Test suite
├── specs/ # Specification documents
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip (package installer)

## Installation

1. Navigate to the project directory:
 ```bash
 cd projects/PROJ-438-the-effect-of-personalized-feedback-timi
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage Instructions

The pipeline is designed to be run sequentially. Each step produces output required by the next step.

### Step 1: Setup Data Directories
Ensure the directory structure exists:
```bash
python code/setup_data_dirs.py
```

### Step 2: Download Data
Download the OULAD dataset from the official source:
```bash
python code/download_data.py
```
*Output*: `data/raw/` containing the extracted OULAD data.

### Step 3: Preprocess Data
Filter courses and extract learner records:
```bash
python code/preprocess.py
```
*Output*: `data/processed/learners_raw.csv`

### Step 4: Apply Exclusions
Remove learners without forum interactions and courses with <50 learners:
```bash
python code/apply_exclusions.py
```
*Output*: Updated `data/processed/learners_raw.csv` (filtered).

### Step 5: Compute Feedback Intervals
Calculate time deltas between submission and response:
```bash
python code/compute_intervals.py
```
*Output*: Intermediate interval data.

### Step 6: Bin Students into Feedback Groups
Assign students to "Immediate", "Delayed", or "Variable" groups:
```bash
python code/bin_feedback_groups.py
```
*Output*: `data/processed/learners_binned.csv`

### Step 7: Fit Statistical Models
Fit Cluster-Robust OLS and perform Tukey HSD post-hoc tests:
```bash
python code/models.py
python code/posthoc_tukey.py
```

### Step 8: Sensitivity Analysis
Run sensitivity analysis on boundary thresholds:
```bash
python code/sensitivity.py
```

### Step 9: Calculate Stability and Flip Rates
Compute significance stability and flip rate metrics:
```bash
python code/calculate_stability.py
python code/calculate_flip_rate.py
```

### Step 10: Evaluate Effect Sizes
Compare calculated effect sizes against the target threshold:
```bash
python code/evaluate_effect_sizes.py
```

### Step 11: Verify Flip Rate
Verify results against Specification SC-003:
```bash
python code/verify_flip_rate.py
```

### Step 12: Generate Final Report
Compile all results into the final analysis report:
```bash
python code/report.py
```
*Output*: Final report and `data/processed/results_metrics.csv`, `data/processed/significance_stability_report.csv`.

## Verification

To verify data integrity, run:
```bash
python code/checksums.py
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## Configuration

Edit `config.yaml` (if present in the root) or modify `code/config.py` to change:
- Dataset URLs
- Feedback timing boundaries (default: 2h, 48h)
- Minimum learner count per course (default: 50)
- Output paths

## License

This project follows the licensing of the OULAD dataset.

## References

- Open University Learning Analytics Dataset: https://analyse.kmi.open.ac.uk/open_dataset
- Specification: `specs/001-feedback-timing-analysis/`