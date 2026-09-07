# Quickstart Guide: The Impact of Perceived Control Over Digital Environments on Anxiety

## Project Overview

This research project investigates the correlation between perceived control over digital environments and anxiety levels, using social media data as a proxy for both variables.

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- At least 7GB available RAM
- 6 hours of continuous runtime capacity (for full dataset processing)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd llmXive-proj-281
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
python -c "import code; print('Installation successful')"
```

## Quick Start

### Run the Full Pipeline

Execute the entire research pipeline from data ingestion to final visualization:

```bash
python code/main.py
```

This will:
1. Download the social media dataset (CardiffNLP tweet sentiment extraction)
2. Preprocess and filter text data
3. Calculate anxiety scores using NLP models
4. Extract control proxies from metadata
5. Perform statistical correlation analysis
6. Generate visualization

**Expected Runtime**: ~4-6 hours on standard hardware
**Memory Usage**: ~3-5 GB peak

### Run Individual Stages

For debugging or incremental processing:

```bash
# Stage 1: Data Ingestion
python code/services/data_ingestion.py

# Stage 2: Preprocessing & Scoring
python code/services/anxiety_scoring.py

# Stage 3: Proxy Extraction
python code/services/proxy_extractor.py

# Stage 4: Statistical Analysis
python code/analysis/statistical_test.py

# Stage 5: Visualization
python code/viz/plot_results.py
```

### Performance Profiling

To verify runtime and memory constraints:

```bash
# Full profiling run
python code/profiling.py

# Check only Plan/Spec discrepancy
python code/profiling.py --check-only

# Custom output path
python code/profiling.py --output data/processed/custom_report.json
```

The profiling script will:
- Measure actual runtime and memory usage
- Validate against SC-004 limits (6h runtime, 7GB RAM)
- Check for discrepancies between Plan.md and Spec SC-004
- Generate a detailed JSON report at `data/processed/profiling_report.json`

## Output Files

After successful execution, you'll find:

- `data/raw/social_media.csv` - Raw dataset download
- `data/processed/preprocessed_text.csv` - Filtered text data
- `data/processed/scoring_results.csv` - Anxiety scores
- `data/processed/proxy_results.csv` - Control proxies
- `data/processed/final_analysis.csv` - Merged analysis dataset
- `data/processed/analysis_results.json` - Statistical test results
- `data/processed/correlation_plot.png` - Visualization
- `data/processed/profiling_report.json` - Performance metrics

## Validation & Testing

Run the test suite:

```bash
pytest tests/ -v --cov=code
```

Key integration tests:
- `tests/integration/test_profiling.py` - Performance validation
- `tests/integration/test_synthetic_correlation.py` - Statistical analysis
- `tests/integration/test_reproducibility.py` - Result reproducibility

## Troubleshooting

### Runtime Limit Exceeded
If the pipeline exceeds 6 hours:
- Check system resources
- Consider processing in smaller chunks
- Review `config.RUNTIME_LIMIT_HOURS` if you need to adjust (not recommended)

### Memory Issues
If you encounter memory errors:
- Ensure you have at least 7GB available RAM
- The pipeline uses streaming for large datasets (T042)
- Close other applications to free memory

### Data Fetch Failures
The pipeline will fail loudly if the real dataset cannot be fetched (T043):
- Check internet connection
- Verify HuggingFace access
- No synthetic fallback is provided to prevent data fabrication

## Next Steps

1. Review the research findings in `data/processed/analysis_results.json`
2. Examine the correlation plot in `data/processed/correlation_plot.png`
3. Read the full methodology in `specs/001-the-impact-of-perceived-control-over-dig/spec.md`
4. Contribute to ongoing research by forking and extending the pipeline

## Support

For issues or questions:
- Check the `specs/` directory for detailed documentation
- Review the `contracts/` directory for data schemas
- Examine the `tests/` directory for usage examples