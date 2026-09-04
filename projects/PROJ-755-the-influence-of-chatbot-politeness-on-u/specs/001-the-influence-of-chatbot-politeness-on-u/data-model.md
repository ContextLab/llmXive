# Data Model: The Influence of Chatbot Politeness on User-Perceived Quality

## 1. Entity Relationship Diagram (Conceptual)

```mermaid
erDiagram
    USER ||--o{ DIALOGUE : "participates in"
    DIALOGUE ||--|{ UTTERANCE : "contains"
    
    USER {
        string user_id PK
        int age
        string gender
        int n_dialogues
        string source_dataset "HCI_P2 | Persona-Chat | EmpatheticDialogues"
    }
    
    DIALOGUE {
        string dialogue_id PK
        string user_id FK
        int quality_rating
        float mean_politeness_score (z-scored)
        int conversation_length (word count)
        float user_sentiment (average)
        bool is_complete
        string source_dataset
    }
    
    UTTERANCE {
        string utterance_id PK
        string dialogue_id FK
        string speaker_role "user|chatbot"
        string text_content
        float politeness_score
    }
```

## 2. Data Schema Definitions

### 2.1 Raw Data (Multi-Source)
- **Sources**: `YCAI3/HCI_P2`, `facebook/Persona-Chat`, `daanelson/EmpatheticDialogues`.
- **Fields**: `text`, `quality_rating`, `user_id`, `metadata` (age, gender), `source`.
- **Format**: Parquet or JSON (depending on the specific file structure in each repo).

### 2.2 Processed Data (Intermediate)
- **File**: `data/processed/dialogues_with_scores.csv`
- **Fields**:
  - `dialogue_id`: Unique identifier (prefixed with source, e.g., `HCI_001`).
  - `user_id`: Link to user.
  - `quality_rating`: Integer (1-5).
  - `mean_politeness_score`: Float (z-scored).
  - `conversation_length`: Integer (word count).
  - `user_sentiment`: Float (average sentiment score of user utterances).
  - `utterance_count`: Integer.
  - `is_complete`: Boolean (True if all required fields present).
  - `source_dataset`: String (e.g., "HCI_P2").

### 2.3 Output Data (Results)
- **File**: `results/clmm_results.csv`
- **Fields**:
  - `term`: Variable name (e.g., `mean_politeness_score`).
  - `estimate`: Coefficient.
  - `std_error`: Standard error.
  - `z_value`: Z-statistic.
  - `p_value`: Raw p-value.
  - `p_adj`: Adjusted p-value (Bonferroni/BH).
  - `confidence_interval_lower`: 95% CI lower bound.
  - `confidence_interval_upper`: 95% CI upper bound.
  - `model_type`: "CLMM" or "Robustness" or "Subgroup".
  - `subgroup`: "All", "Age_<30", "Gender_Female", etc.
  - `source_dataset`: "All" or specific dataset name if run separately.

## 3. Data Processing Pipeline

1. **Download**: Fetch all three datasets to `data/raw/`. Verify checksums.
2. **Parse**: Extract dialogues, split into utterances (user/chatbot).
3. **Filter**:
   - Exclude dialogues with missing `quality_rating`.
   - Exclude dialogues with no chatbot utterances.
   - Log excluded counts.
4. **Score**:
   - Run `jfiedler/politeness-bert` on each chatbot utterance.
   - Compute mean per dialogue.
   - Z-score the mean across the **merged** dataset.
   - Compute `user_sentiment` (using `textblob` or `vader`).
5. **Aggregate**: Create `dialogues_with_scores.csv`.
6. **Model**: Fit CLMM, generate `clmm_results.csv`.
7. **Validate**: Check output schema against `contracts/output.schema.yaml`.

## 4. Data Quality Rules

- **Completeness**: `quality_rating` must be non-null.
- **Validity**: `quality_rating` must be in [1, 5].
- **Consistency**: `mean_politeness_score` must be finite (no NaN/Inf).
- **Uniqueness**: `dialogue_id` must be unique.
- **Referential Integrity**: `user_id` in `DIALOGUE` must exist in `USER`.

## 5. Filtering Logic (Edge Cases)
- **Missing Quality Rating**: Exclude dialogue. Log count.
- **No Chatbot Utterances**: Exclude dialogue. Log count.
- **Classifier Failure**: Assign NaN, exclude utterance from mean. Log count.
- **Missing Demographics**: Exclude from subgroup analysis, retain for main analysis. Log count.
- **Model Convergence Failure**: Report failure, attempt simplified model (remove random effects), log diagnostic.
- **Small Subgroup**: Skip if n < 30. Log exclusion.