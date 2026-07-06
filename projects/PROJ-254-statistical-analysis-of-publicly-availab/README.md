# Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

This project implements an automated pipeline to analyze the evolution of music genres over time using the Million Playlist Dataset (MPD). It ingests playlist data, enriches it with metadata from MusicBrainz, trains Word2Vec embeddings to derive genre vectors, and performs statistical analysis on temporal similarity trends.

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)
- At least 8GB RAM (recommended 16GB for full dataset processing)

### Setup
1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-254-statistical-analysis-of-publicly-availab
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

4. (Optional) Install development tools for linting and formatting:
 ```bash
 pip install ruff black
 ```

## Usage

The pipeline is executed in stages corresponding to the user stories. Ensure you have sufficient disk space and memory before running.

### 1. Data Ingestion and Preprocessing (User Story 1)
Downloads MPD data, fetches MusicBrainz metadata, and trains the global Word2Vec model.
```bash
python code/ingest.py
python code/embeddings.py
```
*Outputs*: `data/derived/metadata_mpd.parquet`, `yearly_embeddings/*.npy`

### 2. Similarity Computation and Visualization (User Story 2)
Computes pairwise cosine similarities between yearly genre vectors and generates plots.
```bash
python code/similarity.py
python code/similarity_save.py
python code/viz.py
```
*Outputs*: `data/derived/yearly_similarity.csv`, `figures/similarity_trend.png`, `figures/genre_similarity_heatmap.html`

### 3. Statistical Regression and Robustness Checks (User Story 3)
Fits a linear regression to test trend significance and calculates Cook's Distance for outliers.
```bash
python code/regression.py
```
*Outputs*: `data/derived/regression_results.json`, `data/derived/cooks_distance_report.csv`

### Full Pipeline
To run the entire pipeline sequentially:
```bash
python code/ingest.py && python code/embeddings.py && python code/similarity.py && python code/similarity_save.py && python code/viz.py && python code/regression.py
```

## Data Sources

- **Million Playlist Dataset (MPD)**: The primary source of streaming data.
 - URL:
 - Format: Parquet files containing playlist tracks and metadata.
 - Note: This project uses the MPD directly; Last.fm data is waived per project plan.

- **MusicBrainz API**: Used to enrich track metadata (year, genre tags).
 - URL: https://musicbrainz.org/doc/XML_Web_Service
 - Rate limits are handled via exponential back-off in `code/ingest.py`.

## Results Interpretation

- **Yearly Genre Embeddings (`yearly_embeddings/*.npy`)**:
 - Numpy arrays representing the centroid vector of each genre for a specific year.
 - Dimensions: `[num_genres, 100]` (100-dimensional Word2Vec space).
 - Low-coverage years (fewer than 1,000 unique tracks) are flagged in logs but included with zero-filled genres where applicable.

- **Similarity Metrics (`data/derived/yearly_similarity.csv`)**:
 - `mean_off_diagonal_similarity`: Average cosine similarity between distinct genre vectors.
 - Higher values indicate genre convergence (less distinction between genres).
 - Lower values indicate genre divergence (more distinct genres).
 - `intra_genre_variance`: Variance within genre clusters over time.

- **Regression Results (`data/derived/regression_results.json`)**:
 - `slope`: Rate of change in genre similarity over time.
 - Positive slope: Genres are becoming more similar (homogenization).
 - Negative slope: Genres are becoming more distinct (fragmentation).
 - `p_value`: Statistical significance of the trend.
 - `ci_lower`, `ci_upper`: 95% Confidence Interval for the slope.

- **Outlier Analysis (`data/derived/cooks_distance_report.csv`)**:
 - Identifies years that disproportionately influence the regression model.
 - High Cook's Distance values (> 1 or > 4/n) suggest potential anomalies or structural breaks in genre evolution.

## Project Structure

```
.
├── code/ # Source code modules
│ ├── ingest.py # Data ingestion and enrichment
│ ├── embeddings.py # Word2Vec training and aggregation
│ ├── similarity.py # Cosine similarity calculation
│ ├── viz.py # Visualization generation
│ ├── regression.py # Statistical modeling
│ ├── models.py # Pydantic data schemas
│ ├── utils.py # Logging and seeding utilities
│ └──...
├── data/
│ ├── raw/ # Downloaded raw data (MPD)
│ └── derived/ # Processed data and intermediate results
├── figures/ # Generated plots and visualizations
├── tests/ # Unit and contract tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## License

This project is for research purposes. Please adhere to the usage policies of the Million Playlist Dataset and MusicBrainz.