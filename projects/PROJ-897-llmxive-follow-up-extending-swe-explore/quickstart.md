# Quickstart Guide: llmXive Follow-up (SWE-Explore Extension)

## Prerequisites

- Python 3.9+
- pip
- Git

## Setup

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repo-url>
 cd PROJ-897-llmxive-follow-up-extending-swe-explore
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Initialize Project Structure**:
 ```bash
 python code/setup_project_structure.py
 ```

## Execution Pipeline

The full pipeline runs the following steps in order. Ensure you have internet access for the data download step.

```bash
# 1. Download Raw Data (SWE-Explore)
python code/data/download.py

# 2. Derive Ground Truth
python code/data/derive_gt.py

# 3. Filter Hard & Non-Hard Subsets
python code/data/filter_hard.py
python code/data/filter_non_hard.py

# 4. Generate Synthetic Issues
python code/data/mutate.py

# 5. Validate Hard Subset
python code/data/validate_hard.py

# 6. Run Agent Baseline (Static Multi-Query)
python code/agent/static_baseline.py

# 7. Run Iterative Agent
python code/agent/iterative.py

# 8. Run Turn-Limit Sweep (Optional/Configurable)
python code/agent/sweep_turns.py

# 9. Calculate Metrics & Statistics
python code/analysis/stats.py
python code/analysis/generate_final_metrics.py

# 10. Generate Plots
python code/analysis/plots.py

# 11. Generate Report
python code/analysis/report_generator.py
```

## Validation

To verify the setup and run a quick check:

```bash
python code/validate_quickstart.py
```

## Output Artifacts

- `data/raw/swe_explore_raw.jsonl`: Raw dataset
- `data/curated/hard_subset.jsonl`: Hard instances based on coverage
- `data/curated/synthetic_issues.jsonl`: Generated ambiguous issues
- `data/results/final_metrics.json`: Statistical analysis results
- `paper/draft.md`: Final report draft
- `figures/`: Generated plots
