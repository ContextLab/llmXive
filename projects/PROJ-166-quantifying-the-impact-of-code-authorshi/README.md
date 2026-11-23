# Quantifying the Impact of Code Authorship Diversity on Software Security

This project analyzes the relationship between code authorship diversity and software security vulnerabilities using a dataset of GitHub repositories and NVD/CVE data.

## Project Structure

- `code/`: Source code for data processing and analysis
 - `config.py`: Configuration and utility functions
 - `data/`: Data ingestion and processing modules
 - `analysis/`: Statistical modeling and reporting modules
- `data/`: Data storage
 - `raw/`: Raw data from external sources
 - `processed/`: Processed and cleaned data
- `tests/`: Test suites
 - `unit/`: Unit tests
 - `integration/`: Integration tests
 - `contract/`: Contract tests
- `contracts/`: Data schema definitions
- `docs/`: Documentation and reports

## Setup

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set environment variables:
 ```bash
 export GITHUB_TOKEN=your_github_token
 export NVD_API_KEY=your_nvd_api_key
 ```

## Usage

Run the data pipeline:
```bash
python code/data/generate_target_list.py
python code/data/download_nvd.py
python code/data/extract_github.py
python code/data/merge_datasets.py
```

Run analysis:
```bash
python code/analysis/fit_models.py
python code/analysis/robustness.py
python code/analysis/generate_final_report.py
```

## Requirements

- Python 3.11+
- `cloc` (for line counting)
- Git

## License

MIT
