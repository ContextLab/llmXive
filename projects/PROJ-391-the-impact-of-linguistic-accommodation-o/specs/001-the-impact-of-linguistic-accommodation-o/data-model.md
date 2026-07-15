# Data Model: Linguistic Accommodation & Human‑Rated Empathy

## 1. Entities & Relationships

### DialoguePair
Represents a single interaction unit from DailyDialog.
- **Attributes**:
  - `conversation_id` (str): Unique identifier for the dialogue session.
  - `turn_index` (int): Index of the turn within the conversation.
  - `user_turn` (str): Normalized text of the user input.
  - `ai_response` (str): Normalized text of the proxy AI response (second speaker in DailyDialog).
  - `emotion_label` (str): Raw emotion label from DailyDialog.
  - `word_count` (int): Total words in the pair.

### AccommodationMetric
Derived metrics for a `DialoguePair`.
- **Attributes**:
  - `lexical_overlap` (float): Jaccard similarity of token sets (0 – 1).
  - `syntactic_similarity` (float): Jaccard similarity of POS tag sets (0 – 1).
  - `dependency_similarity` (float): Jaccard similarity of dependency relation labels (0 – 1).
  - `sentence_length_variance` (float): Variance of sentence lengths in the AI response.

### HumanValidationRecord (FR‑010)
Represents a human‑rated AI‑assistant response.
- **Attributes**:
  - `validation_id` (str): Unique identifier.
  - `user_prompt` (str): Human prompt presented to the AI.
  - `ai_response` (str): Generated AI response.
  - `human_empathy_rating` (int): 1‑5 Likert rating of perceived empathy.
  - `consent_id` (str): Reference to consent record (IRB‑approved).

### FinalDataset (merged)
Combines metrics from `DialoguePair` with the human‑rated empathy scores where available.
- **Attributes** (superset of columns in `final_dataset.csv`):
  - All fields from `DialoguePair` and `AccommodationMetric`.
  - `emotion_mapped_score` (int): Proxy score derived from `emotion_label` (Joy → 5, …, Neutral → 3) – **used only for exploratory checks**.
  - `human_empathy_rating` (int, optional): Rating from the collected validation set; present for rows that belong to the validation subset.
  - `lda_topic_id` (int): Dominant LDA cluster (0‑9).
  - `is_validation_subset` (bool): `True` for the 30 manually rated records.

## 2. Data Flow

1. **Raw Input**: `daily_dialog.parquet` (DailyDialog) and `human_empathy.csv` (collected).  
2. **Ingestion**: `01_ingest_and_preprocess.py` → `data/raw/daily_dialog_raw.csv`.  
3. **Human Collection**: `00_collect_human_empathy.py` → `data/raw/human_empathy/raw_responses.csv`.  
4. **Metric Computation**: `03_compute_metrics.py` → adds accommodation columns.  
5. **Topic Modeling**: `06_generate_topics.py` → adds `lda_topic_id`.  
6. **Merging**: `07_analyze_correlations.py` merges DailyDialog‑derived rows with human‑rated rows on compatible fields, producing `data/processed/final_dataset.csv`.  
7. **Analysis & Validation**: Subsequent scripts read `final_dataset.csv`.

## 3. Schema Adjustments

- Added optional `human_empathy_rating` (int 1‑5) to the final dataset schema.  
- Added `is_validation_subset` (bool) to flag the manually annotated records.  
- Updated `HumanValidationRecord` entity to satisfy FR‑010.

## 4. Constraints & Rules

- **Unicode**: All text fields must be normalized to NFKC.  
- **Null Handling**: Records with empty `user_turn` or `ai_response` after normalization are dropped.  
- **Range**: All similarity scores ∈ [0.0, 1.0]; `human_empathy_rating` ∈ [1, 5].  
- **Consent**: Every row in `human_empathy.csv` must include a non‑empty `consent_id` linking to the IRB consent log.  
