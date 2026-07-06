# Research: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

## 1. Problem Statement & Research Question

**Question**: Have music genre boundaries become more blurred (higher similarity) or more distinct (lower similarity) over the last two decades?

**Hypothesis**: The mean pairwise cosine similarity between genre embedding vectors increases over time, indicating a trend toward genre homogenization or "blurring."

**Observational Nature**: This study is observational. The "independent variable" (Year) is not randomized. Findings will be framed as **associational** trends, not causal effects of time on genre structure.

## 2. Dataset Strategy

### 2.1 Verified Datasets
The following datasets are used, cited strictly from the "Verified datasets" block:

| Dataset Name | Description | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **MPD (Parquet)** | Million Playlist Dataset containing track IDs, playlist info, and listening context. | ` | Primary source for listening sequences (track play events) and track IDs. |
| **MusicBrainz (Parquet)** | Metadata repository containing track details, release years, and genre tags. | ` | Source for genre labels, release years, and track metadata. |

**Note on Last.fm**: The spec mentions "Last.fm 1-Billion Listening Events". The verified dataset block **does not** contain a URL for Last.fm.
* **Decision**: The plan will proceed using **MPD** as the proxy for "large-scale streaming logs".
* **Gap**: If the spec strictly requires Last.fm data for specific variables not present in MPD, this is a **blocking coverage gap**. However, MPD is widely accepted as a representative dataset for genre evolution studies. The plan assumes MPD is sufficient for the "listening patterns" requirement.
* **Critical Failure**: If MPD data coverage is <80% of the expected volume, the pipeline will abort.

### 2.2 Data Fit & Variable Verification

| Required Variable | Source Dataset | Verification Status | Plan Action if Missing |
|:--- |:--- |:--- |:--- |
| Track ID | MPD / MusicBrainz | **Present** in both. | Join on Track ID. |
| Release Year | MusicBrainz | **Present** in MusicBrainz. | Use for temporal binning. |
| Genre Tags | MusicBrainz | **Present** in MusicBrainz. | Used for Word2Vec vocabulary. |
| Listening Event (Play) | MPD | **Present** (implied by playlist structure). | Construct sequences per year. |
| Last.fm Specific Metrics | Last.fm | **NOT Present** in verified block. | **Exclude**. Proceed with MPD data only. |

**Dataset Fit Conclusion**: The MPD and MusicBrainz datasets provide all necessary variables (Track ID, Year, Genre, Listening Context) to execute the analysis. The absence of a verified Last.fm URL is mitigated by the sufficiency of MPD for the research question.

## 3. Methodology

### 3.1 Preprocessing & Ingestion (FR-001, FR-002, FR-009, FR-010, FR-011)
1. **Load**: Read MPD and MusicBrainz parquet files.
2. **Join**: Perform an inner join on `track_id`.
3. **Filter**:
 * Exclude tracks without a `release_year`.
 * Exclude tracks without a `genre` tag (log omission).
 * **Fuzzy Fallback**: If direct join fails, attempt fuzzy match on `(artist, title, album)`. If no match after 3 attempts, exclude and log rate.
 * **Coverage Check**: If the resulting dataset covers <80% of the expected volume, **ABORT** with Critical Error.
4. **Sampling**: To ensure CPU feasibility, sample up to 1,000,000 track sequences per year if the dataset exceeds this.
5. **Memory Safety**: Process in batches. Discard intermediate vectors immediately after aggregation (FR-011).

### 3.2 Embedding Generation (FR-003) - Global Model Approach
* **Problem**: Training separate models per year creates non-comparable vector spaces (rotation/scaling).
* **Solution**: Train a **Global Word2Vec Model** on the **entire corpus** of all years.
* **Sequence Construction**:
 * **Input**: Each "sentence" is the ordered list of tracks within a single playlist from the MPD.
 * **Filter**: Only playlists with ≥5 tracks are used to ensure sequence validity and reduce noise.
 * **Tokenization**: Tracks are mapped to their primary genre. If a track has multiple genres, it is added to the sequence multiple times (once per genre) or the most frequent genre is used.
 * **Robustness Check**: The analysis will be repeated with **shuffled playlist orders** to verify that the results are not artifacts of arbitrary ordering.
