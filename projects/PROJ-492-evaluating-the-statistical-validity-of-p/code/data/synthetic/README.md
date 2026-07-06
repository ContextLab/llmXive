# Synthetic Dataset for A/B Test Validity Evaluation

## Overview
This directory contains synthetic A/B test summaries generated to validate the statistical consistency audit pipeline (FR-030).

## Files
- `synthetic_summaries.csv`: Main dataset in CSV format with 10,000+ records
- `synthetic_summaries.json`: Main dataset in JSON format
- `synthetic_metadata.json`: Generation metadata including counts and statistics
- `README.md`: This documentation file

## Generation Parameters
- **Total Records**: 10,000+ (as per FR-030 requirement)
- **Outcome Types**: Both binary and continuous outcomes included
- **Seed**: 42 (reproducible)
- **Inconsistency Rate**: ~15% of records have injected statistical inconsistencies

## Outcome Type Distribution
- Binary outcomes: ~50% (conversion rates, success/failure metrics)
- Continuous outcomes: ~50% (revenue, time-on-site, engagement metrics)

## Usage
Run the generator script to regenerate:
```bash
python code/src/audit/synthetic.py --n-records 10000 --seed 42
```

## Validation
The dataset satisfies FR-030 requirements:
- ✅ At least 10,000 simulated summaries
- ✅ Both binary AND continuous outcomes present
- ✅ Reproducible via fixed random seed
- ✅ Includes metadata for verification