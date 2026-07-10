# Quickstart Guide: The Impact of Perceived Control Over Digital Environments on Anxiety

## Overview
This project analyzes the correlation between perceived control over digital environments and anxiety levels, using social media data.

## Prerequisites
- Python 3.10+
- pip
- ~7GB RAM available
- ~6 hours maximum runtime

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd llmXive-the-impact-of-perceived-control-over-dig
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Pipeline

### Full Pipeline with Performance Profiling
To run the entire analysis pipeline with performance monitoring (runtime and memory):

```bash
python code/profiling.py
```

This will:
1. Download and preprocess the dataset
2. Score anxiety levels
3. Extract control proxies
4. Perform statistical analysis
5. Generate visualizations
6. Validate runtime < 6h and RAM < 7GB

Output will be saved to `data/processed/`.

### Individual Stages
You can also run individual stages by importing and calling the specific functions in `code/main.py`:

```python
from code.main import run_pipeline
run_pipeline()
```

## Output Files
- `data/processed/scoring_results.csv`: Anxiety scores
- `data/processed/proxy_results.csv`: Control proxies
- `data/processed/analysis_results.json`: Statistical test results
- `data/processed/correlation_plot.png`: Visualization
- `data/processed/performance_report.json`: Performance metrics

## Performance Constraints
- **Runtime**: Must complete within 6 hours (SC-004)
- **Memory**: Must not exceed 7GB RAM
- **Coverage**: Anxiety scoring coverage ≥95%
- **Confidence**: Minimum confidence score ≥0.6

## Testing
Run the test suite:
```bash
pytest tests/ -v --cov=code
```

Run specific profiling tests:
```bash
pytest tests/unit/test_profiling.py -v
pytest tests/integration/test_profiling_integration.py -v
```

## Troubleshooting
- **Memory Error**: Ensure no other heavy applications are running.
- **Dataset Download Failed**: Check internet connection and HuggingFace access.
- **Model Loading Error**: Verify `transformers` and `torch` are installed correctly.