# The Impact of Text Message Tone on Perceived Emotional Support

## Project Overview

This project investigates how text message tone (emoji usage, punctuation intensity, and message length) influences perceived emotional support in different relationship contexts (friend vs. acquaintance). The pipeline implements a rigorous statistical analysis workflow using Linear Mixed Models (LMM) with sensitivity analysis across multiple cue-intensity weighting schemes.

**Key Features**:
- Factorial stimulus generation with controlled text message variations
- Real human participant data ingestion from Prolific
- Linear Mixed Model analysis with random intercepts for participants and stimuli
- Tukey-corrected post-hoc tests for interaction effects
- Sensitivity analysis across three cue-intensity weighting schemes
- Full reproducibility with deterministic random seeds and checksum verification

**Constitutional Principles**:
- Reproducibility: All analyses use fixed random seeds and are fully deterministic
- Verified Accuracy: Real data from Prolific required; mock data rejected for primary analysis
- Data Hygiene: Strict validation, anonymization, and exclusion protocols
- Single Source of Truth: All data flows through validated schemas
- Versioning Discipline: Checksums recorded for all artifacts
- Human-Subject Anonymity: Prolific IDs hashed before analysis

## CLI Usage

The primary entry point is `code/run_pipeline.py`:

```bash
# Run the full pipeline with real data
python code/run_pipeline.py --mode real

# Run the full pipeline with mock data (CI testing only)
python code/run_pipeline.py --mode mock

# Run specific components
python code/run_pipeline.py --mode real --steps stimulus,counterbalance,random_order

# Benchmark runtime
python code/run_pipeline.py --mode mock --benchmark
```

**Important**: Mock mode is disabled for primary analysis. Attempting to generate reports with mock data will exit with error code 1.

## Project Structure

```
.
├── code/ # Python modules and scripts
│ ├── config.py # Configuration constants
│ ├── logging_config.py # Logging setup
│ ├── run_pipeline.py # Main CLI entry point
│ ├── 00_define_weights.py # Cue intensity weighting schemes
│ ├── 01_generate_stimuli.py # Stimulus generation
│ ├── 02_counterbalance.py # Counterbalancing trials
│ ├── 03_random_order.py # Random presentation order
│ ├── 03_clean_data.py # Data cleaning and exclusion
│ ├── 04_fit_lmm.py # Primary LMM analysis
│ ├── 05_posthoc.py # Tukey post-hoc tests
│ ├── 06_sensitivity.py # Sensitivity analysis
│ ├── 99_manifest.py # Final manifest generation
│ └──... # Additional scripts
├── data/
│ ├── raw/ # Raw data (real_ratings.csv, stimuli.csv)
│ ├── processed/ # Cleaned and processed data
│ ├── consent/ # Consent records
│ ├── results/ # Analysis results
│ └── figures/ # Generated plots
├── tests/
│ ├── contract/ # Contract tests
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── specs/
│ └── 001-the-impact-of-text-message-tone-on-perce/
│ ├── spec.md
│ ├── data-model.md
│ └── contracts/ # Schema definitions
├── README.md # This file
├── quickstart.md # Quick start guide
└── requirements.txt # Python dependencies
```

## Reproducibility

This project guarantees full reproducibility through:

1. **Deterministic Execution**: All random operations use a fixed seed defined in `code/config.py`
2. **Checksum Verification**: SHA-256 hashes recorded in `data/checksums.json` for all artifacts
3. **Manifest Generation**: `data/manifest.json` tracks all output files and their hashes
4. **Schema Validation**: All data files validated against YAML schemas in `specs/.../contracts/`
5. **Version Control**: All scripts and configurations under version control

To verify reproducibility:

```bash
# Run the pipeline twice and compare manifests
python code/run_pipeline.py --mode mock
python code/compare_hashes.py
```

The `compare_hashes.py` script verifies that `analysis_results.json` and `sensitivity_report.md` produce identical hashes across runs.

## Requirements

- Python 3.9+
- CPU-only execution (no GPU dependencies)
- See `code/requirements.txt` for full dependency list

## Data Sources

- **Stimuli**: Generated programmatically via `code/01_generate_stimuli.py`
- **Ratings**: Real data from Prolific (minimum 60 participants) required in `data/raw/real_ratings.csv`
- **Mock Data**: Available in `data/mock/` for CI testing only

## Methodological Notes

- Primary analysis uses Wald-Z approximation for p-values (statsmodels)
- Satterthwaite approximation not available in Python stack; documented in `data/results/methodological_limitations.md`
- Sensitivity analysis tests robustness across three cue-intensity weighting schemes
- Straight-lining detection and listwise deletion applied for data quality

## License

This project is licensed under the terms specified in the repository.
