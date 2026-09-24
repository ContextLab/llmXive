# Quickstart Guide for llmXive Blind-Spots-Bench Analysis

This guide outlines the steps to run the full analysis pipeline.

## Prerequisites

- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`)
- GPU recommended for inference (CPU fallback available)

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Configure project:
 ```bash
 python code/setup_structure.py
 python code/setup_linting.py
 ```

3. Ensure `config.yaml` is present with required keys.

## Pipeline Execution

Run the following commands in order to execute the full pipeline:

### Step 1: Download and Filter Dataset
```bash
python code/01_download_and_filter.py
```
- Downloads `Blind-Spots-Bench` dataset
- Filters for "Abstract Reasoning" and "Object-Centric" categories
- Validates integrity and writes `data/filtered/filtered_tasks.jsonl`
- Generates `data/validation/integrity_error_report.json` if errors found

### Step 2: Pilot Study (Threshold Calibration)
```bash
python code/pilot_study.py
```
- Generates CoT traces for N=10 pilot tasks
- Saves to `data/pilot/pilot_traces.jsonl`

### Step 3: Generate Annotation Request
```bash
python code/generate_pilot_annotation_request.py
```
- Creates request file for human experts to label pilot traces

### Step 4: Ingest Pilot Labels (Manual Step Required First)
> **Manual Step**: Human experts must label the pilot traces and save results to `data/pilot/pilot_ground_truth_labels.jsonl`.
```bash
python code/ingest_pilot_labels.py
```

### Step 5: Tune Semantic Matching Threshold
```bash
python code/tune_threshold.py
```
- Iterates cosine similarity thresholds
- Maximizes agreement with human labels
- Saves optimal threshold to `data/pilot/tuned_threshold.json`

### Step 6: Generate Full CoT Traces
```bash
python code/02_generate_cot.py
```
- Generates CoT traces for all filtered tasks
- Uses tuned threshold from `data/pilot/tuned_threshold.json`
- Saves to `data/traces/cot_traces.jsonl`

### Step 7: Parse and Classify Traces
```bash
python code/03_parse_and_classify.py
```
- Parses traces for constraint mentions
- Classifies errors as Perceptual, Procedural, or Correct
- Saves parsed results to `data/results/parsed_traces.jsonl`

### Step 8: Statistical Analysis
```bash
python code/04_statistical_analysis.py
```
- Computes error type proportions
- Performs statistical tests (Fisher's Exact or Chi-squared)
- Generates `data/results/statistical_report.json`

### Step 9: Validation and Reporting
```bash
python code/generate_annotation_request.py
python code/ingest_human_labels.py
python code/validate_classifier.py
python code/generate_paper_sections.py
python code/update_state.py
```

## Output Artifacts

- `data/filtered/filtered_tasks.jsonl`: Filtered dataset
- `data/validation/integrity_error_report.json`: Integrity check results
- `data/pilot/pilot_traces.jsonl`: Pilot CoT traces
- `data/pilot/pilot_ground_truth_labels.jsonl`: Human-labeled pilot data
- `data/pilot/tuned_threshold.json`: Optimal semantic matching threshold
- `data/traces/cot_traces.jsonl`: Full CoT traces
- `data/results/parsed_traces.jsonl`: Parsed and classified traces
- `data/results/statistical_report.json`: Statistical analysis results
- `data/results/consistency_report.json`: Consistency check results

## Troubleshooting

- If GPU OOM occurs, the pipeline will automatically fall back to CPU or 8-bit quantization.
- If data fetch fails, the pipeline will exit with an error (no synthetic fallback).
- Ensure all paths in `config.yaml` match the actual file locations.