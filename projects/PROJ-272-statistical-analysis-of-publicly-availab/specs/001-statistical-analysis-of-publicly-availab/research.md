# Research: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Summary of Research

This research phase validates the feasibility of the statistical analysis pipeline, identifies suitable datasets, and defines the methodological approach for feature extraction and hypothesis testing. Key findings confirm that the ADReSS raw transcripts are available via the official GitHub repository, while DementiaBank lacks a verified public URL. The analysis will rely on CPU-tractable methods (logistic regression, random forest, spaCy parsing, sentence-transformers `all-MiniLM-L-v2`) to ensure compatibility with the 7 GB RAM constraint.

## Dataset Strategy

| Dataset | Source/URL | Status | Notes |
|---------|------------|--------|-------|
| **DementiaBank Pitt Corpus** | NO verified source found | **Excluded (Spec Gap)** | Spec requires this dataset. No verified URL exists in the "Verified datasets" block. **Action**: Plan excludes DementiaBank from implementation scope. FR-001 will be satisfied by ADReSS only. Spec must be updated to remove DementiaBank or provide a verified source. |
| **ADReSS Challenge (Raw Text)** | ` (Verified) | **Verified** | Contains raw interview transcripts and labels. Will be loaded via direct fetch from GitHub. |
| **ADReSS (Embeddings)** | `https://huggingface.co/datasets/pruiu/ADReSS-IS2020_emb` | **Ignored for Features** | Contains pre-computed embeddings. **Strictly ignored** for feature extraction to prevent circular validation. Used only for reference if raw text is missing (fallback fails if raw text missing). |

**Note**: The implementation fetches raw text from the ADReSS GitHub repository. Pre-computed embeddings from HuggingFace are ignored to ensure predictor independence (scientific soundness).

## Methodological Approach

### 1. Data Preprocessing (FR-001)
- **Cleaning**: Remove non-verbal annotations (`<laughter>`, `<pause>`, etc.) using regex.
- **Normalization**: Force UTF-8 encoding.
- **Filtering**: Exclude records with < 50 words (Edge Case).
- **Label Validation**: Exclude records with missing cognitive status (US-1).

### 2. Feature Extraction (FR-002)
- **Lexical**:
 - Type-Token Ratio (TTR): `n_unique_tokens / n_total_tokens`.
 - MTLD (Measure of Textual Lexical Diversity): Using `langid` or custom implementation.
 - Noun/Verb Ratio: POS tagging via `spaCy`. **Zero-Handling**: If nouns=0 or verbs=0, set ratio to `NaN` and exclude record from this specific metric (retained for others).
- **Syntactic**:
 - Mean Clause Length: Calculated using `spaCy` dependency parsing to identify clauses (finite verbs), not punctuation.
 - T-unit Count: Count of independent clauses + dependent clauses using `spaCy` parse trees.
- **Semantic**:
 - Sentence Embedding Cosine Similarity: Calculated as the **average pairwise cosine similarity** between all sentence embeddings within a single transcript (self-similarity/coherence). Pre-computed embeddings in the dataset are ignored.

### 3. Statistical Testing (FR-003, SC-002)
- **Test**: Mann-Whitney U test (non-parametric, suitable for small samples).
- **Comparisons**: Control vs. AD, Control vs. MCI.
- **Correction**: Bonferroni correction for multiple comparisons (SC-002).
- **Effect Size**: **Rank-Biserial Correlation** (or Common Language Effect Size) for Mann-Whitney U tests (replaces invalid Cohen's d).
- **Collinearity Check**: Flag records with identical feature vectors (Edge Case).
- **Power Limitation**: Acknowledged limitation for MCI vs Control comparisons (smaller effect size). Results for MCI vs Control are treated as **exploratory/associational** with a warning about potential Type II errors.

### 4. Predictive Modeling (FR-004, FR-005, SC-003, SC-004)
- **Preliminary Sanity Check**:
 - Split: Stratified train/validation/test partition.
 - Models: Logistic Regression, Random Forest.
 - Metrics: AUC, Accuracy, F1-score (on **Test Set** only).
 - Threshold: **Test AUC ≥ 0.70** (Training AUC removed as invalid success criterion).
- **Primary Validation**:
 - Method: Nested k-fold Cross-Validation

The specific value to remove/generalize: 'k'

Rewritten passage:
Nested k-fold Cross-Validation.
 - Outer Loop: multiple folds (evaluation).
 - Inner Loop: Multiple folds (hyperparameter tuning).
 - Metric: Mean AUC (must be > 0.5, p < 0.05).
 - Stability: SD of AUC ≤ 0.05.

## Statistical Rigor & Constraints

- **Multiple Comparisons**: Bonferroni correction applied to all p-values (SC-002).
- **Sample Size/Power**: Acknowledged limitation; nested CV used to maximize data utility. MCI vs Control results flagged as exploratory.
- **Causal Inference**: Observational study; claims framed as associational only.
- **Measurement Validity**: Features (TTR, MTLD, spaCy-based syntax) are standard NLP metrics; sentence-BERT validated for semantic similarity.
- **Collinearity**: Noun/Verb ratio and TTR may be correlated; independent effects will not be claimed if definitionally related.
- **Circular Validation Prevention**: Semantic features computed from raw text only; pre-computed dataset embeddings ignored.

## Compute Feasibility

- **Memory**: Dataset subset to ~7 GB RAM. `all-MiniLM-L-v2` is small (~80MB) and runs on CPU.
- **Runtime**: Nested CV on ~500 samples with 10 features is computationally light (< 1 hour).
- **GPU**: None required. `sentence-transformers` will use CPU (`device='cpu'`).

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **DementiaBank Unavailable** | **Excluded from scope**. Spec flagged for amendment. |
| **ADReSS Raw Text Unavailable** | Pipeline fails fast. Spec's fallback to DementiaBank is unimplementable (no verified source). |
| **Missing Transcripts in ADReSS** | If raw text missing, pipeline fails (cannot compute lexical/syntactic features). |
| **RAM Overflow** | Stream data processing; process in batches if > 1000 records. |
| **Collinearity** | Flag and exclude perfect collinearity; report descriptive stats only. |
| **Zero-Division in Noun/Verb Ratio** | Set to `NaN` and exclude from that specific metric calculation. |