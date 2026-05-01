# Config.yaml Compliance Verification (T089)

## Purpose

This script verifies that `config.yaml` adheres to Constitution Principle I by
containing only hyperparameters, random seeds, and base paths—NO derived statistics.

## What Constitutes a Violation

Derived statistics that should NOT be in config.yaml include:

- **Dataset metadata**: observation counts, file sizes, checksums
- **Runtime metrics**: elapsed time, memory usage, duration
- **Performance metrics**: F1-score, precision, recall, AUC
- **Model metrics**: learned cluster counts, ELBO values, convergence status
- **Calibrated thresholds**: thresholds computed from data (use base thresholds only)
- **Timestamps**: last_updated, created_at, processed_at

## Usage

```bash
# Check compliance (read-only)
python code/scripts/verify_config_compliance.py

# Automatically fix violations
python code/scripts/verify_config_compliance.py --fix
```

## Output

The script produces:

1. **Console report**: Lists all violations with suggested actions
2. **Updated config.yaml**: If --fix is used, removes derived statistics
3. **Updated state file**: Stores derived statistics in `derived_statistics` section

## Example Violation

```yaml
# BAD - in config.yaml:
datasets:
  electricity:
    observation_count: 45211  # <-- VIOLATION: derived from data

# GOOD - in config.yaml:
datasets:
  electricity:
    url: "https://..."  # only base paths/URLs

# GOOD - in state file:
derived_statistics:
  datasets.electricity.observation_count:
    value: 45211
    reason: "Dataset metadata derived from raw data"
```

## Relation to T073

T073 required reducing config.yaml from 11KB to under 2KB. This script enforces
that requirement by identifying and removing derived statistics that bloat the
config file.

## Validation

After running with --fix, verify:

1. config.yaml is under 2KB
2. All checksums are in state file, not config
3. All observation counts are in state file, not config
4. config.yaml contains only: seeds, hyperparameters, base paths/URLs