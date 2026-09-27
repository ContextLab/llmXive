# Quickstart Guide: llmXive Blind-Spots-Bench Analysis

This guide walks you through the end-to-end execution of the research pipeline.
Ensure all prerequisites are installed and the project structure is correct.

## Prerequisites

1. Python 3.11+
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution Steps

The pipeline is executed in the following order. Each step produces specific artifacts.

### Step 1: Acquire and Filter Data (US1)

Downloads the Blind-Spots-Bench dataset, filters for target categories, and validates integrity.

```bash
python code/01_download_and_filter.py
```

**Outputs:**
- `data/filtered/filtered_tasks.jsonl`
- `data/validation/integrity_pass.json` (or `integrity_error_report.json` on failure)

### Step 2: Pilot Study (US2)

Generates CoT traces for a small pilot set (N=10) to calibrate the semantic matcher.

```bash
python code/pilot_study.py
```

**Outputs:**
- `data/pilot/pilot_traces.jsonl`

### Step 3: Ingest Pilot Labels (US2)

(Manual Step: Human experts label `data/pilot/pilot_traces.jsonl` and save to `data/pilot/pilot_ground_truth_labels.jsonl`)

Then ingest the labels:
```bash
python code/ingest_pilot_labels.py
```

### Step 4: Tune Threshold (US2)

Iterates cosine similarity thresholds to maximize agreement with human labels.

```bash
python code/tune_threshold.py
```

**Outputs:**
- `data/pilot/tuned_threshold.json` (Required for Step 5)

### Step 5: Generate CoT Traces (US2)

Generates full CoT traces for the filtered dataset using the tuned threshold.

```bash
python code/02_generate_cot.py
```

**Outputs:**
- `data/traces/cot_traces.jsonl`

### Step 6: Parse and Classify (US2/US3)

Parses traces for constraint mentions and classifies errors.

```bash
python code/03_parse_and_classify.py
```

**Outputs:**
- `data/results/parsed_traces.jsonl`

### Step 7: Statistical Analysis (US3)

Performs statistical tests on the classified errors.

```bash
python code/04_statistical_analysis.py
```

**Outputs:**
- `data/results/statistical_report.json`

## Full Run (Sample Size 5 for Testing)

For a quick end-to-end test with a small sample:

```bash
python code/01_download_and_filter.py
python code/pilot_study.py --sample-size 5
python code/ingest_pilot_labels.py
python code/tune_threshold.py
python code/02_generate_cot.py --sample-size 5
python code/03_parse_and_classify.py
python code/04_statistical_analysis.py
```

## Verification

After running, verify the presence of key artifacts:
- `data/filtered/filtered_tasks.jsonl`
- `data/pilot/tuned_threshold.json`
- `data/traces/cot_traces.jsonl`
- `data/results/statistical_report.json`
