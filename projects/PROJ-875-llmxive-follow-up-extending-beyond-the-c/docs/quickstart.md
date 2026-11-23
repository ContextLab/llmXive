# Quickstart Guide

This guide provides the exact commands to run the llmXive pipeline for the Pilot and Full experiment modes.

## Prerequisites

1. **Python Environment**: Ensure you have Python 3.10+ installed.
2. **Dependencies**: Install the required packages using the pinned `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Configuration

The pipeline uses a seed configuration file located at `config/seeds.yaml`. Ensure this file contains the list of integer seeds for the current run phase (Pilot or Full).

```bash
# Verify seeds configuration
cat config/seeds.yaml
```

## Execution Modes

The main entry point `code/main.py` supports two execution modes: `pilot` and `full`.

### Pilot Mode

Runs the experiment on a small subset of seeds (N=20) to verify the pipeline and perform an initial power analysis.

**Command:**
```bash
python code/main.py --mode pilot
```

**Expected Outputs:**
- `results/statistical_summary.json`: Aggregated metrics and statistical test results.
- `state/checksums.yaml`: Data integrity checksums for processed files.
- `results/power_analysis_report.json`: Power analysis results (if applicable).

### Full Mode

Runs the experiment on the full dataset (N=64) if the power analysis indicates sufficient statistical power, or as a standalone full run.

**Command:**
```bash
python code/main.py --mode full
```

**Expected Outputs:**
- `results/statistical_summary.json`: Final aggregated metrics and statistical test results.
- `state/checksums.yaml`: Data integrity checksums for processed files.
- `state/artifact_hashes.yaml`: Version hashes for all artifacts.

## Verification

After running a mode, verify the execution by checking the log files and output artifacts.

```bash
# Check the statistical summary
cat results/statistical_summary.json

# Verify data integrity
cat state/checksums.yaml
```

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Configuration Errors**: Verify `config/seeds.yaml` is valid YAML and contains the correct seed list.
- **Logging**: Check the rotating log files in the `logs/` directory for detailed error messages.