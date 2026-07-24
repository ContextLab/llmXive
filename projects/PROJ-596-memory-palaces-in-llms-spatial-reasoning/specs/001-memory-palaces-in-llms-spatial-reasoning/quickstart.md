# Quickstart: Memory Palaces in LLMs

## Prerequisites

- Python 3.11+
- 6 GB RAM available
- 14 GB disk space
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/PROJ-596-memory-palaces-in-llms-spatial-reasoning.git
   cd PROJ-596-memory-palaces-in-llms-spatial-reasoning
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/code/requirements.txt
   ```

## Running the Experiment

### 1. Download Datasets
```bash
python code/data/loaders.py --download
```
This script downloads bAbI, LAMBADA, and Story Cloze datasets to `data/raw/`.

### 2. Train Models
```bash
python code/main.py --config config/train.yaml
```
This runs training for both spatial and baseline variants across 5 seeds.

### 3. Evaluate Models
```bash
python code/main.py --eval --config config/eval.yaml
```
This computes exact-match recall and interference distance.

### 4. Analyze Results
```bash
python code/analysis/stats.py --input data/results/
```
This performs statistical tests and generates summary reports.

## Expected Output

- `data/results/run_summary.json`: Aggregated metrics for all runs.
- `data/results/statistical_analysis.csv`: P-values, effect sizes, confidence intervals.
- `artifacts/results/figure_recall.png`: Plot of recall accuracy by variant and dataset.

## Troubleshooting

- **OOM Errors**: If you encounter OOM errors, the script automatically reduces batch size to 4. If memory usage still exceeds 6 GB, the dataset is capped to [deferred] of its original size.
- **Dataset Download Failures**: If a dataset fails to download, the script logs the error and skips that dataset.