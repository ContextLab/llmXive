# Quickstart: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions runner (or local machine with 7GB+ RAM).

## 1. Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd <project-root>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Acquisition

The pipeline expects raw data in `data/raw/`.

```bash
# Create directory
mkdir -p data/raw

# Download MPD (Example command - replace with actual wget/curl if needed)
# Note: In CI, this is handled by the setup script. Locally, you may need to download manually.
# wget "https://huggingface.co/datasets/talkpl-ai/mpd-original/resolve/main/data/train-00000-of-00004.parquet" -O data/raw/mpd.parquet

# Download MusicBrainz
# wget "https://huggingface.co/datasets/imseldrith/musicbrainz-all-songs/resolve/main/data/train-00000-of-00001.parquet" -O data/raw/musicbrainz.parquet
```

*Note: Ensure checksums match the values in `state/projects/PROJ-254-...yaml`.*

## 3. Run the Pipeline

Execute the full pipeline end-to-end:

```bash
python -m src.code.ingest
python -m src.code.embeddings
python -m src.code.similarity
python -m src.code.regression
python -m src.code.viz
```

Or run the master script (if available):

```bash
python -m src.code.run_all
```

## 4. Verify Outputs

Check the `data/derived/` directory for:
-   `global_model.w2v`
-   `embeddings/` folder containing `.npy` files.
-   `yearly_similarity.csv`
-   `sensitivity_report.csv` (Contains Full, Outlier_Removed, Shuffled_Order results)
-   `similarity_trend.png`
-   `genre_similarity_heatmap.html`

## 5. Run Tests

```bash
# Contract tests (schema validation)
pytest tests/contract/

# Unit tests
pytest tests/unit/
```

## 6. Troubleshooting

-   **Memory Error**: Ensure `FR-011` logic (batching) is active. Reduce the sample size in `src/code/utils.py`.
-   **Missing Genres**: Check `pipeline_log.txt` for the "missing genre" warning.
-   **Data Coverage Error**: If the pipeline aborts with "Critical Coverage Error", the MPD dataset volume is insufficient. Verify the download URL and checksums.
-   **API Rate Limits**: The pipeline includes exponential back-off. If it fails, wait and retry.