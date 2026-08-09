# Project: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Overview
This project investigates the relationship between visual attention patterns (specifically fixation duration on source attribution vs. headline body) and susceptibility to misleading headlines. We analyze how cognitive reflection, headline valence, and attention distribution interact to influence belief ratings.

## Key Findings
- Visual attention to source attribution significantly moderates the effect of headline valence on belief susceptibility.
- Higher cognitive reflection scores correlate with reduced susceptibility to misleading headlines, particularly when source attribution is attended to.
- The interaction between fixation duration, valence, and cognitive reflection explains a significant portion of the variance in belief ratings.

## Repository Structure
```
.
├── code/ # Implementation scripts
│ ├── utils/ # Utility functions (fixation detection, ROI mapping, etc.)
│ ├── models/ # Data models (Participant, Stimulus, GazeEvent)
│ ├── 01_extract_empirical_outcome.py
│ ├── 02_preprocess_gaze.py
│ ├── 03_valence_calculation.py
│ ├── 04_data_merge.py
│ ├── 05_regression_analysis.py
│ ├── 06_measure_runtime.py
│ ├── 07_generate_causal_framing.py
│ ├── robustness_runner.py
│ ├── robustness_sweep.py
│ └── robustness_stability_check.py
├── data/
│ ├── raw/ # Raw eye-tracking data
│ ├── derived/ # Processed datasets
│ └── processed/ # Final analysis-ready datasets
├── output/ # Generated reports and logs
├── state/ # Pipeline state and validation artifacts
├── tests/ # Test suites
├── docs/ # Documentation
└── paper/ # Draft manuscript and supplementary materials
```

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure the dataset is downloaded by running `code/utils/data_loading.py`

## Usage
Run the pipeline in order:
1. `python code/01_extract_empirical_outcome.py`
2. `python code/02_preprocess_gaze.py`
3. `python code/03_valence_calculation.py`
4. `python code/04_data_merge.py`
5. `python code/05_regression_analysis.py`
6. `python code/06_measure_runtime.py`
7. `python code/07_generate_causal_framing.py`
8. `python code/robustness_sweep.py` (optional robustness analysis)

## Data
- **Raw Data**: Eye-tracking data from the Dundee Eye-Tracking Corpus (downloaded via `code/utils/data_loading.py`)
- **Derived Data**: Preprocessed gaze events, valence scores, and merged datasets
- **Outputs**: Regression results, robustness reports, and causal framing statements

## Configuration
Edit `code/config.yaml` to modify:
- Random seed
- Dataset URL
- Fixation detection parameters (I-VT or I-DT)
- ROI definitions

## License
This project is licensed under the MIT License.
