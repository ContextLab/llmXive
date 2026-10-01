# Quickstart Guide: Visual Crowding Impact on Facial Emotion Recognition

This guide provides instructions for setting up and running the full analysis pipeline for the
"Impact of Visual Crowding on Facial Emotion Recognition Accuracy" project.

## Prerequisites

- Python 3.10+
- pip package manager
- Access to the RAVDESS dataset (via HuggingFace)
- Minimum 7 GB RAM (for full dataset processing) or 1 GB RAM (for sampled processing)

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Pipeline Overview

The pipeline consists of the following stages:

1. **Data Download**: Fetch RAVDESS dataset
2. **Frame Extraction**: Extract frames from video files
3. **Stimulus Generation**: Create visual crowding stimuli
4. **Clutter Metrics**: Compute visual clutter metrics (US2)
5. **Human Data Collection**: Run pilot study (manual step)
6. **Analysis**: Fit GLMM models and generate reports (US3)

## Running the Pipeline

### Option 1: Full Pipeline (Recommended)

Run the unified pipeline orchestrator:
```bash
python code/run_full_pipeline.py
```

This script executes all stages in the correct order, with error handling and logging.

### Option 2: Individual Stages

You can also run individual stages:

1. **Download Data**:
 ```bash
 python code/utils/download.py
 ```

2. **Extract Frames**:
 ```bash
 python code/utils/frame_extractor.py
 ```

3. **Generate Stimuli**:
 ```bash
 python code/utils/stimulus_gen.py
 ```

4. **Compute Clutter Metrics** (US2):
 ```bash
 python code/utils/clutter_metrics.py
 ```

5. **Run Pilot Study** (Manual):
 ```bash
 python code/analysis/run_pilot.py
 ```
 Note: This requires manual interaction to collect responses from ≥5 participants.

6. **Fit GLMM Model**:
 ```bash
 python code/analysis/glmm_model.py
 ```

7. **Generate Report**:
 ```bash
 python code/analysis/reporting.py
 ```

## Streaming Data Loading Strategy (US2)

The clutter metrics computation (`code/utils/clutter_metrics.py`) implements a chunked processing
strategy to handle large datasets within the 7 GB RAM constraint. This section describes the
implementation details and fallback criteria.

### Chunking Logic

The manifest file (`data/interim/stimuli_manifest.json`) is processed in chunks of 100 entries
by default. For each chunk:

1. Load the chunk of manifest entries into memory.
2. Load the corresponding images one at a time.
3. Compute local contrast variance and spatial frequency energy.
4. Write results to the output CSV immediately (append mode).
5. Clear memory before processing the next chunk.

This ensures that memory usage remains constant regardless of the total number of stimuli.

### Fallback Sampling Criteria

If memory pressure is detected (available memory < 1 GB), the system automatically switches to
a statistically valid random sampling mode:

1. **Detection**: The `should_trigger_fallback()` function checks available memory using `psutil`.
2. **Sampling**: A random subset of stimuli is selected:
 - Sample size = max(1000, 10% of total stimuli)
 - Fixed seed (42) for reproducibility
3. **Logging**: The sampling details are recorded in `data/processed/metrics_sampling_log.txt`:
 - Total stimuli available
 - Number of stimuli sampled
 - Sampling seed
 - Reason for fallback
4. **Processing**: Only the sampled stimuli are processed.

This fallback ensures that the analysis can proceed even when the full dataset cannot be
processed due to hardware constraints, while maintaining statistical validity.

### Memory Management

- Images are loaded one at a time using PIL and explicitly garbage collected after processing.
- Intermediate numpy arrays are deleted immediately after metric computation.
- Results are written to disk in chunks to avoid accumulating large lists in memory.
- The `gc.collect()` function is called after each chunk to force garbage collection.

### Reproducibility

All sampling operations use a fixed random seed (42) to ensure that results are reproducible
across different runs and environments.

## Output Files

The pipeline produces the following key output files:

- `data/processed/clutter_metrics.csv`: Computed clutter metrics for each stimulus
- `data/processed/validation_report.json`: Validation report for the metrics
- `data/processed/human_judgments_aggregates.csv`: Aggregated human judgment data
- `data/processed/regression_results.json`: GLMM regression results
- `artifacts/model_config.yaml`: Model configuration and diagnostics
- `artifacts/final_report.md`: Final associational report

## Troubleshooting

### Memory Errors

If you encounter memory errors:

1. Ensure you have at least 1 GB of available RAM.
2. The pipeline will automatically switch to sampling mode if memory is insufficient.
3. Check `data/processed/metrics_sampling_log.txt` to confirm sampling occurred.

### Missing Dependencies

If you see import errors:

```bash
pip install -r requirements.txt
```

### RAVDESS Dataset Issues

If the dataset download fails:

1. Verify your HuggingFace API token is set correctly.
2. Check your internet connection.
3. Ensure you have sufficient disk space (RAVDESS is ~2 GB).

## Next Steps

After running the pipeline, review the output files and the final report in `artifacts/final_report.md`.
The report frames all findings as associational (per FR-006) and includes model diagnostics.