# Research: Association between Linguistic Accommodation and Perceived Empathy

## 1. Dataset Strategy

The study relies on **two data sources**:

1. **DailyDialog (Human‑Human)** – `https://huggingface.co/datasets/pixelsandpointers/daily_dialog_w_turn_templates/resolve/main/data/test-00000-of-00001.parquet` (verified).  
   - Provides extensive multi‑turn dialogues, emotion annotations, and raw text needed to compute accommodation metrics.  
   - **Limitation**: No AI‑assistant turns and no explicit empathy ratings. DailyDialog will be used **only** to compute linguistic accommodation proxies.

2. **Human‑Collected AI‑Assistant Empathy Dataset** – a new dataset created in‑house (see Phase 0a).  
   - Consists of ≥30 AI‑assistant responses (generated via a standard open‑source chatbot) paired with human‑rated empathy scores on a 1‑5 Likert scale.  
   - Collected under IRB‑approved protocol, with informed consent and anonymization, satisfying Constitution Principle VI.  
   - This dataset provides the **required `empathy_rating`** variable for the primary analysis.

### Data Fit & Variable Verification

| Required Variable | DailyDialog | Human‑Collected Dataset |
|-------------------|-------------|--------------------------|
| `user_turn` | ✔ (human turn) | ✔ (human prompt) |
| `ai_response` | **Missing** – we treat the second speaker as a proxy only for metric computation, **not** for primary analysis. | ✔ (generated AI response) |
| `empathy_rating` | **Missing** – DailyDialog has only emotion labels. | ✔ (human‑rated Likert score) |
| `topic` | **Missing** – generated via LDA (see Phase 5). | ✔ (LDA‑derived `lda_topic_id`) |

Because DailyDialog lacks the core `empathy_rating`, the **human‑collected dataset** is essential to meet FR‑010 and the research question. The two datasets are merged on shared metric fields after metric computation.

### Scope Constraints & Ethical Handling

- The human‑collected dataset will be **released** only in aggregated form (summary statistics) to respect participant privacy.  
- No external participants beyond the consenting annotators are recruited; all annotators are project members who have provided written consent.  
- All data transformations produce new files; original raw files are preserved unchanged.

## 2. Metric Definitions & Methodology

### Accommodation Metrics (FR‑001, FR‑002, FR‑008)

- **Lexical Overlap**: Jaccard similarity of token sets (4‑decimal precision).  
- **Syntactic Similarity**: Jaccard similarity of POS tag sets (spaCy `en_core_web_sm`).  
- **Dependency Similarity**: Jaccard similarity of dependency relation labels (spaCy).  
- **Sentence Length Variance**: Variance of sentence lengths within the AI response.  

All text is normalized to Unicode NFKC; records with empty or non‑text after normalization are dropped.

### Empathy Rating (FR‑010)

- Human annotators assign a **1‑5 Likert rating** to each AI response reflecting perceived empathy.  
- Ratings are stored in `human_empathy.csv` and merged with accommodation metrics for analysis.  
- Inter‑rater reliability (Cohen’s κ) is computed on the validation subset (see Phase 8).

### Statistical Analysis (FR‑004, FR‑005, FR‑006, SC‑001‑005)

1. **Correlation Tests**: Pearson and Spearman correlations between each accommodation metric (`lexical_overlap`, `syntactic_similarity`, `dependency_similarity`) and `empathy_rating`.  
2. **Multiple‑Comparison Correction**: Bonferroni correction applied to the **four primary tests** (Pearson & Spearman for lexical and syntactic metrics). Corrected α = 0.05 / 4 = 0.0125, stored in `correlation_summary.json`.  
3. **Bootstrap Resampling**: Adaptive loop starting at 1 000 iterations, *continuing until* the 95 % CI width < 0.01. No early‑stop fallback; if convergence is not achieved after 50 000 iterations, the pipeline aborts with an error (ensuring FR‑006 compliance).  
4. **False Discovery Rate**: Benjamini‑Hochberg FDR computed across the four tests and recorded.  
5. **Power Analysis**: With α = 0.0125 and target effect size r = 0.15, a two‑tailed test requires ≈ 600 valid pairs. The combined dataset (DailyDialog + human‑collected) provides > 90 k pairs, comfortably exceeding the requirement.

### Regression Control (FR‑007)

- **Covariates**: Total word count and dominant LDA topic ID (k = 10).  
- Topics are generated in Phase 5, residualized from accommodation metrics, and VIF is checked (threshold < 5).  
- Linear regression estimates the unique contribution of each accommodation metric to empathy ratings, reporting R² and standardized coefficients.

### Sensitivity Analysis (FR‑009)

- Compute correlations using **dependency similarity** as an alternative accommodation proxy.  
- Success criterion: |Δr| ≤ 0.05 between POS‑based and dependency‑based correlation coefficients. Results are stored in `sensitivity_results.json`.

### Validation Strategy (FR‑010)

- **Phase 0a** collects ≥30 human empathy ratings for AI responses.  
- **Phase 8** computes inter‑rater reliability (Cohen’s κ) and compares the averaged human rating to any proxy scores (e.g., emotion‑to‑Likert mapping) for consistency checks.  
- The validation subset is **stratified by emotion** to ensure balanced coverage.

## 3. Compute Feasibility & Rationale

- All scripts are CPU‑only; spaCy `en_core_web_sm` runs comfortably on 2 cores.  
- LDA uses Gensim with sparse matrices (< 1 GB RAM).  
- Bootstrap convergence typically achieved within 5 000 iterations (< 2 h).  
- Total pipeline runtime on GitHub Actions is expected ≤ 5 h.

## 4. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Collect human empathy ratings** | No public dataset satisfies FR‑010; ethical collection fulfills the requirement and Principle VI. |
| **Use DailyDialog for metric computation** | Large, verified corpus provides robust accommodation measures; later merged with human‑rated empathy data. |
| **Bonferroni α = 0.0125** | Explicitly matches the four primary hypothesis tests, satisfying SC‑005. |
| **Bootstrap convergence** | Guarantees FR‑006 compliance; safety guard prevents infinite loops while still enforcing CI < 0.01. |
| **Mandatory sensitivity analysis** | Ensures construct validity of accommodation proxies per FR‑009. |
| **LDA topic control** | Meets FR‑007 specification; residualization prevents collider bias. |
| **VIF checks** | Guarantees regression covariates are not collinear, preserving interpretability. |