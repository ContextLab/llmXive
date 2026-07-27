# llmXive: Extending VideoKR Towards Knowledge- and Reasoning-Intensive Video Understanding

This project implements a pipeline to analyze the VideoKR-SFT dataset, annotating questions with structural chain lengths (hops) from a knowledge graph. It then performs statistical analysis to detect non-linear "reasoning cliffs" where accuracy drops significantly as the required reasoning depth increases.

## Project Structure

```
.
├── code/ # Source code for the pipeline
│ ├── ingest/ # Data ingestion and annotation scripts
│ ├── analysis/ # Statistical analysis and plotting scripts
│ └── utils/ # Utility functions (config, graph utils, etc.)
├── data/ # Data storage
│ ├── raw/ # Raw downloaded datasets (VideoKR-SFT, KG)
│ └── processed/ # Annotated data, plots, and analysis results
├── tests/ # Unit and integration tests
├── docs/ # Documentation
└── specs/ # Feature specifications and design docs
```

## Prerequisites

- Python 3.9+
- Required Python packages listed in `requirements.txt`

## Data Requirements

The pipeline requires two primary datasets, which are automatically downloaded by the ingestion script:

1. **VideoKR-SFT**: The Video-Knowledge-Reasoning SFT dataset.
 - Source: Verified URL (e.g., HuggingFace or specific repository).
 - Purpose: Source of questions and answers to be annotated.
2. **Knowledge Graph**: A graph structure representing entities and relationships.
 - Source: Verified URL or local file (as per `specs/001-video-reasoning-threshold`).
 - Purpose: Used to calculate the shortest path (chain length) between entities in questions.

If the data is not present in `data/raw/`, run the download script first.

## Usage

### Running the Full Pipeline

The entire pipeline can be executed end-to-end using the main entry point. This script orchestrates data download, annotation, statistical analysis, and report generation.

```bash
python code/main.py
```

**Note**: `code/main.py` is not yet implemented in this specific task scope but is the intended entry point. Currently, you must run the stages sequentially:

1. **Ingestion & Annotation**:
 ```bash
 python code/ingest/download_data.py
 python code/ingest/annotate_graph.py
 python code/ingest/calculate_annotation_coverage.py
 ```
2. **Analysis (US2 & US3)**:
 ```bash
 python code/analysis/stratify_accuracy.py
 python code/analysis/detect_threshold.py
 python code/analysis/generate_binned_summary.py
 python code/analysis/generate_plots.py
 python code/analysis/sensitivity.py
 python code/analysis/generate_sensitivity_report.py
 ```
3. **Final Reporting**:
 ```bash
 python code/analysis/generate_final_report.py
 ```

### Running Individual Scripts

Each script in `code/` is designed to be runnable independently. They accept no command-line arguments by default and rely on configuration in `code/utils/config.py`.

Example:
```bash
python code/ingest/annotate_graph.py
```

## Output Artifacts

Upon successful completion of the pipeline, the following artifacts will be generated in the `data/processed/` directory:

### Data Artifacts
- `annotated_videokr.csv`: The VideoKR-SFT dataset with added columns:
 - `chain_length`: Exact integer shortest path hops.
 - `chain_bin`: Categorical bin (1, 2, 3+).
 - `correctness`: Answer correctness.
- `annotation_coverage.json`: Statistics on the annotation process (total input, unmapped, annotated counts).
- `accuracy_vs_hop_raw.csv`: Raw data points for continuous plotting.
- `sensitivity_thresholds.csv`: Results of the threshold sensitivity sweep.
- `stability_metric.json`: Final robustness status (PASS/FAIL).

### Visualizations
- `accuracy_vs_hop_raw.png`: Scatter plot with LOESS trend line showing accuracy vs. hop count.
- `accuracy_binned.png`: Bar plot of accuracy per hop bin.
- `sensitivity_overlay.png`: Overlay plot of accuracy curves for different threshold definitions.

### Reports & Logs
- `threshold_results.json`: Statistical test results (p-value, effect size, optimal knot).
- `sensitivity_summary.md`: Markdown summary of the sensitivity analysis.
- `sensitivity_report.md`: Detailed report including robustness conclusion.
- `final_report.md`: Aggregated final report containing all results and methodology notes.
- `runtime_log.json`: End-to-end runtime measurement.
- `memory_log.json`: Peak memory usage measurement.
- `methodology_override.md`: Documentation of the GAM rejection and permutation test usage.

## Configuration

Configuration is managed via `code/utils/config.py`. Key settings include:
- `PROJECT_ROOT`: The root directory of the project.
- `SEED`: Random seed for reproducibility.
- `DATA_PATHS`: Paths to raw and processed data directories.

## Testing

Run unit and integration tests using `pytest`:

```bash
pytest tests/
```

## Methodology Notes

- **Threshold Detection**: Uses a Permutation Test (n=1000) for change-point detection, as specified in the project Plan, overriding the Spec's initial LRT requirement.
- **GAMs**: Generalized Additive Models (GAMs) are explicitly rejected for this analysis due to statistical invalidity on discrete ordinal variables, as documented in `methodology_override.md`.

## License

[Project License]
