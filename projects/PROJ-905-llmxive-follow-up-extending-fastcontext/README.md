# llmXive: Extending FastContext

This project extends the FastContext paper "Training Efficient Repository Explorer for Coding Agents" by analyzing repository structure regularity and its impact on context retrieval performance.

## Overview

The project implements:
1. **Static Analysis**: Scores repositories based on structural regularity (directory layout, test presence, import patterns).
2. **Stratification**: Splits repositories into "Regular" and "Irregular" sets based on scores.
3. **FastContext-Lite**: A CPU-efficient context exploration pipeline.
4. **Baseline Comparison**: Runs the original FastContext (4B) model for comparison.
5. **Statistical Analysis**: Compares performance between Regular and Irregular sets.

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-905-llmxive-follow-up-extending-fastcontext
 ```

2. Create a virtual environment (optional but recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

## Usage

### Step 1: Download Dataset

Download the SWE-bench Lite dataset:
```bash
cd code
python data_loader.py
```

### Step 2: Extract Ground Truth Annotations

Extract relevant files from dataset annotations:
```bash
python annotation_extractor.py
```
Output: `data/raw/ground_truth_annotations.csv`

### Step 3: Run Static Analysis

Analyze repository structure and compute regularity scores:
```bash
python static_analysis.py
```
Output: `data/processed/regularity_scores.csv`

### Step 4: Stratify Repositories

Split repositories into Regular and Irregular sets:
```bash
python stratification.py
```
Output: `data/processed/regular_repos.csv`, `data/processed/irregular_repos.csv`

### Step 5: Run FastContext-Lite Pipeline

Execute the efficient context exploration pipeline:
```bash
python fastcontext_lite.py
```

### Step 6: Run Baseline (Original FastContext 4B)

Execute the baseline model for comparison:
```bash
python baseline_runner.py
```

### Step 7: Run Full Experiment

Run the complete experiment pipeline:
```bash
python main.py
```
Output: `data/results/exploration_logs.jsonl`

### Step 8: Analyze Results

Perform statistical analysis on the results:
```bash
python analysis.py
```
Output: `data/results/statistical_summary.json`

## Project Structure

```
projects/PROJ-905-llmxive-follow-up-extending-fastcontext/
├── code/
│ ├── __init__.py
│ ├── config.py
│ ├── data_loader.py
│ ├── annotation_extractor.py
│ ├── static_analysis.py
│ ├── stratification.py
│ ├── fastcontext_lite.py
│ ├── baseline_runner.py
│ ├── metrics_logger.py
│ ├── analysis.py
│ ├── main.py
│ └── requirements.txt
├── data/
│ ├── raw/
│ ├── processed/
│ └── results/
├── tests/
│ ├── unit/
│ └── integration/
├── specs/
│ └── contracts/
├── state/
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.