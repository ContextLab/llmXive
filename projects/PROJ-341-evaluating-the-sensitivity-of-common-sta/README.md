# Evaluating the Sensitivity of Common Statistical Tests to Dataset Size

## Overview
This project investigates how sample size affects the reliability of common statistical tests (t-test, ANOVA, chi-squared). We simulate data with known ground truth across a range of sample sizes (n=5 to n=500) to empirically calculate Type I and Type II error rates.

## Project Structure
```
.
├── code/ # Source code
│ ├── simulation/ # Simulation engine
│ ├── analysis/ # Threshold finding & validation
│ ├── visualization/ # Plotting utilities
│ └── main.py # Entry point
├── data/
│ ├── raw/ # Public datasets (downloaded)
│ ├── simulation/ # Simulation outputs (p-values, error rates)
│ ├── visualization/ # Generated plots
│ └── reports/ # Final validation reports
├── tests/ # Unit and integration tests
├── specs/ # Design documents
├── requirements.txt # Dependencies
└── README.md
```

## Prerequisites
- Python 3.9+
- pip

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
### Running the Simulation
Run the main simulation script with default parameters:
```bash
python code/main.py
```

To specify parameters:
```bash
python code/main.py --sample-size 20 --effect-size 0.5 --test-type t-test --alpha 0.05
```

### Generating Validation Report
After simulation and analysis, generate the validation report:
```bash
python code/main.py --run-validation
```

## Output
- `data/simulation/p_values_raw.csv`: Raw p-values from all simulation iterations.
- `data/simulation/error_rates_summary.csv`: Aggregated Type I and Type II error rates.
- `data/visualization/`: Generated plots showing sample size vs. error rate.
- `data/reports/validation_report.md`: Final report comparing simulation to real-world data.

## License
MIT
