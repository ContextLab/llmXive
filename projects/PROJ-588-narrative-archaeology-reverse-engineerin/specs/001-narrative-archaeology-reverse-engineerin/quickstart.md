# Quickstart: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

## Prerequisites

- Python 3.11+
- Docker (required for fMRIPrep)
- `datalad` (optional, for data fetching)
- GitHub Actions Runner (for execution)

## Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Data Fetching

Run the data download script to fetch the 5-subject subset of ds000234:

```bash
python src/data/download.py --dataset ds000234 --subjects 5 --output data/raw
```

*Note: This step requires internet access and may take 10-20 minutes.*

## Running the Pipeline

Execute the full analysis pipeline on the 5-subject subset:

```bash
python src/main.py --mode full --subjects 5
```

This will:
1. Preprocess data with fMRIPrep.
2. Segment events and align with HRF.
3. Extract ROIs.
4. Run RSA analysis.
5. Train decoding models.
6. Output results to `results/`.

## Verification

To verify the pipeline on a minimal subset (2 subjects):

```bash
python src/main.py --mode full --subjects 2 --verify
```

Check `logs/` for motion artifact logs and `data/` for checksum files.

## Troubleshooting

- **OOM Error**: Reduce `--workers` in `main.py` to 1.
- **fMRIPrep Fail**: Check `logs/fmriprep/` for specific error codes.
- **Missing Labels**: Ensure `events.tsv` matches the BOLD timecourse length.
