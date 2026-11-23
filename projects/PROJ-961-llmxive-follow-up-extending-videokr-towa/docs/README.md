# llmXive: VideoKR Follow-up (Extending VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding)

**Project ID**: PROJ-961-llmxive-follow-up-extending-videokr-towa

This project implements an automated science pipeline to analyze the "reasoning cliff" in video understanding tasks. It extends the VideoKR-SFT dataset with structural chain lengths (hops) derived from a knowledge graph and performs statistical threshold detection using permutation tests.

## Usage

### Prerequisites

1. **Python**: 3.9+
2. **Dependencies**: Install all requirements listed in `requirements.txt`.
3. **Data**: The pipeline expects raw data files to be present in `data/raw/`. If not present, run the ingestion step first (see below).

### Running the Pipeline

The entire pipeline is orchestrated by a single entry point. To execute the full analysis workflow:

```bash
python code/main.py
```

This script:
1. Initializes the environment and logs start time/memory.
2. Executes the data ingestion, annotation, stratification, threshold detection, and sensitivity analysis modules.
3. Generates all final artifacts (CSVs, JSONs, Plots, Reports).
4. Writes runtime and memory logs to `data/processed/`.

**Note**: If any step fails, the error is logged to `data/processed/error_log.txt`, but the runtime logs will still be generated to allow for debugging.

### Data Requirements

The pipeline requires the following datasets, which must be placed in `data/raw/` or downloaded via the ingestion script (`code/ingest/download_data.py`):

1. **VideoKR-SFT**:
 - **Source**: Hugging Face Datasets (`video-knowledge-reasoning/videoKR-SFT` or similar verified ID).
 - **Description**: The core dataset containing video questions, answers, and ground truth correctness labels.
 - **Format**: Parquet or JSONL (handled via `datasets` library).

2. **Knowledge Graph**:
 - **Source**: Verified URL (e.g., from the VideoKR paper repository or UCI/NAB archive).
 - **Description**: A graph of entities and relationships used to calculate the shortest path (chain length) between question entities.
 - **Format**: CSV or JSON (edges list).

If the data is missing, run the ingestion script manually:
```bash
python code/ingest/download_data.py
```

## Output Artifacts

Upon successful completion of `code/main.py`, the following artifacts will be generated in the `data/processed/` directory:

### Data Artifacts
- `annotated_videokr.csv`: The VideoKR-SFT dataset enriched with `chain_length` (exact hops) and `chain_bin` (1, 2, 3+).
- `accuracy_vs_hop_raw.csv`: Aggregated accuracy statistics per hop count.
- `sensitivity_thresholds.csv`: Results of the sensitivity analysis across different threshold definitions.

### Statistical Results
- `annotation_coverage.json`: Metrics on data coverage and unmapped entity counts.
- `bin_config.json`: The final binning strategy used for statistical testing (merged/deferred status).
- `threshold_results.json`: The primary result of the permutation test (optimal knot, p-value, significance).
- `sensitivity_intermediate.json`: Detailed intermediate results for the sensitivity sweep.
- `stability_metric.json`: Robustness status (PASS/FAIL) based on the stability of the threshold detection.

### Visualizations
- `accuracy_vs_hop_raw.png`: Scatter plot with LOESS trend line showing accuracy vs. hop count.
- `accuracy_binned.png`: Bar plot showing accuracy per hop bin.
- `sensitivity_overlay.png`: Overlay of accuracy curves for different threshold definitions.

### Reports & Logs
- `final_report.md`: A comprehensive Markdown report aggregating all findings, methodology, and conclusions.
- `runtime_log.json`: Total runtime and pipeline success flag.
- `memory_log.json`: Peak memory usage statistics.
- `error_log.txt`: Detailed error messages if any pipeline step failed.

## Project Structure

```text
.
├── code/
│ ├── main.py # Orchestrator Entry Point
│ ├── ingest/ # Data downloading and annotation
│ ├── analysis/ # Statistical analysis and visualization
│ ├── utils/ # Configuration, graph utilities, versioning
│ └──...
├── data/
│ ├── raw/ # Source datasets (VideoKR-SFT, KG)
│ └── processed/ # Generated artifacts
├── tests/ # Unit and integration tests
├── docs/ # Documentation
└── requirements.txt # Python dependencies
```

## License

This project is part of the llmXive automated science pipeline.
