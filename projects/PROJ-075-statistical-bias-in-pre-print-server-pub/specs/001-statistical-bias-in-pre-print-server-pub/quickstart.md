# Quickstart: Statistical Bias in Pre-Print Server Publication Trends

## Prerequisites

- Python 3.11 or higher
- `pip` (Python package manager)
- Git (for cloning the repository)
- At least 15GB of free disk space (for PDFs and metadata)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-075-statistical-bias-in-pre-print-server-pub
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### Step 1: Fetch Metadata

```bash
python code/fetch/openalex_loader.py --stream --cache-dir data/raw/openalex_metadata
python code/fetch/arxiv_biorxiv_scraper.py --year 2018-2023 --output data/raw/arxiv_metadata data/raw/biorxiv_metadata
```

### Step 2: Match Pre-prints to Journals

```bash
python code/match/fuzzy_matcher.py --input data/raw/arxiv_metadata data/raw/biorxiv_metadata --output data/processed/matched_pairs.csv
```

### Step 3: Extract Statistical Metrics

```bash
python code/extract/stats_extractor.py --input data/processed/matched_pairs.csv --output data/processed/extracted_metrics.csv
```

### Step 4: Run Analysis

```bash
python code/analysis/p_curve.py --input data/processed/extracted_metrics.csv --output data/results/p_curve_results.json
python code/analysis/effect_size.py --input data/processed/extracted_metrics.csv --output data/results/effect_size_results.json
python code/analysis/sensitivity.py --input data/processed/extracted_metrics.csv --output data/results/sensitivity_results.json
```

### Step 5: Generate Report

```bash
python code/utils/report_generator.py --input data/results/*.json --output docs/paper_draft.md
```

## Testing

Run the test suite:

```bash
pytest tests/ -v --cov=code --cov-report=xml
```

## Troubleshooting

- **PDF extraction fails**: Ensure `pdfplumber` is installed and the PDFs are not password-protected.
- **Match rate < 60%**: Increase the initial query size or adjust the fuzzy matching threshold in `code/match/fuzzy_matcher.py`.
- **Memory error**: Use `streaming=True` for OpenAlex and process PDFs one at a time.

## Next Steps

- Review the `research.md` for detailed methodology.
- Check `data-model.md` for schema details.
- Explore `contracts/` for validation schemas.