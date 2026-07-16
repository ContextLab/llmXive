# Quickstart: llmXive follow-up: extending "Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution"

## Prerequisites

- Python 3.11+
- Git
- 10 GB free disk space
- GitHub Actions free-tier runner (or local equivalent: 2 CPU cores, ~7 GB RAM)

## Setup

### 1. Clone Repository

```bash
git clone
cd llmxive-followup
git checkout 001-llmxive-followup
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Seeds

Edit `src/config/config.py` to set random seeds:

```python
RANDOM_SEED = 42
ALFWORK_SEED = 42
TRANSFORMER_SEED = 42
```

### 4. Download ALFWorld

```bash
pip install alfworld
# ALFWorld will download datasets on first run; no manual download needed.
```

## Run Experiment

### Generate Baseline Trajectories (Cohort 1)

```bash
python src/sim/trajectory_generator.py --n 500 --condition baseline --output data/raw/baseline_trajectories.jsonl
```

### Generate Degraded Trajectories (Cohort 2)

```bash
python src/sim/trajectory_generator.py --n 500 --condition degraded --output data/raw/degraded_trajectories.jsonl
```

### Generate Intervention Trajectories (Cohort 3)

```bash
python src/sim/trajectory_generator.py --n 500 --condition intervention --output data/raw/intervention_trajectories.jsonl
```

### Validate Trajectories

```bash
python src/sim/validation.py --input data/raw/baseline_trajectories.jsonl --output data/derived/baseline_validated.jsonl
python src/sim/validation.py --input data/raw/degraded_trajectories.jsonl --output data/derived/degraded_validated.jsonl
python src/sim/validation.py --input data/raw/intervention_trajectories.jsonl --output data/derived/intervention_validated.jsonl
```

### Calculate Retrieval Scores

```bash
python src/retrieval/relevance_scorer.py --input data/derived/baseline_validated.jsonl --task-bank data/raw/task_bank.json --output data/derived/baseline_scores.jsonl
python src/retrieval/relevance_scorer.py --input data/derived/degraded_validated.jsonl --task-bank data/raw/task_bank.json --output data/derived/degraded_scores.jsonl
python src/retrieval/relevance_scorer.py --input data/derived/intervention_validated.jsonl --task-bank data/raw/task_bank.json --output data/derived/intervention_scores.jsonl
```

### Run Statistical Analysis

```bash
python src/analysis/statistical_tests.py --input data/derived/baseline_scores.jsonl,data/derived/degraded_scores.jsonl,data/derived/intervention_scores.jsonl --output data/derived/stats.csv
```

## Verify Results

Check `data/derived/stats.csv` for statistical results.
Run tests:

```bash
pytest tests/ -v
```

## Cleanup

```bash
rm -rf data/raw/* data/derived/*
```