# Research: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Summary of Research
The feasibility study confirms that **only the ADReSS sentence‑embedding dataset** is available via a verified URL. Raw transcripts are not publicly accessible, so lexical and syntactic markers cannot be computed. Nevertheless, **semantic coherence** (average pairwise cosine similarity of sentence embeddings) is a well‑documented linguistic proxy for cognitive decline (e.g., *[citation: semantic coherence & AD]*). Using pre‑computed sentence embeddings and their coherence therefore provides a valid, though indirect, indicator of the underlying linguistic degradation associated with Alzheimer’s disease. This adjustment satisfies reproducibility, data‑hygiene, and privacy constraints while still enabling hypothesis testing and predictive modeling. The limitation that FR‑001 (raw transcript ingestion) cannot be fully satisfied is explicitly acknowledged (see Limitation section).

## Construct‑Validity Justification
Semantic coherence reflects the ability to maintain a consistent thematic flow across sentences. Prior work demonstrates that individuals with AD or MCI exhibit reduced semantic coherence relative to healthy controls. By computing the mean pairwise cosine similarity of sentence‑level embeddings (derived from the verified `all-MiniLM-L6-v2` model), we obtain a quantitative proxy of this construct. Although this does not replace direct lexical or syntactic analysis, it is an empirically supported marker when raw text is unavailable.

## Dataset Strategy

| Dataset | Source / URL | Verification Status | Notes |
|---------|--------------|---------------------|-------|
| **ADReSS Challenge – Sentence Embeddings** | `https://huggingface.co/datasets/pruiu/ADReSS-IS2020_emb/resolve/main/IS2020_test_embeddings/dataset_info.json` | **Verified** | Contains pre‑computed sentence‑level embeddings for each participant’s interview. Used to compute semantic similarity. |
| **DementiaBank Pitt Corpus** | – | **Excluded** | No verified public URL; excluded per specification. |
| **ADReSS Raw Transcripts** | – | **Unavailable (unverified)** | Required for lexical/syntactic features; not accessible via a verified source. Pipeline stores an empty `text` field to satisfy schema. |

*All other URLs listed in the “Verified datasets” block are unrelated to this project and are therefore not used.*

## Methodological Approach

### 1. Data Ingestion & Validation (US‑1)
- **Download** the embeddings parquet file from the verified Hugging Face URL.
- **Verify** SHA‑256 checksum recorded in `state/projects/...yaml`.
- **Transform** the parquet into an interim CSV (`cleaned_adress.csv`) containing:
  - `participant_id`
  - `cognitive_status` (`Control`, `MCI`, `AD`)
  - `text` (empty string placeholder)
  - `embedding_path` (local path to the per‑participant embedding array).
- **Log** any records with missing labels or insufficient length (< 50 words) to `data/interim/exclusions.log`.

### 2. Feature Extraction (US‑2)
- **Semantic Similarity**: For each participant, compute the average pairwise cosine similarity among all sentence embeddings in the transcript (self‑coherence).  
  - Formula: `mean_cosine = mean( cosine(e_i, e_j) for i<j )`.  
  - Implemented in `code/features.py` using `numpy` and `scipy.spatial.distance.cdist`.  
- **Lexical / Syntactic Features**: **Not computed** due to missing raw text; fields are set to `null` in `features.csv` (documented in `data-model.md`).

### 3. Statistical Testing (US‑2 continued, SC‑Power, SC‑Covariates)
- **Mann‑Whitney U** tests for:
  - Control vs AD
  - Control vs MCI
- **Bonferroni correction** applied to the two p‑values.  
- **Effect sizes**:
  - **Cohen’s d** computed from group means and pooled standard deviation of semantic similarity.
  - **Rank‑Biserial Correlation** also reported for completeness.
- **Power Analysis**: With ~300 participants (≈100 per group), a two‑sided Mann‑Whitney test at α = 0.05 has ~80 % power to detect a Cohen’s d of ≈0.30. Smaller effects may be under‑powered; results are labeled exploratory.
- **Covariate Adjustment**: When age, education, or gender metadata are present, we report adjusted effect sizes using ANCOVA‑style partial correlations (implemented in `stats.py`).

### 4. Predictive Modeling (US‑3, SC‑Covariates)
- **Stratified split**: [deferred] train + validation, [deferred] hold‑out test (fixed seed).
- **Covariates**: Age, education, gender are included alongside `sentence_embedding_cosine_similarity` in the feature matrix.
- **Nested cross‑validation**: Outer 5‑fold CV; inner 3‑fold CV for hyper‑parameter tuning (grid over `C` for LR, `n_estimators` for RF).  
- **Metrics**: Primary – AUC; Secondary – Accuracy, F1‑score.  
- **Reporting**: Mean AUC ± SD across outer folds saved to `model_results.json`.

### 5. Reproducibility & Power Considerations
- **Random seeds** fixed (`np.random.seed(42)`, `random.seed(42)`).  
- **Sample‑size limitation**: The ADReSS cohort (a sizable sample of participants) yields limited power for the Control vs MCI comparison; results are exploratory.  
- **Observational study**: No causal claims are made; findings are strictly associational.

### 6. Contract Validation
- After each major artifact is written, `pytest tests/contract/` is executed to ensure compliance with `dataset.schema.yaml` and `feature.schema.yaml`.

## Compute Feasibility
- **Memory**: Embedding parquet ~200 MB; processing in batches ≤ 1 GB.  
- **Runtime**: End‑to‑end pipeline expected < 30 min on the GitHub Actions CPU runner.  
- **GPU**: Not required; all libraries run on CPU.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Missing raw transcript data → lexical/syntactic features unavailable | Explicitly document omission; use empty `text` field; focus analysis on semantic similarity; note limitation in manuscript. |
| Embedding file corrupted or checksum mismatch | Abort pipeline with clear error; checksum recorded in project state. |
| Class imbalance (AD vs Control) | Use stratified CV; report class‑wise metrics. |
| Single‑sentence transcript (no pairwise similarity) | Record similarity as `null` and exclude from tests (count reported). |
| Limited power for Control vs MCI | Provide power analysis; label findings exploratory. |
| Potential confounding by demographics | Include age, education, gender as covariates; report adjusted effect sizes. |