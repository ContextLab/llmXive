# Quickstart: Counterfactual Inspector Agent

## Prerequisites

- Python 3.11+
- `git`
- Access to a Hugging Face account (for dataset access, if required)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-follow-up
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` includes `scikit-learn`, `pandas`, `scipy`, `datasets`, `openai`, `pyyaml`.*

## Running the Pipeline

### 1. Download Data (Optional)
If you want to pre-download the dataset:
```bash
python code/data_loader.py --dataset uci_har --mode download
```
This creates `data/raw/uci_har_test.csv`.

### 2. Run the Full Pipeline
Execute the main script with a specific dataset:
```bash
python code/main.py --dataset uci_har --seed 42
```
- **Output**: Results are saved in `output/`.
- **Logs**: Detailed logs are in `logs/pipeline_run.log`.

### 3. Inspect Results
- **Baseline Story**: `output/baseline_stories/uci_har_baseline.json`
- **Counterfactual Report**: `output/counterfactual_reports/uci_har_counterfactual.json`
- **Integrated Story**: `output/integrated_stories/uci_har_integrated.json`
- **Metrics**: `output/metrics_report.json`

## Testing

Run the unit tests to verify statistical logic and query generation:
```bash
pytest tests/unit/ -v
```

Run integration tests for the full pipeline:
```bash
pytest tests/integration/ -v
```

## API Usage (Programmatic)

You can import the pipeline components directly:

```python
from code.stats_engine import StatsEngine
from code.query_generator import QueryRetrier

# Initialize
stats = StatsEngine()
trier = QueryRetrier(max_attempts=2)

# Load data
df = stats.load_data("data/raw/uci_har_test.csv")

# Baseline
baseline = stats.find_primary_correlation(df)

# Counterfactual
counterfactuals = trier.generate_and_test(df, baseline)
```

## Troubleshooting

- **Low Power Error**: If the dataset has < 30 rows, the system will flag `low_power_flag: true` in the output but continue running.
- **Query Timeout**: If the LLM query generation times out, the `QueryRetrier` will retry up to 2 times. If it fails, the counterfactual section will be marked "Failed".
- **Memory Error**: If the dataset is too large, enable streaming in `config.py` (`STREAMING_MODE = True`).
