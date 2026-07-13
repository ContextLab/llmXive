# llmXive Follow-up: Quick Start Guide

This guide outlines the steps to execute the **Enhancing Train-Free Infinite-Frame Generation** pipeline on CPU-only environments.

## Prerequisites

### 1. Python Environment
Ensure you have Python 3.9+ installed. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. System Requirements
- **CPU**: 2+ cores (Recommended: 4+)
- **RAM**: Minimum 16GB (6GB limit enforced in code for safety)
- **Disk**: ~20GB free space for datasets and intermediate results
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows (WSL2)

## Project Structure

```text
PROJ-874-llmxive-follow-up-extending-enhancing-tr/
├── code/ # Main implementation
│ ├── config.py # Configuration and logging
│ ├── download.py # Dataset fetching
│ ├── generate.py # Baseline video generation
│ ├── correct.py # Optical flow correction
│ ├── evaluate.py # Metric calculation
│ ├── analyze.py # Statistical analysis
│ ├── pilot_study.py # Pilot variance calculation
│ └── utils/ # Helper modules (video, flow, artifacts)
├── data/
│ ├── raw/ # Downloaded datasets (NarrLV, VBench)
│ ├── processed/ # Intermediate frames and flow fields
│ └── results/ # Final metrics and logs
├── tests/ # Unit, integration, and contract tests
├── docs/ # Documentation
└── quickstart.md # This file
```

## Step-by-Step Execution

### Step 1: Dataset Download
Before generating videos, ensure all required datasets (NarrLV and VBench) are present.

```bash
python code/download.py
```

**CLI Flags:**
- `--force`: Re-download even if files exist
- `--verbose`: Show detailed download progress

**Validation:**
The script performs a pre-flight check (T012a) to verify all required files exist before proceeding. If any are missing, it aborts with a clear error message listing the missing files.

### Step 2: Baseline Generation (User Story 1)
Generate baseline videos in two modes:

**Naive Baseline (No Self-Reflection):**
```bash
python code/generate.py --mode baseline-naive
```

**Full Self-Reflection Baseline:**
```bash
python code/generate.py --mode baseline-full
```

**CLI Flags:**
- `--mode`: `baseline-naive` or `baseline-full` (Required)
- `--dataset`: Name of the dataset to process (default: all)
- `--seed`: Random seed for reproducibility (default: 42)
- `--profile-memory`: Enable memory profiling (logs peak RSS to `results/memory_profile.log`)

**Output:**
- Videos saved to `data/results/baseline_<mode>/`
- Logs include wall-clock time per video (T014)

### Step 3: Pilot Study (Prerequisite for Statistical Analysis)
Run a small pilot study (N=5) to estimate variance for power analysis.

```bash
python code/pilot_study.py
```

**Output:**
- `data/pilot_variance.json`: Contains `mean`, `std`, `n_samples`, and `metric_name`.

### Step 4: Flow Correction (User Story 2)
Apply RAFT-Small optical flow correction to the naive baseline outputs.

```bash
python code/correct.py
```

**CLI Flags:**
- `--precision`: `fp16` or `fp32` (Auto-fallback if FP16 OOM)
- `--input-dir`: Path to naive baseline videos (default: auto-detected)

**Note:** This step requires the naive baseline videos from Step 2. If missing, the script aborts with an error (T021).

**Output:**
- Warped videos and flow fields saved to `data/results/corrected/`
- Memory and timing logs in `results/`

### Step 5: Evaluation and Analysis (User Story 3)
Compute metrics (VBench, FVD, Object Permanence) and perform statistical testing.

**Evaluate:**
```bash
python code/evaluate.py
```

**Analyze:**
```bash
python code/analyze.py
```

**CLI Flags (analyze.py):**
- `--pilot-file`: Path to `data/pilot_variance.json` (default: auto-detected)
- `--alpha`: Significance level for tests (default: 0.05)

**Power Analysis (T030a):**
The `analyze.py` script automatically calculates statistical power. If power < 0.8, it flags the study as underpowered and may abort subsequent tests (T027/T028) or mark them as invalid.

**Output:**
- `data/results/metrics.csv`: Detailed metrics per video.
- `data/results/failure_cases.json`: Videos with significant drops in Object Permanence or VBench score.
- `data/results/analysis_summary.txt`: Statistical summary including p-values and test types.

## Dataset Requirements

The pipeline requires the following datasets, automatically fetched via HuggingFace `datasets` library:

1. **NarrLV**: Long-form video generation benchmark.
2. **VBench**: Video quality assessment benchmark.

If these are not present in `data/raw/`, `code/download.py` will attempt to fetch them. Ensure you have internet access during the download step.

## Troubleshooting

- **OOM Errors**: If you encounter Out-of-Memory errors, ensure `code/config.py` memory limits are respected. The `--profile-memory` flag can help diagnose peak usage.
- **Missing Files**: If the script aborts citing missing files, run `code/download.py` first or check `data/raw/` manually.
- **Flow Estimation Failures**: If RAFT-Small fails (e.g., due to motion blur), the pipeline automatically falls back to nearest-neighbor interpolation (T023) and logs the event.

## Verification

To verify the entire pipeline end-to-end:

```bash
# 1. Download
python code/download.py

# 2. Generate Naive
python code/generate.py --mode baseline-naive

# 3. Pilot Study
python code/pilot_study.py

# 4. Correct
python code/correct.py

# 5. Evaluate & Analyze
python code/evaluate.py
python code/analyze.py
```

Ensure all output files (`data/results/*.csv`, `data/results/*.json`, `figures/*.png`) are generated successfully.