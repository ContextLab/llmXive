# Research: Survey of Large Audio Language Models – Hallucination Analysis

## 1. Problem Statement
The project aims to quantify the trustworthiness of Large Audio Language Models (LALMs) by measuring hallucination rates across speech, music, and environmental sound domains. A secondary objective is to explore whether domain-specific training data volume correlates with these hallucination rates.

## 2. Dataset Strategy

### Verified Datasets
Per the project constraints, only the following verified sources are used. These datasets were selected for their availability of fine-grained ground-truth entity metadata (speaker, instrument, category) required for hallucination detection.

| Domain | Dataset Name | Verified URL (HuggingFace) | Usage | Metadata Check |
|--------|--------------|----------------------------|-------|----------------|
| **Environmental Sounds** | ESC-50 | ` | Primary test set for environmental sounds. | Verify `category` field exists. |
| **Music** | FMA Small | ` | Primary test set for music. Provides `genres` and `instrument` tags. | Verify `instrument` field exists; if missing, sample excluded. |
| **Speech** | LibriSpeech (dev-clean) | ` | Primary test set for speech. Provides `speaker_id` and `text`. | Verify `speaker_id` field exists. |

*Note: The original spec mentioned MusicBench and AudioBench, but these lack verified URLs in the input block and often lack the specific entity-level metadata required for rule-based detection. The plan switches to FMA Small and LibriSpeech which are verified and metadata-rich.*

### Training Data Volume Estimates (FR-006)
- **Source**: Published model cards, technical reports (PDFs), and dataset papers.
- **Method**: Parse text from model documentation to extract domain-specific training hours or token counts.
- **Proxy Derivation**: If exact counts are unavailable, derive a relative proxy (e.g., "High", "Medium", "Low") based on dataset size descriptions.
 - **Uncertainty Flag**: Assign `High` uncertainty if derived from vague text (e.g., "large dataset"), `Medium` if from token counts, `Low` if from explicit hours.
- **Sensitivity**: Perform a sensitivity analysis by testing all rank permutations of the ordinal proxy to ensure the observed trend is not an artifact of arbitrary ranking.

## 3. Methodology

### 3.1 Audio Preprocessing (FR-002)
- Resample all audio to a standard telephony bandwidth.
- Truncate samples >10 seconds.
- Log discarded samples to `pipeline.log`.

### 3.2 Inference (FR-001, FR-003)
- Load LALMs (≤2B params) using `torch` CPU-only.
- Use standardized prompting template for caption generation.
- Store raw text output.

### 3.3 Hallucination Detection (FR-004, FR-012)
- **Rule-Based Detector**: Compare caption entities against ground truth metadata.
- **Normalization**: Lowercase and strip strings.
- **Enhanced Matching**:
 - **Fuzzy Match**: Use Levenshtein distance to handle minor spelling variations.
 - **Synonym Match**: Use WordNet to expand ground truth entities (e.g., "canine" -> "dog") before comparison.
- **Validity**: Use external lexical resources (WordNet, MusicBrainz) distinct from model training data.
- **Completeness Check**: If ground truth metadata is incomplete (<90% fields present), flag the hallucination rate as "Potentially Inflated".

### 3.4 Statistical Analysis (FR-005, FR-007)
- **Per-Domain Rates**: Compute hallucination rate with Wilson-score confidence interval.
- **Domain Comparison**: Perform **Kruskal-Wallis H-test** to check for significant differences in rates across domains (Constitution Principle VI).
- **Correlation (Exploratory)**:
 - Compute Spearman's rank correlation between training data volume (ordinal proxy) and hallucination rate.
 - **Constraint**: N=3 (domains). **NO p-values or confidence intervals reported** as they are statistically invalid for N=3.
 - **Output**: Report coefficient and a descriptive statement of rank order (e.g., "Rank order: Env < Music < Speech").
 - **Sensitivity**: Report if the trend holds across different rank assignments of the proxy.
- **Framing**: All results framed as **associational** (observational design). No causal claims.

### 3.5 Human Validation (FR-008, FR-009)
- **Sampling**: Select a representative sample size.
 - **Redistribution Logic**: If a domain is missing, redistribute its quota equally to remaining domains (e.g., 2 domains -> 75 each).
- **Crowd Retrieval**: Use `code/retrieve_crowd_judgments.py` to download judgments from the crowdsourcing platform and format as `human_judgments.csv`.
- **Agreement**: Compute Cohen’s κ; flag if <0.6.

## 4. Computational Feasibility
- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
 - Use small models (≤2B) in default precision (no 8-bit/4-bit).
 - Process data in batches to stay under RAM limits.
 - **Runtime Guard**: If elapsed time > 4.5 hours, automatically reduce sample size by [deferred].
- **Libraries**: `torch` (CPU wheel), `transformers`, `scikit-learn`, `nltk`, `fuzzywuzzy`. No CUDA.

## 5. Risks & Mitigations
- **Risk**: Missing metadata in alternative datasets (FMA/LibriSpeech).
 - **Mitigation**: Implement metadata validation step; exclude samples with missing fields and log them.
- **Risk**: Model OOM on 7GB RAM.
 - **Mitigation**: Implement aggressive garbage collection; process one model at a time; use `torch.no_grad()`; reduce batch size if needed.
- **Risk**: Correlation instability due to ordinal proxy.
 - **Mitigation**: Perform sensitivity analysis across rank permutations; report trend stability.