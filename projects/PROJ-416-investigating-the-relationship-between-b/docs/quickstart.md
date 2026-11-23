# Quickstart Guide

This guide walks you through setting up and running the Brain Network Dynamics and VR Therapy Response analysis pipeline.

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- 2 CPU cores, 7GB RAM, 14GB disk
- Internet connection (for initial data download)

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 git clone <repository-url>
 cd PROJ-416-investigating-the-relationship-between-b
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure environment variables (optional, for custom paths):
 ```bash
 cp.env.example.env
 # Edit.env with your configuration
 ```

## Running the Pipeline

The pipeline consists of several stages that must be run in order:

1. **Verify Source**: Ensure the data source is valid
 ```bash
 python code/scripts/verify_gate.py
 ```

2. **Download**: Fetch data from OpenNeuro
 ```bash
 python code/main.py --stage download
 ```

3. **Validate**: Check data integrity and required variables
 ```bash
 python code/main.py --stage validate
 ```

4. **Preprocess**: Apply motion correction, slice timing, normalization
 ```bash
 python code/main.py --stage preprocess
 ```

5. **Compute Metrics**: Calculate network properties
 ```bash
 python code/main.py --stage compute
 ```

6. **Analyze**: Perform statistical analysis
 ```bash
 python code/main.py --stage analyze
 ```

7. **Generate Report**: Create final results report
 ```bash
 python code/main.py --stage report
 ```

8. **Full Validation**: Run end-to-end validation
 ```bash
 python code/scripts/run_quickstart_validation.py
 ```

## Troubleshooting

### Data Unavailable Halt

**Symptom**: Pipeline exits with "Data Unavailable: No longitudinal dataset found"

**Cause**: The multi-source data aggregation (T001a) failed to find a dataset with:
- Resting-state fMRI (NIfTI)
- Paired pre/post clinical scores
- Validated anxiety instrument (GAD-7, HAM-A, BAI)

**Resolution**:
1. Check `data/verified_sources.json` to see which sources were checked
2. Verify the OpenNeuro ID is correct and the dataset exists
3. Ensure the dataset contains the required variables (pre/post scores, anxiety instrument)
4. If no suitable dataset exists, the pipeline must halt - do not proceed with non-VR data

### Checking Verified Source File

**Symptom**: "Missing verified dataset source" or "FatalError" during download

**How to verify**:
```bash
cat data/verified_sources.json
```

**Expected schema**:
```json
{
 "source_name": "OpenNeuro",
 "dataset_id": "ds00XXXX",
 "verified_date": "YYYY-MM-DD",
 "notes": "Dataset contains resting-state fMRI and GAD-7 scores",
 "has_pre_post": true,
 "has_clinical_scores": true
}
```

**Actions**:
- If file is missing: Run T001a (multi-source aggregation) to populate it
- If file is corrupted: Delete and re-run the aggregation script
- If `dataset_id` is invalid: Check OpenNeuro for the correct ID

### Manual Verification of "Verified Source" Gate

**Purpose**: Ensure the gate correctly blocks invalid data sources

**Steps**:
1. Temporarily rename `data/verified_sources.json`:
 ```bash
 mv data/verified_sources.json data/verified_sources.json.bak
 ```

2. Attempt to run download stage:
 ```bash
 python code/main.py --stage download
 ```

3. Expected result: Pipeline exits with code 1 and message "Missing verified dataset source"

4. Restore the file:
 ```bash
 mv data/verified_sources.json.bak data/verified_sources.json
 ```

5. Check logs for confirmation:
 ```bash
 grep "Verified Source Gate Active" logs/validation.log
 ```

### Underpowered Warning

**Symptom**: "WARNING: Underpowered for hypothesis testing (Power < 0.8)" in reports

**Cause**: Sample size (N) is below the minimum required for 80% power at effect size f²=0.15

**Resolution**:
1. Check `data/metrics/power_analysis.json` for the exact `min_N_required` value
2. If N < 5: Pipeline will HALT with "Insufficient Power: N < 5"
3. If 5 ≤ N < min_N_required: Results are in "Exploratory Mode" (effect sizes only, no p-value claims)
4. To resolve: Collect more subjects or adjust effect size expectations

**Note**: This is a methodological constraint, not a bug. The pipeline correctly identifies and reports power limitations.

### Module Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'dotenv'` or similar

**Resolution**:
```bash
pip install python-dotenv
pip install -r requirements.txt # Ensure all dependencies are installed
```

### Missing Output Files

**Symptom**: Declared deliverables (e.g., `data/metrics/statistical_results.csv`) are absent

**Resolution**:
1. Check if previous stages completed successfully
2. Review logs for errors: `tail -f logs/pipeline.log`
3. Ensure the script that produces the file is invoked (check `quickstart.md` run-book)
4. For `statistical_results.csv`: Run `python code/analysis/save_stats_results.py`

### Motion Exclusion

**Symptom**: Many subjects excluded due to motion (>3mm translation or >3° rotation)

**Resolution**:
1. Check `data/metrics/qc_metrics.csv` for exclusion reasons
2. Review preprocessing parameters in `code/data/preprocess.py`
3. Consider if motion thresholds are appropriate for your dataset
4. Log is in `logs/preprocessing.log`

## Output Files

Key outputs are stored in:

- `data/processed/`: Preprocessed NIfTI files
- `data/metrics/`: QC metrics, network metrics, statistical results
- `reports/`: Final analysis report, sensitivity analysis
- `logs/`: Pipeline execution logs

## Support

For issues not covered here, check:
- `logs/pipeline.log` for detailed error messages
- `docs/CONTRIBUTING.md` for development guidelines
- Project README for known limitations