# PROJ-189: Investigating the Correlation Between Gut Microbiome and Cognitive Decline

## Project Structure

This project follows the llmXive automated science pipeline structure:

- `data/`: Raw and processed data
 - `raw/`: Unmodified source data
 - `processed/`: Cleaned and aggregated data
 - `models/`: Trained model artifacts
- `code/`: Source code for analysis
 - `utils/`: Shared utilities
- `tests/`: Test suites
 - `unit/`: Unit tests
 - `integration/`: Integration tests
 - `contract/`: Contract tests
- `docs/`: Documentation

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. Run the analysis pipeline:
 ```bash
 python code/01_data_ingestion.py
 python code/02_preprocessing.py
 ```

## Data Sources

- AGP 16S Taxonomic Data: Qiita/EBI
- HRS Cognitive Metadata: HRS Portal

## License

Open for research use.
