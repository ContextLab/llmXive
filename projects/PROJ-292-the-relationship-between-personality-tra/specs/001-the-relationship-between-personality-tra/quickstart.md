# Quickstart: The Relationship Between Personality Traits and Response to Personalized AI Feedback

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-292-the-relationship-between-personality-tra
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

### Expected Output

- **Data**: `data/processed/analysis_data.csv`
- **Results**: `results/analysis_results.json`
- **Plots**: `results/plots/correlation_heatmap.png`, `results/plots/regression_plot.png`
- **Report**: `results/report.md`

### Validation

To verify the data ingestion step independently:

```bash
python code/download.py --validate
```

This will download the dataset, compute the checksum, and verify the presence of required columns.

## Troubleshooting

- **Error: "Missing Personality Data"**: This is expected. The pipeline generates synthetic personality data because no verified source exists. See `research.md` for details.
- **Error: "URL 404"**: Ensure you are using the `ziq` dataset URL. The `ayazosha` URL is deprecated and excluded.
- **OOM Error**: The pipeline is optimized for 7GB RAM. If OOM occurs, reduce the dataset sample size in `config.py`.