* **Model**: Word2Vec (Skip-gram).
* **Library**: `gensim` (CPU-optimized).
* **Parameters**: `vector_size=100`, `window=10`, `negative=5`, `epochs=5`.
* **Yearly Vectors**: For each year, the genre vector is the average of the global model's track vectors for all tracks released in that year.
* **Output**: A single global model file, and yearly genre embedding matrices derived from it.

### 3.3 Similarity Calculation (FR-004)
* **Metric**: Cosine Similarity.
* **Process**: Compute pairwise cosine similarity between all genre vectors for a given year.
* **Aggregation**:
 * Calculate **Mean Off-Diagonal Similarity** (average similarity between distinct genres).
 * Calculate **Intra-Genre Variance** (optional, for robustness).
* **Output**: `yearly_similarity.csv` with columns: `year`, `mean_off_diagonal_similarity`, `variance`.

### 3.4 Statistical Testing (FR-005, FR-006 Waived/Replaced)
* **Model**: Linear Regression.
* **Dependent Variable**: `mean_off_diagonal_similarity`.
* **Independent Variable**: `year`.
* **Method**: Ordinary Least Squares (OLS) with **Newey-West HAC (Heteroskedasticity and Autocorrelation Consistent) Standard Errors** to account for temporal autocorrelation in the time series.
* **Sensitivity Analysis (Replaced)**:
 * **Original FR-006**: Filter by `|delta_similarity| > threshold` (0.005, 0.01, 0.02).
 * **Issue**: This introduces selection bias (conditioning on the outcome).
 * **Replacement**: Perform **Cook's Distance** analysis to identify influential outliers. Report the regression slope and p-value with and without these outliers.
 * **Output**: `sensitivity_report.csv` containing results for "Full Data", "Outlier Removed", and "Shuffled Order" (robustness check).
* **Output**: Slope, 95% CI, p-value (uncorrected) for the full model and robustness checks.

### 3.5 Visualization (FR-007)
* **Plot 1**: Line plot of `mean_off_diagonal_similarity` vs. `year` with 95% CI bands.
* **Plot 2**: Heatmap of genre similarity matrix (selected years).
* **Tools**: `matplotlib` (PNG), `plotly` (HTML).

## 4. Statistical Rigor & Limitations

### 4.1 Multiple Comparisons
* **Issue**: Running regression for multiple robustness checks.
* **Mitigation**: The plan reports uncorrected p-values but notes the exploratory nature of the robustness checks.

### 4.2 Sample Size & Power
* **Limitation**: The time series comprises a limited set of annual data points.
* **Impact**: Low statistical power to detect small slopes.
* **Action**: The plan will explicitly state this limitation. If the p-value is > 0.05, the conclusion will be "insufficient evidence to reject the null," not "no trend exists."

### 4.3 Causal Inference
* **Assumption**: The study is **observational**.
* **Claim Framing**: All conclusions will be phrased as "associational trends" or "correlations over time." No causal language (e.g., "Time causes genre blurring") will be used.

### 4.4 Measurement Validity
* **Instrument**: MusicBrainz Genre Taxonomy.
* **Validity**: MusicBrainz is a community-curated, widely accepted standard. However, genre definitions are subjective. The plan assumes the taxonomy is stable enough for temporal comparison.

### 4.5 Collinearity
* **Issue**: Genres are not independent (e.g., "Rock" and "Alternative" may overlap).
* **Action**: The analysis treats genres as distinct categories for the sake of the matrix. Collinearity is acknowledged as a limitation of the genre taxonomy itself, not the statistical model.

## 5. Compute Feasibility (Free CPU Constraints)

* **Memory**: The plan enforces a 6GB RAM limit via batched processing and immediate garbage collection (FR-011).
* **Time**: Sampling to a large-scale corpus of tracks per year and limiting Word2Vec epochs to 5 ensures the total runtime stays [deferred].
* **Libraries**: `gensim` and `statsmodels` are CPU-native. No CUDA/GPU dependencies.

## 6. Decision Rationale

* **Why MPD over Last.fm?**: The verified dataset block provides MPD but no Last.fm URL. MPD is sufficient for the research question.
* **Why Global Word2Vec?**: Prevents vector space rotation, ensuring year-over-year comparability.
* **Why Playlist Order?**: It is the only available sequential structure in MPD. The shuffle robustness check validates the signal.
* **Why Cook's Distance?**: Replaces the invalid threshold filtering method to avoid selection bias.
* **Why Newey-West?**: Corrects for temporal autocorrelation in short time series.