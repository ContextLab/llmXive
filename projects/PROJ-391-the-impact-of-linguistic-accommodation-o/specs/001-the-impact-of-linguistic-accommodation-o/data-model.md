# Data Model: The Impact of Linguistic Accommodation on Perceived Empathy in AI Assistants

## Entities

### 1. DialoguePair
Represents a single interaction unit.
- `conversation_id`: string (UUID or dataset ID)
- `turn_index`: integer (0-based)
- `user_turn`: string (normalized text)
- `ai_response`: string (normalized text, proxy for AI)
- `topic`: string (e.g., "daily_life", "shopping" - from dataset)
- `emotion_label`: string (e.g., "joy", "sadness")

### 2. AccommodationMetric
Computed features for a `DialoguePair`.
- `pair_id`: string (FK to DialoguePair)
- `lexical_overlap`: float (Jaccard similarity, 0.0-1.0)
- `syntactic_similarity_pos`: float (POS Jaccard similarity, 0.0-1.0)
- `syntactic_similarity_dep`: float (Dependency Jaccard similarity, 0.0-1.0, for sensitivity)
- `sentence_length_variance`: float
- `user_turn_length`: integer (word count)
- `ai_response_length`: integer (word count)
- `is_repetition`: boolean (True if lexical_overlap > 0.9)

### 3. EmpathyRating
Derived or explicit rating.
- `pair_id`: string (FK to DialoguePair)
- `proxy_empathy_score`: integer (1-5 Likert)
- `source`: string ("explicit" or "inferred")
- `inferred_from_emotion`: string (e.g., "joy")

### 4. AnalysisResult
Aggregated statistical outputs.
- `metric_type`: string ("lexical" or "syntactic")
- `correlation_method`: string ("pearson" or "spearman")
- `correlation_coefficient`: float
- `p_value`: float
- `ci_lower`: float
- `ci_upper`: float
- `bootstrap_iterations`: integer
- `effect_size_category`: string ("negligible", "small", "medium", "large")
- `bonferroni_corrected_alpha`: float
- `is_significant`: boolean

## Data Flow

1.  **Input**: `data/raw/dailydialog_test.json` (Raw)
2.  **Step 1**: `code/data_ingestion.py` -> `data/processed/dialogues_cleaned.csv` (DialoguePair)
3.  **Step 2**: `code/data_ingestion.py` -> `data/processed/accommodation_metrics.csv` (AccommodationMetric)
4.  **Step 3**: `code/empathy_mapping.py` -> `data/processed/empathy_ratings.csv` (EmpathyRating)
5.  **Step 4**: `code/sensitivity_analysis.py` -> `data/processed/sensitivity_results.csv` (Comparison of POS vs Dep)
6.  **Step 5**: `code/statistical_analysis.py` -> `data/processed/analysis_results.csv` (AnalysisResult)
7.  **Output**: `outputs/reports/statistical_summary.md`, `outputs/figures/scatter_plot.png`

## Storage Constraints
- **Raw Data**: ~10 MB (compressed).
- **Processed Data**: ~5 MB (CSVs with floats).
- **Total Disk**: < 20 MB (well within 14 GB limit).
- **RAM**: < 1 GB for loading full dataset.
