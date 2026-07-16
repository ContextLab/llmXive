# PROJ-470: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Overview
This project implements an automated pipeline to analyze resting-state EEG data
to predict cognitive fatigue. The core hypothesis is that cognitive fatigue
manifests as a phase transition in the system's problem-solving matter,
measurable through signal complexity metrics like Lempel-Ziv Complexity (LZC)
and Permutation Entropy (PE).

## Project Structure

```
.
├── code/ # Pipeline implementation
│ ├── config.yaml # Configuration parameters
│ ├── download.py # Data retrieval (Sleep-EDF, SHHS)
│ ├── preprocess.py # Filtering and artifact rejection
│ ├── features.py # LZC and PE calculation
│ ├── analysis.py # Correlation and statistical analysis
│ ├── report.py # Final report generation
│ ├── models/ # Data models
│ └── utils/ # Logging utilities
├── data/
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Cleaned EEG and extracted metrics
│ └── analysis/ # Statistical results
├── docs/ # Documentation
├── tests/ # Unit and integration tests
└── specs/ # Design documents and requirements
```

## Quick Start

1. **Setup Environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

2. **Download Data**
 ```bash
 python code/download.py
 ```
 *Note: Requires internet access. Downloads Sleep-EDF from PhysioNet.*

3. **Preprocess Data**
 ```bash
 python code/preprocess.py
 ```
 *Applies 1-40Hz bandpass filter and rejects artifacts >±100µV.*

4. **Extract Features**
 ```bash
 python code/features.py
 ```
 *Calculates LZC and PE, outputs to `data/processed/`.*

5. **Run Analysis**
 ```bash
 python code/analysis.py
 ```
 *Correlates complexity metrics with fatigue scores.*

6. **Generate Report**
 ```bash
 python code/report.py
 ```

## Configuration
Edit `code/config.yaml` to adjust:
- Filter cutoffs (default: 1-40 Hz)
- Artifact thresholds (default: ±100 µV)
- Feature extraction parameters
- Dataset sources

## Data Sources
- **Primary**: Sleep-EDF (PhysioNet ID: `sleep-edf`)
- **Fallback**: SHHS dataset (if Sleep-EDF lacks required variables)

## Statistical Methods
- **Correlation**: Spearman/Pearson (configurable)
- **Multiple Comparisons**: Benjamini-Hochberg correction
- **Sensitivity Analysis**: p ≤ 0.05 and p ≤ 0.01 thresholds

## Limitations
- Requires resting-state EEG segments ≥ 120 seconds
- Dependent on data quality from public repositories
- Complexity metrics may conflate adaptive simplification with degenerative noise

## License
MIT License