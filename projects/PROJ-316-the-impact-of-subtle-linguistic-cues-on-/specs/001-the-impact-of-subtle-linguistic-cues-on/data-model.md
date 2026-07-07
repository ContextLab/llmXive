# Data Model: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

## Entities & Relationships

### ConversationRecord
- **Purpose**: Represents a single chatbot interaction.  
- **Attributes**:  
  - `conversation_id` (str, unique)  
  - `raw_text` (str)  
  - `length` (int, word count)  
  - `turn_count` (int)  
- **Source**: Raw JSONL file (e.g., from HuggingFace dataset).  
- **Derivation**: None; raw input.

### LinguisticMetrics
- **Purpose**: Derived quantitative scores from `ConversationRecord`.  
- **Attributes**:  
  - `conversation_id` (str, FK to ConversationRecord)  
  - `pronoun_rate` (float, 0.0–1.0)  
  - `hedge_density` (float, 0.0–1.0)  
  - `valence_score` (float, -1.0–1.0)  
  - `excluded_reason` (str, optional: "empty_text", "missing_rating")  
- **Derivation**: Computed by `extraction/` scripts per FR-001, FR-006.  
- **Source**: `data/processed/features.csv`.

### HumanRating
- **Purpose**: Subjective authenticity score assigned by human annotator.  
- **Attributes**:  
  - `conversation_id` (str, FK to ConversationRecord)  
  - `authenticity_score` (int, 1–5 Likert)  
  - `rater_id` (str)  
  - `annotation_instructions` (str, reference to document)  
  - `krippendorff_alpha` (float, ≥0.7 required)  
- **Source**: External verified dataset or annotation process (FR-009).  
- **Derivation**: Aggregated per `conversation_id` if multiple raters.

### AnalysisResult
- **Purpose**: Final statistical output.  
- **Attributes**:  
  - `feature` (str)  
  - `correlation_type` (str: "pearson", "spearman")  
  - `coefficient` (float)  
  - `p_value` (float)  
  - `adjusted_p_value` (float, BH-corrected)  
  - `ci_lower` (float)  
  - `ci_upper` (float)  
  - `regression_coefficient` (float, optional)  
  - `vif` (float, optional)  
- **Source**: `analysis/` scripts.  
- **Derivation**: Computed from `LinguisticMetrics` and `HumanRating`.

## Relationships

- `ConversationRecord` 1:1 `LinguisticMetrics` (one-to-one; one record per conversation).  
- `ConversationRecord` 1:1 `HumanRating` (one aggregated rating per conversation).  
- `LinguisticMetrics` + `HumanRating` → `AnalysisResult` (many-to-one; one result per feature).

## Data Flow

1. **Raw Input**: `data/raw/conversations.jsonl` → `ConversationRecord`.  
2. **Extraction**: `ConversationRecord` → `LinguisticMetrics` (via `extraction/` scripts).  
3. **Rating Merge**: `LinguisticMetrics` + `HumanRating` → Joined dataset (exclude missing ratings).  
4. **Analysis**: Joined dataset → `AnalysisResult` (via `analysis/` scripts).  
5. **Output**: `data/derived/analysis_results.csv`.

## Constraints & Validation

- **Empty Text**: If `length` < 5, skip metric calculation; set `excluded_reason = "empty_text"`.  
- **Missing Rating**: If `authenticity_score` is null, exclude row; log count.  
- **Skewness**: If Shapiro-Wilk p < 0.05, flag in report; suggest log-transform.  
- **VIF**: If VIF > 5, flag multicollinearity; do not claim independent effects.  
- **Authenticity Scale**: Must be 1–5 Likert; reject if outside range.  
- **Inter-Rater Reliability**: Krippendorff’s α ≥ 0.7 required; reject if lower.

## File Formats

- **Raw**: JSONL (one conversation per line).  
- **Processed**: CSV (features.csv, ratings.csv).  
- **Derived**: CSV (analysis_results.csv).  
- **Checksums**: SHA-256 recorded in `state/projects/PROJ-316-...yaml`.