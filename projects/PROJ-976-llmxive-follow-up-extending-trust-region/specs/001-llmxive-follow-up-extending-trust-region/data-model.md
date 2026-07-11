# Data Model: llmXive follow-up: extending "Trust-Region Behavior Blending for On-Policy Distillation"

## Entity Definitions

### DiversityProfile
Represents the static feature vector for a single teacher response.
- **distinct_4_ratio**: float (0.0 - 1.0). Ratio of distinct 4-grams to total 4-grams.
- **ngram_entropy**: float. Average entropy of n-grams (n=1 to 4).
- **syntactic_variation_score**: float. Variance of parse tree depths.
- **text_length**: int. Number of tokens/characters.
- **parse_failed**: boolean. True if parsing failed (metric set to NaN).

### TrainingInstance
Links a `DiversityProfile` to a proxy target (since ground truth is missing).
- **profile_id**: string. Unique ID linking to the source output.
- **domain**: string. "book_corpus" (source) or "beir" (target).
- **proxy_quality_score**: float. Relevance score (BEIR) or text length (Book Corpus) used as a proxy for quality.
- **proxy_stability_score**: float. Simulated stability metric (e.g., inverse of text length variance) used as a proxy for stability.
- **optimal_epsilon_0**: null. (Ground truth missing, set to null).
- **collapse_label**: null. (Ground truth missing, set to null).
- **final_loss_variance**: null. (Ground truth missing, set to null).

### AnalysisResult
The output of the correlation analysis.
- **model_type**: string. "Correlation" or "Baseline".
- **task**: string. "correlation_analysis".
- **source_domain**: string. "book_corpus".
- **target_domain**: string. "beir".
- **metrics**: dict. Correlation coefficients, baseline delta, p-values.

## Data Flow

1.  **Input**: Raw JSONL/Parquet files from verified datasets.
2.  **Processing**:
    -   Filter empty/whitespace rows.
    -   Compute `distinct_4_ratio`, `ngram_entropy`, `syntactic_variation_score`.
    -   Handle parse failures (assign NaN).
    -   Join with available metadata (relevance scores, text length) to create proxy targets.
3.  **Output**:
    -   `data/processed/feature_matrix_source.csv`
    -   `data/processed/feature_matrix_target.csv`
    -   `data/results/correlation_report.json`

## Edge Cases & Defaults

-   **Empty Text**: `distinct_4_ratio` = 0.0, `ngram_entropy` = 0.0, `syntactic_variation_score` = NaN.
-   **Parse Failure**: `syntactic_variation_score` = NaN. Row is excluded from analysis if > 20% of data fails.
-   **Missing Proxy Metadata**: Row is excluded from the analysis set but logged for coverage reporting.