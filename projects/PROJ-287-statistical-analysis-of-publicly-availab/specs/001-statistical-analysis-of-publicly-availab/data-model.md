# Data Model: Statistical Analysis of Topic Drift

## 1. Overview

This document defines the data structures used for ingestion, processing, and analysis. All data is stored in `data/` (raw/processed) and results in `results/`.

## 2. Entity Definitions

### 2.1 Abstract Record
Represents a single academic paper abstract.
*   **id**: `string` (Unique identifier, e.g., `pubmed_12345` or `arxiv_2001.12345`)
*   **source**: `enum` ("arXiv", "PubMed")
*   **publication_year**: `integer` (2000–2024)
*   **field_tag**: `string` (e.g., "cs.LG", "stat.ML", "q-bio")
*   **raw_text**: `string` (Original abstract text)
*   **processed_text**: `string` (Tokenized, lemmatized, stopword-removed)
*   **token_count**: `integer` (Count of tokens in `processed_text`)
*   **window_id**: `string` (e.g., "2000-2004")

### 2.2 Topic Vector
Represents the topic distribution for a specific time window.
*   **window_start**: `integer`
*   **window_end**: `integer`
*   **topic_0** ... **topic_9**: `float` (Probability mass, sum = 1.0)
*   **coherence_score**: `float` (c_v metric)
*   **n_abstracts**: `integer` (Number of abstracts used for this window)
*   **seed**: `integer` (Random seed used for LDA)
*   **aligned_topic_vector**: `array[float]` (Topic proportions reordered to align with the previous window)

### 2.3 Divergence Measurement
Represents the drift between two consecutive windows.
*   **window_pair**: `string` (e.g., "2000-2004_to_2005-2009")
*   **divergence_value**: `float` (JS Divergence, base 2)
*   **p_value_raw**: `float` (From permutation test)
*   **p_value_adjusted**: `float` (MaxT corrected)
*   **ci_lower**: `float` (95% CI lower bound from bootstrapping)
*   **ci_upper**: `float` (95% CI upper bound from bootstrapping)
*   **significance_flag**: `boolean` (True if adjusted p < 0.05)
*   **quality_flag**: `string` ("Valid", "Unreliable")

## 3. File Formats

### 3.1 Raw Data (JSONL)
*   **Location**: `data/raw/pubmed_2000_2024.jsonl`
*   **Schema**: One JSON object per line.
    ```json
    {"id": "pmid_123", "source": "PubMed", "year": 2005, "text": "..."}
    ```

### 3.2 Processed Data (CSV)
*   **Location**: `data/processed/window_2000_2004.csv`
*   **Columns**: `id, source, year, field, processed_text, token_count`
*   **Filter**: Only rows with `token_count >= 20`.

### 3.3 Reproducibility Manifest (JSON)
*   **Location**: `results/manifest.json`
*   **Content**:
    ```json
    {
      "version": "1.0.0",
      "random_seed": 42,
      "parameters": {
        "k_topics": 10,
        "max_iter": 20,
        "permutations": 1000,
        "coherence_threshold": 0.4,
        "min_tokens": 20,
        "window_definitions": ["2000-2004", "2005-2009", ...],
        "sampling_rate": 0.2,
        "correction_method": "MaxT",
        "arxiv_fetch_status": "success"
      },
      "datasets": {
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/",
        "arxiv_url": "http://export.arxiv.org/oai2"
      },
      "checksums": {
        "raw_pubmed": "sha256:...",
        "processed_2000_2004": "sha256:..."
      }
    }
    ```

## 4. Data Flow

1.  **Fetch**: API -> `data/raw/*.jsonl` (Checksummed)
2.  **Preprocess**: `data/raw/*.jsonl` -> Filter (year, tokens) -> `data/processed/*.csv`
3.  **Model**: `data/processed/*.csv` -> LDA -> `results/topic_vectors.json`
4.  **Align**: `results/topic_vectors.json` -> Topic Alignment -> `results/aligned_topic_vectors.json`
5.  **Analyze**: `results/aligned_topic_vectors.json` -> JS Divergence + Permutation (with refit) -> `results/divergence_stats.csv`
6.  **Visualize**: `results/divergence_stats.csv` -> `results/figures/*.png`
