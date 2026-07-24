# llmXive Follow-up: AutoResearchClaw Extension - Quick Start

## Prerequisites

- Python 3.9+
- pip
- Git

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmxive-followup
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Set up the project structure:
 ```bash
 python code/setup/create_project_structure.py
 ```

## Running the Pipeline

### Phase 1: Data Ingestion

```bash
# Download ARC-Bench dataset
python code/01_data_ingestion/download_arc_bench.py

# Parse reasoning traces
python code/01_data_ingestion/parse_reasoning_traces.py
```

### Phase 2: Annotation & Distillation

```bash
# Annotate failure cases
python code/02_annotation_distillation/annotate_failures.py

# Split data
python code/02_annotation_distillation/split_data.py

# Distill rules
python code/02_annotation_distillation/distill_rules.py
```

### Phase 3: Execution & Baseline Comparison

```bash
# Generate experiment manifest
python code/03_execution/generate_manifest.py

# Run rule engine experiments
python code/03_execution/run_experiments.py

# Run baseline external agent
python code/03_execution/run_baseline_external.py

# Merge results
python code/03_execution/merge_results.py
```

### Phase 4: Statistical Analysis

```bash
# Fit statistical model
python code/04_analysis/statistical_model.py

# Perform time difference test
python code/04_analysis/time_diff_test.py

# Calculate stratified rates
python code/04_analysis/calculate_stratified_rates.py

# Generate error taxonomy
python code/04_analysis/error_taxonomy.py

# Generate final report
python code/04_analysis/generate_report.py
```

## Running External Baseline

The external baseline agent is run via `run_baseline_external.py`. This script:

1. Loads the experiment manifest
2. Submits jobs to the external baseline system
3. Polls for results with exponential backoff
4. Handles timeouts (max 24 hours)

```bash
python code/03_execution/run_baseline_external.py
```

If the baseline times out, check `data/derived/baseline_timeout_error.json` for details.

## Testing

Run all tests:
```bash
pytest code/tests/
```

Run specific test suites:
```bash
# Rule engine tests
pytest code/tests/test_rule_engine.py

# Pipeline integration tests
pytest code/tests/test_pipeline.py

# Linting checks
pytest code/tests/test_lint_check.py

# Formatting checks
pytest code/tests/test_black_check.py
```

## Code Quality

### Linting
```bash
ruff check code/
```

### Formatting
```bash
black --check code/
```

### Fix formatting issues
```bash
black code/
```

## State Management

Update state file with artifact hashes:
```bash
python code/utils/update_state.py
```

## Resources

- Max CPU cores: 2 [UNRESOLVED-CLAIM: c_852b0eb6 — status=not_enough_info]
- Max memory: 7GB
- If memory usage exceeds 7GB, the system will trigger fallback to regex-based distillation. [UNRESOLVED-CLAIM: c_a29bff3f — status=not_enough_info]
