# Quickstart: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

## Prerequisites

- **Python**: Version 3.11 or higher.
- **Java**: JDK 11 or higher (required for Defects4J framework).
- **Git**: To clone the Defects4J repository.
- **Defects4J CLI**: Installed and configured (see `).
- **Memory**: At least 7 GB available RAM.
- **Disk**: At least 14 GB free space.

## Installation

1. **Clone the Repository**:
 ```bash
 git clone <repository-url>
 cd <project-root>
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: Ensure `defects4j` is installed on your system and in your PATH.*

## Running the Pipeline

The pipeline is executed via a single orchestration script that handles data ingestion, metric extraction, analysis, and modeling.

```bash
# Run the full pipeline
python code/run_pipeline.py
```

### Expected Output

Upon successful completion, the following artifacts will be generated in `code/data/processed/`:

- `features.csv`: The labeled feature matrix.
- `correlation_report.json`: Point-Biserial and Spearman correlation results, including VIF scores.
- `model_performance.json`: ROC-AUC and F1 scores from cross-validation.
- `statistical_test.json`: P-values from the Paired Permutation Test.
- `feature_importance.json`: Ranked list of metrics from Random Forest.
- `plots/`: Directory containing generated bar charts and correlation heatmaps.

### Verification

To verify the pipeline ran correctly:

1. Check that `features.csv` exists and has no null values in the metric columns.
2. Ensure the `is_buggy` column contains only 0s and 1s.
3. Confirm that `statistical_test.json` contains a p-value (result of the permutation test).
4. Verify that `correlation_report.json` includes VIF scores.

## Troubleshooting

- **Memory Error**: If the script crashes due to memory, reduce the number of selected projects in `code/src/ingest.py` (e.g., from 10 to 5).
- **Parsing Errors**: Check `code/data/processed/exclusion_log.txt` for files that failed to parse.
- **Defects4J Not Found**: Ensure `defects4j` is installed and `JAVA_HOME` is set correctly.
- **Labeling Error**: Verify that the `defects4j` framework is correctly configured and can retrieve bug info.

## Next Steps

- Review `research.md` for detailed methodology.
- Examine `data-model.md` for schema details.
- Run `pytest tests/` to validate individual components.