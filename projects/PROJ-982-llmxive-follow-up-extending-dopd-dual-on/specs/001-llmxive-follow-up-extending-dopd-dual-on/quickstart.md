# Quickstart: 001-dopd-discrete-mdp

## Prerequisites

- Python 3.11+
- Git

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Dependencies include: `gymnasium`, `minigrid`, `numpy`, `pandas`, `scipy`, `pytest`.*

## Running the Experiment

### 1. Generate Data (Single Seed)
To test a single run of the DOPD regime:
```bash
python code/training/run_experiment.py --seed 42 --regime dopd --grid-size 5
```

### 2. Run Full Statistical Analysis (50 Seeds)
To execute the full research protocol:
```bash
python code/training/run_experiment.py --seeds 50 --grid-size 5 --output data/processed/full_analysis.csv
```
*This command runs both "uniform" and "dopd" regimes across 50 seeds and aggregates results.*

### 3. Run Statistical Test
To compute the Mann-Whitney U test and effect size:
```bash
python code/analysis/stats.py --input data/processed/full_analysis.csv
```
*Output: `data/processed/stats_report.json`.*

### 4. Verify Environment
To ensure the "privilege illusion" is correctly simulated:
```bash
python code/env/test_privilege.py
```
*Checks that Teacher sees `H` and Student does not, and that `H` is required for optimal reward.*

## Reproducing Results

To reproduce a specific seed:
```bash
export PYTHONHASHSEED=0
python code/training/run_experiment.py --seed 42 --regime dopd
```

## Troubleshooting

- **Memory Error**: Ensure `--grid-size` is ≤ 5. Larger grids explode Q-table size.
- **Import Error**: Ensure `minigrid` is installed (`pip install minigrid`).
- **Statistical Error**: If `p_value` is NaN, check that both regimes have valid data (no crashes).
