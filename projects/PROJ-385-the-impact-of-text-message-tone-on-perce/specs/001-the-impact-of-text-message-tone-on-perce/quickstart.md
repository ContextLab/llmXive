# Quickstart Guide: The Impact of Text Message Tone on Perceived Emotional Support

This guide provides instructions for setting up, running, and validating the automated science pipeline for analyzing text message tone and emotional support.

## Prerequisites

- Python 3.9+
- `pip` package manager
- Access to a terminal/command line

## 1. Environment Setup

### Clone and Install Dependencies

```bash
# Navigate to the project root
cd /path/to/PROJ-385-the-impact-of-text-message-tone-on-perce

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

### Verify Installation

Ensure all required packages are installed:
```bash
python -c "import pandas; import numpy; import scipy; import statsmodels; import linearmodels; print('All dependencies installed successfully.')"
```

## 2. Project Structure

The project follows this directory layout:

```
.
├── code/ # Python source code
│ ├── 00_power_analysis.py
│ ├── 01_generate_stimuli.py
│ ├── 02_simulate_ratings.py
│ ├── 03_clean_data.py
│ ├── 04_run_lmm.py
│ ├── 05_sensitivity_analysis.py
│ ├── config.py
│ ├── logging_config.py
│ └──...
├── data/
│ ├── raw/ # Raw generated/collected data
│ ├── processed/ # Cleaned and analyzed data
│ └── consent/ # Anonymized consent records (real data only)
├── tests/ # Test suites
│ ├── contract/
│ ├── unit/
│ └── integration/
├── specs/ # Feature specifications
│ └── 001-text-tone-emotional-support/
│ ├── quickstart.md
│ ├── plan.md
│ ├── data-model.md
│ └── contracts/
└── figures/ # Generated plots and visualizations
```

## 3. Running the Pipeline

### Option A: Run Individual Stages

You can run each stage of the pipeline independently:

1. **Power Analysis** (Determines target sample size)
 ```bash
 python code/00_power_analysis.py
 ```
 *Output*: `data/processed/power_analysis_results.json`, `data/processed/power_curve.png`

2. **Stimulus Generation** (Creates text message variants)
 ```bash
 python code/01_generate_stimuli.py
 ```
 *Output*: `data/raw/stimuli.csv`

3. **Rating Simulation** (Generates mock human ratings)
 ```bash
 python code/02_simulate_ratings.py
 ```
 *Output*: `data/raw/ratings.csv`

4. **Data Cleaning** (Detects straight-lining, handles missing data)
 ```bash
 python code/03_clean_data.py
 ```
 *Output*: `data/processed/cleaning_log.csv`

5. **LMM Analysis** (Primary statistical model)
 ```bash
 python code/04_run_lmm.py
 ```
 *Output*: `data/processed/analysis_results.json`

6. **Sensitivity Analysis** (Robustness checks)
 ```bash
 python code/05_sensitivity_analysis.py
 ```
 *Output*: `data/processed/sensitivity_report.csv`

### Option B: Run Full Pipeline with CLI

Use the unified CLI entry point for end-to-end execution:

```bash
# Run in mock/simulation mode (default)
python code/run_pipeline.py --mode mock

# Run in real data mode (requires real data collection)
python code/run_pipeline.py --mode real

# Run with benchmarking enabled
python code/run_pipeline.py --mode mock --benchmark

# Specify a random seed for reproducibility
python code/run_pipeline.py --mode mock --seed 42
```

**CLI Arguments**:
- `--mode`: `mock` (simulation) or `real` (human data collection)
- `--benchmark`: Enable timing and performance metrics
- `--seed`: Integer random seed for reproducibility

**Output**: JSON report to stdout containing `total_duration_seconds`, `per_stage_duration`, and `assertion: total_duration < 21600`.

## 4. Validation & Testing

### Contract Tests

Validate data schemas against specifications:

```bash
# Test stimulus schema
python -m pytest tests/contract/test_stimulus_schema.py -v

# Test rating schema
python -m pytest tests/contract/test_rating_schema.py -v
```

### Unit Tests

Run unit tests for specific logic components:

```bash
# Data cleaning logic
python -m pytest tests/unit/test_data_cleaning.py -v

# LMM analysis logic
python -m pytest tests/unit/test_analysis_logic.py -v

# Sensitivity logic
python -m pytest tests/unit/test_sensitivity_logic.py -v
```

### Integration Tests

Run full pipeline integration tests:

```bash
# Full LMM pipeline
python -m pytest tests/integration/test_lmm_pipeline.py -v

# Quickstart validation
python -m pytest tests/integration/test_quickstart.py -v
```

## 5. Configuration

### Random Seed Pinning

Set a fixed random seed for reproducibility:
```bash
python code/run_pipeline.py --seed 42
```

Or configure via `code/config.py` if using a custom configuration file.

### Logging

Pipeline logs are written to `data/pipeline.log`. This includes:
- Pipeline start/stop events
- Exclusion reasons (straight-lining, missing data)
- Timeout events
- Stage completion timestamps

## 6. Data Output Formats

### Power Analysis Results (`data/processed/power_analysis_results.json`)
```json
{
 "target_N": 150,
 "effect_size": 0.15,
 "power": 0.80,
 "alpha": 0.05,
 "method": "simulation",
 "seed": 42
}
```

### Stimuli (`data/raw/stimuli.csv`)
Columns: `stimulus_id`, `scenario_id`, `emoji_level`, `punctuation_level`, `length`, `text`

### Ratings (`data/raw/ratings.csv`)
Columns: `participant_id`, `stimulus_id`, `relationship_context`, `emotional_support_rating`

### Analysis Results (`data/processed/analysis_results.json`)
Contains fixed effect estimates, p-values, variance components, and Tukey-corrected post-hoc results.

## 7. Troubleshooting

### Missing Dependencies
```bash
pip install -r code/requirements.txt --upgrade
```

### Schema Validation Failures
Ensure data generation scripts (`01_generate_stimuli.py`, `02_simulate_ratings.py`) are run before validation tests.

### Pipeline Timeout
If the pipeline exceeds the 6-hour limit (SC-005), check the log in `data/pipeline.log` for the specific stage that timed out. Reduce sample size or optimize code as needed.

## 8. Next Steps

- **Simulation Mode**: Run the full pipeline with `--mode mock` to generate synthetic data and validate the analysis workflow.
- **Real Data Mode**: Deploy to Qualtrics/Prolific (see `code/04_collect_real_data.py` for API integration) and run with `--mode real`.
- **Sensitivity Analysis**: Review `data/processed/sensitivity_report.csv` to assess robustness of findings across alternative cue definitions.

## 9. Support & References

- **Data Model**: See `specs/001-text-tone-emotional-support/data-model.md`
- **API Contracts**: See `specs/001-text-tone-emotional-support/contracts/`
- **Implementation Plan**: See `specs/001-text-tone-emotional-support/plan.md`
- **Codebase**: `code/` directory