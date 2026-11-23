# Quick Start Guide - Visual Complexity IAT Pipeline

## Prerequisites
- Python 3.11.x
- pip

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

### Step 1: Generate Synthetic Data (for testing/CI)
```bash
python code/data/load.py --null-effect
```
This generates synthetic response logs at `data/raw/responses/synthetic_participants.csv`.

### Step 2: Process Stimuli
```bash
python code/main.py --process-stimuli
```
Computes visual complexity metrics for background images.

### Step 3: Aggregate Responses
```bash
python code/main.py --aggregate-responses
```
Filters trials and calculates D-scores.

### Step 4: Run Analysis
```bash
python code/main.py --run-analysis
```
Performs permutation test and sensitivity analysis.

### Step 5: Generate Plots and Report
```bash
python code/viz/plot.py
python code/viz/generate_report.py
```
Produces publication-quality figures and final report.

## Production Mode (Real Data)
To run with real data (no synthetic fallback):
1. Place real data at `data/raw/responses/participants.csv`
2. Run without `--null-effect` flag:
 ```bash
 python code/main.py --process-stimuli --aggregate-responses --run-analysis
 ```

## Verification
After running the full pipeline, verify outputs:
- `data/results/permutation_results.json`
- `data/results/sensitivity_results.json`
- `data/results/d_score_comparison.png`
- `data/results/final_report.md`