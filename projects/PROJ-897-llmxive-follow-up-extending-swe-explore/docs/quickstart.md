# Quickstart Guide

## Prerequisites

- Python 3.10+
- pip
- Git

## Setup

1. **Install Dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Create Project Structure**
 ```bash
 python code/setup_project_structure.py
 ```

3. **Configure Linting**
 ```bash
 python code/setup_linting.py
 ```

## Execution Pipeline

The full pipeline runs the following steps in order:

### Phase 1: Data Download & Processing
```bash
# Download raw dataset
python code/data/download.py

# Derive ground truth
python code/data/derive_gt.py

# Filter hard instances
python code/data/filter_hard.py

# Filter non-hard instances
python code/data/filter_non_hard.py

# Generate synthetic issues
python code/data/mutate.py

# Validate hard subset
python code/data/validate_hard.py
```

### Phase 2: Agent Execution
```bash
# Run static baseline
python code/agent/static_baseline.py

# Run iterative agent
python code/agent/iterative.py
```

### Phase 3: Analysis
```bash
# Generate metrics
python code/analysis/generate_final_metrics.py

# Run statistical tests
python code/analysis/stats.py

# Generate plots
python code/analysis/plots.py

# Generate report
python code/analysis/report_generator.py
```

## Verification

To verify the pipeline completed successfully:
```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **ModuleNotFoundError**: Ensure `code/requirements.txt` was installed.
- **File not found**: Ensure `python code/setup_project_structure.py` was run first.
- **Memory errors**: The pipeline uses streaming for large datasets; ensure at least 7GB RAM available [UNRESOLVED-CLAIM: c_45194770 — status=not_enough_info].
