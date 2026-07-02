# Quickstart: The Impact of Linguistic Accommodation on Perceived Empathy in AI Assistants

## Prerequisites
- Python 3.11+
- pip
- Access to the project repository
- Internet access (for downloading DailyDialog and NLTK/spacy models)

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-391-the-impact-of-linguistic-accommodation-o
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

2.  **Download Data & Models**:
    The ingestion script will attempt to download DailyDialog from the verified URLs. Ensure internet access is available.
    ```bash
    python code/main.py --stage download
    ```
    *Note: This also downloads required NLTK and spaCy models.*

## Running the Pipeline

Execute the full pipeline (Ingestion -> Mapping -> Sensitivity -> Analysis -> Visualization):

```bash
python code/main.py --stage full
```

### Individual Stages
- **Ingestion & Metrics**: `python code/main.py --stage ingest`
- **Empathy Mapping**: `python code/main.py --stage map`
- **Sensitivity Analysis**: `python code/main.py --stage sensitivity`
- **Statistical Analysis**: `python code/main.py --stage analyze`
- **Visualization**: `python code/main.py --stage viz`

## Verification

1.  **Check Data**:
    Verify `data/processed/accommodation_metrics.csv` exists and contains no nulls in metric columns.
    ```bash
    python -c "import pandas as pd; df = pd.read_csv('data/processed/accommodation_metrics.csv'); print(df.isnull().sum())"
    ```

2.  **Check Plots**:
    Ensure `outputs/figures/scatter_plot.png` is generated.

3.  **Check Stats**:
    Review `outputs/reports/statistical_summary.md` for correlation coefficients, p-values, and effect size interpretations.

## Troubleshooting

- **Missing Data**: If DailyDialog download fails, check network or verify the URL in `code/data_ingestion.py`.
- **Memory Error**: Unlikely given dataset size. If encountered, reduce batch size in `data_ingestion.py`.
- **POS Tagging Errors**: Ensure `nltk` data is downloaded (`nltk.download('averaged_perceptron_tagger')`).
- **Dependency Parsing Errors**: Ensure `spacy` and the English model are installed (`python -m spacy download en_core_web_sm`).
