# Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

This project implements a reproducible pipeline to analyze the evolution of music genres over time using the Million Playlist Dataset (MPD). It ingests playlist data, matches tracks to MusicBrainz metadata, trains a global Word2Vec model to derive yearly genre embeddings, computes temporal similarity trends, and performs statistical regression analysis.

## Installation

Ensure you have Python 3.11+ installed. Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

**Dependencies**:
- `pandas`, `numpy`, `scikit-learn`, `statsmodels` (data processing & modeling)
- `gensim` (Word2Vec training)
- `matplotlib`, `plotly` (visualization)
- `requests`, `pyarrow` (data fetching & storage)
- `pydantic` (data validation)
- `psutil` (memory monitoring)
- `ruff`, `black` (linting & formatting)

## Usage

The pipeline is designed to run sequentially through three main user stories. You can run the full pipeline or specific stages.

### Full Pipeline Execution

```bash
python -m src.code.run_quickstart_validation
```

This script orchestrates the entire workflow:
1. **Ingestion**: Downloads MPD parquet files, fetches MusicBrainz metadata, and joins data.
2. **Embeddings**: Trains a global Word2Vec model and aggregates yearly genre embeddings.
3. **Similarity**: Computes pairwise cosine similarities between yearly genre vectors.
4. **Regression**: Fits a linear regression model to test trend significance and performs robustness checks.

### Running Individual Stages

If you wish to run specific stages (e.g., for debugging or incremental development):

```bash
# Stage 1: Ingest and preprocess data
python -c "from ingest import main; main()"

# Stage 2: Train embeddings and aggregate yearly vectors
python -c "from embeddings import main; main()"

# Stage 3: Compute similarity and generate plots
python -c "from similarity import main; main()"

# Stage 4: Run regression analysis
python -c "from regression import main; main()"
```

## Data Sources

This project relies on **real, publicly available data**. No synthetic or fake data is used.

- **Million Playlist Dataset (MPD)**:
 - Source: `https://mlp-datasets.s3.amazonaws.com/mpd_subset_100k.parquet`
 - Description: A subset of the Spotify Million Playlist Dataset containing 100,000 playlists. [UNRESOLVED-CLAIM: c_b5386082 — status=not_enough_info]
 - Usage: Used to extract track IDs, release years, and playlist sequences for Word2Vec training.
 - Note: The Last.fm dataset mentioned in earlier design docs is **WAIVED** per the project plan; only MPD data is used.

- **MusicBrainz API**:
 - Source: `
 - Usage: Fetched at runtime to retrieve genre metadata for tracks matched by ISRC or title.
 - Fallback: Fuzzy matching is implemented if exact matches fail.

**Data Storage**:
- Raw data is stored in `data/raw/`.
- Processed/derived data (e.g., metadata joins, embeddings, similarity matrices) is stored in `data/derived/`.

## Results Interpretation

The pipeline generates several key artifacts that can be found in the `data/derived/` and `figures/` directories.

### 1. Yearly Genre Embeddings (`data/derived/yearly_embeddings/`)
- **Format**: NumPy `.npy` files (one per year).
- **Content**: Vector representations of genres for each year, derived by averaging track vectors (from Word2Vec) grouped by genre and year.
- **Interpretation**: These vectors capture the semantic "position" of a genre in a high-dimensional space for a given year. Changes in these vectors over time indicate genre evolution.
- **Low Coverage**: Years with fewer than 1,000 unique tracks are flagged in `data/derived/low_coverage_years.json` and excluded from regression analysis [UNRESOLVED-CLAIM: c_299f810e — status=not_enough_info] to ensure statistical robustness.

### 2. Similarity Trends (`data/derived/yearly_similarity.csv`, `figures/similarity_trend.png`)
- **Content**: A time series of mean off-diagonal similarity between genre vectors.
- **Interpretation**:
 - **Increasing Similarity**: Suggests genres are becoming more homogeneous or converging (e.g., pop influencing rock, rock influencing hip-hop).
 - **Decreasing Similarity**: Suggests genres are diverging or fragmenting into more distinct sub-genres.
 - **95% CI Bands**: Visualized in `similarity_trend.png` to indicate statistical confidence in the trend.

### 3. Regression Results (`data/derived/regression_results.json`, `data/derived/cooks_distance_report.csv`)
- **Content**: Statistical test of the similarity trend (slope, p-value, confidence interval).
- **Interpretation**:
 - **Slope**: The rate of change in genre similarity per year.
 - **P-value**: Indicates whether the observed trend is statistically significant (typically p < 0.05).
 - **Cook's Distance**: Identifies outlier years that disproportionately influence the regression model. High values suggest those years may represent anomalous shifts in music culture.

### 4. Sensitivity Report (`data/derived/sensitivity_report.csv`)
- **Content**: Regression slopes and p-values computed under different filtering thresholds (years with small year-over-year similarity changes are excluded).
- **Interpretation**: Demonstrates the robustness of the primary finding. If the trend remains significant across thresholds, the conclusion is more reliable.

## Project Structure

```
.
├── code/
│ ├── __init__.py
│ ├── utils.py # Logging, deterministic seeding
│ ├── models.py # Pydantic data schemas
│ ├── memory_utils.py # Memory monitoring & GC management
│ ├── ingest.py # Data ingestion & matching
│ ├── embeddings.py # Word2Vec training & aggregation
│ ├── similarity.py # Cosine similarity calculation
│ ├── viz.py # Plotting utilities
│ ├── regression.py # Statistical modeling & robustness checks
│ └── run_quickstart_validation.py # End-to-end orchestration
├── data/
│ ├── raw/ # Downloaded MPD parquet files
│ └── derived/ # Processed data, embeddings, results
├── figures/ # Generated plots (PNG, HTML)
├── tests/ # Unit and contract tests
├── requirements.txt
└── README.md
```

## Reproducibility

- **Deterministic Seeding**: All random number generators (NumPy, Python `random`) are seeded at the start of execution to ensure reproducible results.
- **Memory Management**: The pipeline monitors RAM usage and triggers garbage collection to stay within a 6GB limit [UNRESOLVED-CLAIM: c_d0376a88 — status=not_enough_info], preventing OOM errors on large datasets.
- **Checksum Verification**: `data/raw/` files are verified against checksums to ensure data integrity.

## License

This project is for research purposes. Please refer to the original data sources (Spotify/MPD, MusicBrainz) for their respective usage licenses.