# Quickstart: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

## 1. Prerequisites

- Python 3.11+
- `git`
- At least 14GB disk space (for data downloads and processing).
- Internet access to fetch datasets from OpenNeuro (via `wget`).

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-228-investigating-the-impact-of-visual-compl

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Download

The pipeline automatically downloads data from the verified OpenNeuro source using `wget` if not present. To manually verify:

```bash
# Run the ingestion script (downloads and processes)
python code/main.py --phase download
```

## 4. Running the Pipeline

Execute the full pipeline (US1 → US2 → US3a → US3b):

```bash
python code/main.py --phase full
```

### Output

- `data/interim/complexity_metrics.csv`
- `data/interim/pfc_timeseries.csv`
- `data/processed/results.json`
- Logs in `logs/`

## 5. Verification

Check the output JSON for expected fields:

```bash
python -c "import json; data = json.load(open('data/processed/results.json')); print(data[0]['entropy']['is_significant'])"
```

## 6. Troubleshooting

- **Memory Error**: Ensure you are running on a machine with ≥6GB RAM. The script will abort if exceeded.
- **Dataset Missing**: If the verified OpenNeuro link is unreachable, check `research.md` for alternative sources or re-run `main.py` with `--retry`.
- **Missing Frames**: Check `logs/ingestion.log` for warnings about excluded frames.