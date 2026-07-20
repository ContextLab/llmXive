# Code Directory

## Structure
- `config.py`: Global configuration, logging setup, constants
- `models.py`: Data classes for Participant, NoiseLog, TaskPerformance
- `data_ingestion.py`: Data loading, validation, calibration, and preprocessing
- `model_fitting.py`: Statistical modeling (LMM, VIF, LRT, Tukey HSD)
- `sensitivity_analysis.py`: Robustness checks and threshold sweeps
- `scripts/`: Executable entry points for pipeline stages

## Usage
All scripts are run from the project root:
```bash
python code/scripts/<script_name>.py
```
