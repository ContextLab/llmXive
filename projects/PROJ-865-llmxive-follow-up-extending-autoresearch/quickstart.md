# Quickstart Guide: llmXive Follow-up (AutoResearchClaw Extension)

This guide provides instructions for running the full pipeline, including data ingestion, rule distillation, execution, and statistical analysis.

## Prerequisites

1. **Python Environment**: Ensure Python 3.10+ is installed.
2. **Dependencies**: Install required packages:
 ```bash
 pip install -r requirements.txt
 ```
3. **Directory Structure**: Run the setup script to create necessary directories:
 ```bash
 python code/utils/setup_dirs.py
 ```

## Running the Pipeline

The pipeline is executed in stages. Ensure you have completed the previous stages before proceeding.

### Stage 1: Ingest and Distill

Fetch the ARC-Bench dataset, annotate failures, and distill rules.

```bash
python code/01_data_ingestion/download_arc_bench.py
python code/02_annotation_distillation/annotate_failures.py
python code/02_annotation_distillation/distill_rules.py
python code/02_annotation_distillation/validate_rules.py
python code/02_annotation_distillation/verify_quantization.py
```

### Stage 2: Execute and Compare

Run the rule engine and the baseline agent on the test manifest, then merge results.

```bash
python code/03_execution/generate_manifest.py
python code/03_execution/run_experiments.py
python code/03_execution/run_baseline.py --manifest data/derived/experiment_manifest.csv --output data/derived/baseline_results.json
python code/03_execution/merge_results.py
```

### Stage 3: Analyze

Perform statistical analysis and generate the final report.

```bash
python code/04_analysis/statistical_model.py
python code/04_analysis/time_diff_tobit.py
python code/04_analysis/calculate_stratified_rates.py
python code/04_analysis/error_taxonomy.py
python code/04_analysis/paired_test.py
python code/04_analysis/visualize_censored_data.py
python code/04_analysis/generate_report.py
python code/04_analysis/generate_executive_summary.py
```

## Running the Baseline

To run the baseline agent specifically (after the manifest has been generated):

1. **Ensure baseline agent is installed**: Verify that the baseline simulation logic is available in `code/03_execution/run_baseline.py`.
2. **Run the baseline script**: Execute the following command, replacing the manifest path if necessary:
 ```bash
 python code/03_execution/run_baseline.py --manifest data/derived/experiment_manifest.csv --output data/derived/baseline_results.json
 ```
3. **Wait for completion**: The script will process each task in the manifest and write the results to `data/derived/baseline_results.json`.
4. **Verify output**: Check that `data/derived/baseline_results.json` exists and contains valid JSON with keys `task_id`, `method`, `time_to_pivot`, `success`, and `failure_type`.

## Full Orchestration

Once all components are implemented, you can run the entire pipeline via the main orchestration script:

```bash
python code/main.py
```

## Troubleshooting

- **Missing Data**: If `data/derived/` files are missing, ensure you have run the ingestion and distillation stages first.
- **Dataset Errors**: If the dataset download fails, check your internet connection and verify the dataset ID in `code/01_data_ingestion/download_arc_bench.py`.
- **Resource Limits**: If you encounter memory errors, ensure your system meets the requirements defined in `code/utils/config.py`.