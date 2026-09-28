# llmXive: Foundation Protocol Follow-up

Automated research pipeline for analyzing the trade-off between context compression and policy violation rates in agentic societies.

## Project Structure

- `code/`: Python implementation modules
- `data/`: Raw generated workflows, processed execution logs, and analysis results
- `contracts/`: JSON schemas for workflow and execution log validation
- `state/`: Project state registry with artifact checksums
- `tests/`: Unit and integration tests
- `specs/`: Design documents and user stories

## Prerequisites

- Python 3.11+
- pip (package manager)

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Quick Start

Run the full pipeline to generate workflows, execute them with full and compressed contexts, and analyze the trade-off curve:

```bash
python code/main.py --generate --compress --analyze
```

This command:
- Generates synthetic workflows (T012)
- Executes them with full context (T014)
- Executes them with compressed contexts at depths 1-20 (T021, T023)
- Analyzes the trade-off and identifies the safe operating zone (T029-T031)

## Reproducibility and Verification

This project enforces strict reproducibility and data integrity checks. Follow these steps to verify results.

### 1. Run the Pipeline Twice with Identical Seeds

To verify determinism, execute the pipeline twice with the same seed and compare output hashes:

```bash
# First run
python code/main.py --generate --compress --analyze --seed 42

# Second run (same seed)
python code/main.py --generate --compress --analyze --seed 42
```

The `--seed` flag ensures that all random operations (workflow generation, sampling) use the same seed, producing identical outputs.

### 2. Verify Reproducibility Report

After running the pipeline twice, check the reproducibility report:

```bash
cat data/results/reproducibility_report.json
```

The report contains:
- `run1_hash`: SHA-256 hash of all data files from the first run
- `run2_hash`: SHA-256 hash of all data files from the second run
- `identical`: Boolean indicating if the hashes match
- `timestamp`: ISO8601 timestamp of the verification

If `identical` is `true`, the pipeline is fully deterministic.

### 3. Verify Data Consistency

Run the data consistency check to ensure all generated workflows have corresponding execution logs and analysis entries:

```bash
python code/utils/verify_data_consistency.py
```

This script cross-references:
- `data/raw/`: Generated workflow IDs
- `data/processed/`: Execution log workflow IDs
- `data/results/`: Analysis result workflow IDs

The output is written to `data/results/data_consistency_report.json`.

### 4. Verify Invalid Workflow Exclusion

Ensure that workflows marked as `is_valid=false` are excluded from the final analysis:

```bash
python code/utils/verify_invalid_workflow_exclusion.py
```

This script verifies that invalid workflows do not appear in `data/results/tradeoff_curve.csv` or `data/results/threshold_ci.json`.

### 5. Verify Oracle Independence

Run the static analysis check to ensure the Oracle engine is only imported for validation, not execution logic:

```bash
python code/utils/verify_oracle_independence.py
```

This script parses the AST of `full_context.py` and `compressed_context.py` to verify that no policy execution logic is implemented directly in the engines.

### 6. Verify Data Hygiene

Run the data hygiene audit to ensure `data/raw/` contains only generated files and derived directories contain only processed data:

```bash
python code/utils/data_hygiene_audit.py
```

The audit report is written to `data/results/data_hygiene_audit.log`.

### 7. Verify Edge Case Handling

Review the edge case audit report to see how single-node graphs and depth=0 cases were handled:

```bash
cat data/results/edge_case_summary.json
```

This report aggregates edge cases from `data/processed/edge_cases.log` and `data/processed/edge_cases_filtered.log`.

### 8. Verify Checksums

Use the checksum utility to verify the integrity of specific artifacts:

```bash
python code/utils/checksum_utils.py --file data/raw/workflows.json
python code/utils/checksum_utils.py --directory data/processed/
```

### 9. Validate Against Schemas

Ensure all JSON files conform to the defined schemas:

```bash
python code/utils/validate_schemas.py
```

This script validates all files in `data/processed/` and `data/results/` against the schemas in `contracts/`.

## Output Artifacts

The pipeline produces the following key artifacts:

- `data/raw/workflows.json`: Generated synthetic workflows
- `data/processed/full_context_logs.json`: Execution logs with full context
- `data/processed/compressed_context_logs.json`: Execution logs with compressed contexts
- `data/results/tradeoff_curve.csv`: Regression curve data (reduction_pct, error_rate, ci_lower, ci_upper)
- `data/results/threshold_ci.json`: Identified safe operating zone threshold with confidence intervals
- `data/results/glmm_diagnostics.json`: GLMM model diagnostics and coefficients
- `data/processed/pairwise_comparison_results.json`: Corrected p-values for multiple comparisons
- `data/results/reproducibility_report.json`: Hash comparison of two pipeline runs
- `data/results/data_consistency_report.json`: Data integrity verification results
- `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`: Final state registry with artifact hashes

## Testing

Run the full test suite:

```bash
pytest
```

Run specific test categories:
- Unit tests: `pytest tests/unit/`
- Integration tests: `pytest tests/integration/`
- Contract tests: `pytest tests/contract/`

## Configuration

Key configuration options:

- `--seed`: Random seed for deterministic generation (default: 42)
- `--count`: Number of workflows to generate (default: 500)
- `--depths`: Compression depths to test (default: 1-20)
- `--threshold`: Policy violation error rate threshold for safe operating zone (default: 1.0)

## License

This project is part of the llmXive research initiative. See LICENSE for details.