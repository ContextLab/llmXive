# Deployment Guide

## Environment
- Python 3.11+
- Linux/Unix recommended

## Dependencies
Install all dependencies from `requirements.txt`.

## Configuration
- Set `DATA_RAW`, `DATA_PROCESSED`, `PRIMES`, `TARGETS`, `STATE` in `code/config.py`.
- Ensure `state/projects/PROJ-345/state.yaml` is initialized.

## Execution
1. Run `python code/run_state_init.py`.
2. Run `python code/data/ingest.py`.
3. Run `python code/data/preprocess.py`.
4. Run `python code/models/lmm.py`.
5. Run `python code/reports/generate_report.py`.

## Output
- `reports/final_analysis_report.pdf`
- `state/model_convergence_metrics.json`
- `data/processed/linked_trials.csv`

## Monitoring
- Check logs for errors and warnings.
- Verify `state.yaml` for artifact checksums.
- Run `python code/validation/validate_quickstart.py` for final validation.

## Rollback
If issues arise, restore `state.yaml` to a previous version and re-run the pipeline.
