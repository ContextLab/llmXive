# Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

This project implements an automated pipeline to analyze the evolution of music genres over time using publicly available streaming data (Million Playlist Dataset - MPD). The pipeline ingests raw playlist data, enriches it with metadata from MusicBrainz, trains Word2Vec-based genre embeddings, computes temporal similarity metrics, and performs statistical regression to test for significant trends. [UNRESOLVED-CLAIM: c_8de106ed — status=not_enough_info]

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)
- 6GB+ RAM (recommended for full dataset processing)
- 14GB+ disk space (for raw and derived data)

### Setup
1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. (Optional) Install development tools:
 ```bash
 pip install ruff black pytest
 ```

## Usage

The pipeline is organized into modular scripts that can be run sequentially or independently once their dependencies are met.

### 1. Data Ingestion and Preprocessing
Downloads MPD parquet files, fetches MusicBrainz metadata, and joins the datasets.
```bash
python code/ingest.py
```
**Outputs:**
- `data/derived/metadata_mpd.parquet`
- `pipeline_log.txt` (logs ingestion stats, match rates, warnings)

### 2. Embedding Generation
Trains a global Word2Vec model on track sequences and aggregates yearly genre embeddings.
```bash
python code/embeddings.py
```
**Outputs:**
- `yearly_embeddings/{year}.npy` (one file per year)
- `pipeline_log.txt` (updated with training stats)

### 3. Similarity Computation and Visualization
Computes pairwise cosine similarities between yearly genre vectors and generates visual artifacts.
```bash
python code/similarity.py
python code/viz.py
```
**Outputs:**
- `data/derived/yearly_similarity.csv`
- `figures/similarity_trend.png`
- `figures/genre_similarity_heatmap.html`
- `pipeline_log.txt` (updated with visualization status)

### 4. Regression Analysis and Robustness Checks
Fits a linear regression model to test trend significance and calculates Cook's Distance for outlier detection.
```bash
python code/regression.py
```
**Outputs:**
- `data/derived/regression_results.json`
- `data/derived/cooks_distance_report.csv`
- `pipeline_log.txt` (updated with model parameters and outlier counts)

### Running the Full Pipeline
To run the entire pipeline end-to-end:
```bash
python code/ingest.py && \
python code/embeddings.py && \
python code/similarity.py && \
python code/viz.py && \
python code/regression.py
```

## Data Sources

### Primary Data: Million Playlist Dataset (MPD)
- **Source**: [Kaggle - Million Playlist Dataset]
- **Format**: Parquet files containing playlist metadata and track IDs
- **Usage**: Raw input for ingestion pipeline
- **License**: See Kaggle dataset terms

### Metadata Enrichment: MusicBrainz API
- **Source**: [MusicBrainz API](https://musicbrainz.org/doc/Development/XML_Web_Service/Version_2)
- **Purpose**: Fetches track metadata (year, genre, artist) to enrich MPD data
- **Rate Limiting**: Exponential back-off implemented to respect API limits
- **Fallback**: Fuzzy matching fallback logic for tracks not found via exact ID match

### Data Storage
- **Raw Data**: `data/raw/` (downloaded MPD parquet files)
- **Derived Data**: `data/derived/` (processed metadata, similarity results, regression outputs)
- **Embeddings**: `yearly_embeddings/` (NumPy arrays of yearly genre vectors)
- **Figures**: `figures/` (visualization outputs)

## Results Interpretation

### Yearly Genre Embeddings
- **Format**: `{year}.npy` files containing vectors of shape `(num_genres, 100)`
- **Interpretation**: Each row represents a genre's position in a 100-dimensional semantic space derived from playlist co-occurrence patterns.
- **Low-Coverage Years**: Years with <1,000 unique tracks are flagged in logs but included (with zero-fill for missing genres)

### Similarity Metrics
- **Mean Off-Diagonal Similarity**: Average cosine similarity between different genre vectors within a year.
 - **Increasing trend**: Suggests genres are becoming more similar (homogenization)
 - **Decreasing trend**: Suggests genres are becoming more distinct (differentiation)
- **Intra-Genre Variance**: Measures the spread of genre vectors around their centroid.
 - **High variance**: Indicates diverse sub-genres or inconsistent tagging
 - **Low variance**: Indicates cohesive genre definitions

### Regression Results
- **Slope**: Rate of change in mean similarity per year.
 - **Positive slope**: Genres converging over time
 - **Negative slope**: Genres diverging over time
- **95% Confidence Interval**: Range of plausible slope values.
- **P-value**: Statistical significance of the trend (p < 0.05 indicates significant trend).
- **Cook's Distance Report**: Identifies influential outliers that may disproportionately affect regression results.

### Warnings and Edge Cases
- **Missing Genre Rate > 20%**: Logged as a warning; may indicate unreliable genre tagging for that year.
- **Low Coverage Years**: Flagged in logs; excluded from regression analysis but retained in embeddings.
- **API Failures**: Retried with exponential back-off; failures logged to `pipeline_log.txt`.

## Project Structure
```
.
├── code/
│ ├── __init__.py
│ ├── utils.py # Logging, deterministic seeding
│ ├── models.py # Pydantic data models
│ ├── memory_utils.py # Memory monitoring and GC management
│ ├── ingest.py # Data ingestion and enrichment
│ ├── embeddings.py # Word2Vec training and aggregation
│ ├── similarity.py # Similarity computation
│ ├── similarity_save.py # Similarity results persistence
│ ├── viz.py # Visualization generation
│ ├── regression.py # Statistical analysis
│ └── verify_checksums.py # Data integrity verification
├── data/
│ ├── raw/ # Downloaded MPD files
│ └── derived/ # Processed outputs
├── yearly_embeddings/ # Yearly genre embedding files
├── figures/ # Visualization outputs
├── tests/
│ ├── __init__.py
│ ├── contract/ # Schema validation tests
│ └── unit/ # Unit tests for logic
├── requirements.txt
├── README.md
└── pipeline_log.txt # Centralized logging output
```

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Million Playlist Dataset contributors
- MusicBrainz community
- Gensim, Pandas, NumPy, Matplotlib, Plotly, and Statsmodels libraries