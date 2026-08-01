# Code Summarization Efficacy Study - Reproducibility Package

This repository contains the code and data for evaluating the efficacy of code summarization techniques for bug localization.

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Running the Analysis

The main analysis script processes interaction logs and generates statistical results:

```bash
python code/analysis/run_statistics.py
```

This will produce:
- `data/analysis_results/results.csv`: Main statistical results
- `data/analysis_results/sensitivity_analysis.csv`: Sensitivity analysis across cutoffs
- `data/analysis_results/outlier_flags.json`: Detected outliers

### Reproducibility Verification

To verify reproducibility on a fresh environment:

1. Extract the reproducibility package:
 ```bash
 tar -xzf data/reproducibility_package_v1.0.tar.gz
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run the analysis:
 ```bash
 python code/analysis/run_statistics.py
 ```

4. Compare results with baseline (within 5% tolerance):
 ```bash
 python code/tests/test_reproducibility.py
 ```

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical analysis scripts
│ ├── data_prep/ # Data preparation utilities
│ ├── utils/ # Shared utilities
│ └── tests/ # Test suite
├── data/
│ ├── analysis_results/ # Generated analysis outputs
│ ├── interaction_logs/ # Participant interaction data
│ ├── summaries/ # Code summaries generated
│ └── reproducibility_package_v1.0.tar.gz
├── README.md
└── requirements.txt
```

## Data Privacy

This package contains **anonymized** interaction logs only. Raw logs and consent forms are explicitly excluded to comply with ethical guidelines and Constitution Principle VI.

## Citation

If you use this code or data in your research, please cite the associated publication.

## License

See LICENSE file for details.
