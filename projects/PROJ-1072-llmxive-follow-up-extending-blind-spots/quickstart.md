# Quickstart Guide: llmXive - Blind Spots Bench Follow-up

This guide explains how to run the pipeline end-to-end to reproduce the study on Blind Spots in Multimodal Models.

## Prerequisites

- Python 3.11+
- Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Ensure `config.yaml` is populated with the correct dataset URL and model settings.
Run the URL verification step first:
```bash
python code/00_verify_dataset_url.py
```

## Execution Steps

The pipeline consists of several sequential steps. Run them in order.

### Step 1: Dataset Acquisition and Filtering (US1)
Downloads the dataset, filters for relevant categories, and validates integrity.
```bash
python code/01_download_and_filter.py
```
**Output**: `data/filtered/filtered_tasks.jsonl`, `data/validation/integrity_pass.json`

### Step 2: Pilot Study (US2)
Generates a small set of CoT traces for threshold tuning.
```bash
python code/pilot_study.py
```
**Output**: `data/pilot/pilot_traces.jsonl`

### Step 3: Human Annotation (Manual)
**Required**: Human experts must label the pilot traces.
1. Run `python code/generate_pilot_annotation_request.py` to generate the request file.
2. Manually label the traces and save to `data/pilot/pilot_ground_truth_labels.jsonl`.
**Note**: The pipeline will halt if this file is missing.

### Step 4: Threshold Tuning (US2 - T019)
Computes the optimal semantic matching threshold based on human labels.
```bash
python code/tune_threshold.py
```
**Output**: `data/pilot/tuned_threshold.json`

### Step 5: Full CoT Generation (US2)
Generates CoT traces for the full filtered dataset using the tuned threshold.
```bash
python code/02_generate_cot.py
```
**Output**: `data/traces/cot_traces.jsonl`

### Step 6: Parsing and Classification (US2/US3)
Parses traces for constraint mentions and classifies errors.
```bash
python code/03_parse_and_classify.py
```
**Output**: `data/results/parsed_traces.jsonl`

### Step 7: Statistical Analysis (US3)
Performs statistical tests on the classified errors.
```bash
python code/04_statistical_analysis.py
```
**Output**: `data/results/statistical_report.json`

## Running the Full Pipeline

To run the entire pipeline (excluding manual steps), execute:
```bash
bash code/run_pipeline.sh
```
*Note: Ensure manual annotation (Step 3) is completed before running the full script.*