# Quickstart: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

## 1. Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## 2. Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-183-the-impact-of-perspective-taking-on-mora
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
   *Dependencies*: `pandas`, `numpy`, `scipy`, `statsmodels`, `pytest`, `requests`.

## 3. Data Setup

1. **Configure Dataset URL**:
   - Edit `code/config.py` to provide the verified URL for the "Against the Others!" dataset.
   - **CRITICAL**: The pipeline will halt if this URL is missing or invalid.

2. **Run the ingestion script**:
   ```bash
   python -m code.data.ingest
   ```
   - This will filter for high-outrage posts, select 40 stimuli, and save them to `data/processed/stimuli.json`.
   - **Note**: If the dataset lacks required topics or fields, the script will exit with an error.

## 4. Running the Simulation

To validate the pipeline with synthetic data:

```bash
python -m code.analysis.pipeline --mode simulate --n [sample_size] --seed 42
```

- **Output**:
  - `data/processed/simulation_results.csv`: Synthetic participant data.
  - `data/analysis/stats_report.json`: Statistical results (LMM, Mann-Whitney U).

## 5. Running Tests

Ensure the pipeline logic is correct:

```bash
pytest tests/ -v
```

- **Coverage**:
  - `test_ingest.py`: Verifies stimulus filtering and count.
  - `test_simulation.py`: Verifies randomization balance and attention check logic.
  - `test_stats.py`: Verifies statistical calculations against known values.

## 6. Adding Human Data

1. **Collect data**: Use the survey interface (to be built) to collect human responses.
2. **Format**: Save as `data/human_results.csv` with the same schema as `simulation_results.csv` (defined in `contracts/response.schema.yaml`).
3. **Run Analysis**:
   ```bash
   python -m code.analysis.pipeline --mode analyze --input data/human_results.csv
   ```

## 7. Troubleshooting

- **"DataInsufficientError"**: The dataset does not contain enough high-outrage posts for the selected topics. Check the dataset content or adjust the topic filter in `config.py`.
- **"ModuleNotFoundError"**: Ensure the virtual environment is activated and `requirements.txt` was installed.
- **"AssertionError" in tests**: Check if `random_seed` is pinned in `config.py`.
- **"Dataset URL Missing"**: The pipeline cannot proceed without a verified URL in `config.py`.