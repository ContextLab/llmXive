# Data Model: The Influence of Chatbot Politeness on User-Perceived Quality

## 1. Conceptual Model

The data model represents the relationship between Users, their Dialogues, and the computed Politeness/Quality metrics.

### Entities

1.  **User**: A participant in the dataset.
    -   `user_id`: Unique identifier.
    -   `age`: Age of the user (numeric, optional).
    -   `gender`: Gender of the user (categorical, optional).
    -   `num_dialogues`: Count of dialogues (derived).
2.  **Dialogue**: A single conversation.
    -   `dialogue_id`: Unique identifier.
    -   `user_id`: Foreign key to User.
    -   `quality_rating`: Ordinal rating (1-5).
    -   `conversation_length`: Word count or utterance count.
    -   `mean_politeness_score`: Z-scored mean of utterance scores.
    -   `raw_politeness_mean`: Raw mean before z-scoring.
3.  **Utterance**: A single message.
    -   `utterance_id`: Unique identifier.
    -   `dialogue_id`: Foreign key to Dialogue.
    -   `speaker_role`: 'user' or 'chatbot'.
    -   `text_content`: The message text.
    -   `politeness_score`: Score from `jfiedler/politeness-bert`.

### Relationships
-   **User** 1:N **Dialogue**
-   **Dialogue** 1:N **Utterance**

## 2. Data Flow

1.  **Raw Data**: Downloaded from HuggingFace (Parquet/CSV).
    -   *Fields*: `dialogue_id`, `user_id`, `utterances` (list), `metadata` (age, gender, rating).
2.  **Processed Data**:
    -   Filtered for completeness (rating present, chatbot utterances exist).
    -   Scores computed per utterance.
    -   Aggregated to mean per dialogue.
    -   Z-scored.
3.  **Output Data**:
    -   Model coefficients, p-values, confidence intervals.

## 3. Schema Definitions

The following schemas are defined in `contracts/`:
-   `dataset.schema.yaml`: Structure of the processed dialogue data.
-   `output.schema.yaml`: Structure of the statistical results.

## 4. Data Hygiene & Versioning

-   **Checksums**: All raw files under `data/raw/` are checksummed (SHA-256).
-   **Immutability**: Raw files are never modified. Derivations are written to `data/processed/`.
-   **PII**: No personally identifiable information (names, emails) is stored in `data/processed/`. `user_id` is an anonymized hash.
