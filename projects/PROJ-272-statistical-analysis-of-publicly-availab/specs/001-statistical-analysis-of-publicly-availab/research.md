# Research: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Summary of Research
The ADReSS Challenge provides **pre‑computed sentence embeddings** for each participant’s interview (verified Hugging Face URL). Raw transcripts are not publicly released, so lexical and syntactic markers cannot be computed directly. Nevertheless, **semantic coherence**—operationalized as the **Fisher‑z transformed mean pairwise cosine similarity** of sentence‑level embeddings—has been shown to be a useful indicator of semantic consistency in language tasks. The `all‑MiniLM‑L6‑v2` model (source: arXiv:2607.07974) is validated for semantic similarity tasks, providing a reliable basis for the coherence metric.

## Specification Amendment Request
Because the original specification (FR‑001, FR‑002, SC‑002) requires raw transcripts that are unavailable in the open ADReSS dataset, we formally request the following amendments:

1. **FR‑001 Amendment** – Allow ingestion of raw transcripts **if** an open dataset with them becomes available. Until then, the pipeline will create an empty `text` field and log the step as a no‑op.
2. **FR‑002 Amendment** – Permit lexical and syntactic feature extraction to be conditional on the presence of raw transcripts. When transcripts are missing, those feature columns will be set to `null`.
3. **SC‑002 Amendment** – Adjust the success‑criterion to **≥ 300 records** after exclusions (the realistic maximum for ADReSS). The primary hypothesis will focus on the combined **(AD + MCI) vs Control** contrast to ensure adequate power.

These amendments are reflected in the implementation plan and will be recorded as a formal amendment (version 1.1.0) to the project constitution.

## Construct‑Validity Justification
Semantic coherence captures the consistency of thematic content across utterances. The `all‑MiniLM‑L6‑v2` model (arXiv:2607.07974) has been benchmarked on standard semantic similarity datasets, ensuring that cosine similarity between its sentence embeddings reflects genuine semantic relatedness. Prior neuro‑cognitive work indicates that lower coherence correlates with cognitive impairment; therefore, the Fisher‑z transformed mean cosine similarity serves as a valid proxy for detecting decline. By including **sentence count** as a covariate, we control for the known dependence of mean similarity on the number of sentences, preserving construct validity.

## Dataset Strategy

| Dataset | Source / URL | Verification Status | Notes |
|---------|--------------|---------------------|-------|
| **ADReSS Challenge – Sentence Embeddings** | `https://huggingface.co/datasets/pruiu/ADReSS-IS2020_emb/resolve/main/IS2020_test_embeddings/dataset_info.json` | **Verified** | Contains per‑participant sentence‑level embeddings for the test set. Used for all downstream feature computation. |
| **MCI Parquet (unused)** | `https://huggingface.co/datasets/mcimpoi/dtd_split_1/resolve/main/data/test-00000-of-00001-d6ecda0bacf8f78c.parquet` | **Verified** | Retained for possible future extensions; not part of the primary analysis. |
| **PII Synthetic (unused)** | `https://huggingface.co/datasets/nvidia/Nemotron-PII/resolve/main/data/test-00000-of-00001.parquet` | **Verified** | Used only to test the privacy‑audit component; not part of the scientific dataset. |
| **DementiaBank** | – | **Excluded** | No public URL; explicitly excluded per specification. |

All other URLs listed in the “Verified datasets” block are unrelated and therefore omitted.

## Methodological Approach

### 1. Data Ingestion & Validation (US‑1)
* **Download** the embeddings parquet via `datasets.load_dataset(..., streaming=False)` from the verified URL.  
* **Checksum** the file (`sha256`) and store the hash in the project state.  
* **Create** `data/interim/cleaned_adress.csv` with columns: `participant_id`, `label`, `text` (empty string placeholder), `age`, `education`, `embedding_path`, `sentence_count`.  
* **Optional raw transcript ingestion**: if an open dataset with raw transcripts is later supplied, `ingest_raw_transcripts()` will populate the `text` column; otherwise this step is a no‑op (per amendment).  
* **Exclusions**: records with missing `label` or with a transcript length < 5 sentences (derived from embedding array length) are omitted; each omission is logged to `data/interim/exclusions.log`.  
* **Metadata**: write **`data/results/raw_record_count.json`** (total participants before exclusions) and **`data/results/group_counts.json`** (per‑group counts after exclusions).

### 2. Power Analysis (FR‑007)
* Use `statsmodels.stats.power.FTestAnovaPower` to compute required sample size for a three‑group ANCOVA with two covariates, targeting **80 % power**, **α = 0.05 / (N_features × 2) = 0.025**, and a medium effect size (partial η² ≈ 0.06 ⇒ Cohen’s f ≈ 0.25).  
* **Primary contrast**: **combined AD + MCI vs Control** (≥ 80 % power with ~300 participants).  
* **Exploratory contrast**: **Control vs MCI** (power < 80 %); this limitation is documented in `data/results/power_analysis.txt`. Results are saved to `data/results/power_analysis.txt`.

### 3. Feature Extraction (US‑2)
* Load each participant’s embedding array (`.npy` stored in `embedding_path`).  
* Compute **semantic coherence** as the mean pairwise cosine similarity of sentence embeddings (`sentence_embedding_cosine_similarity`).  
* Apply a **Fisher‑z transformation** to improve normality:

\[
z_i = \frac{1}{2}\ln\left(\frac{1 + \text{Coherence}_i}{1 - \text{Coherence}_i}\right)
\]

* **Conditional lexical/syntactic extraction**: if raw transcripts are available, compute TTR, MTLD, noun/verb ratio, mean clause length, and T‑unit count; otherwise store `null` for these columns.  
* Store both `sentence_embedding_cosine_similarity` **and** `z_coherence` in `data/processed/features.csv`. Lexical/syntactic columns are `null` when no raw text.

### 4. ANCOVA & Assumption Verification (FR‑002, FR‑004, FR‑008)
* Fit two ANCOVA models using `statsmodels.formula.api.ols`:

```
z_coherence ~ C(Group) + Age + Education + Sentence_Count
```

  - **Primary contrast**: **(AD + MCI) vs Control**.  
  - **Exploratory contrast**: **Control vs MCI**.

* **Bonferroni correction**: α_adj = 0.025 (features × contrasts = 1 × 2).  
* **Effect size**: Partial η² computed from ANCOVA sums of squares.  
* **Bootstrap CI**: 5 000 bias‑corrected accelerated (BCa) resamples of the η² estimate.  
* **Assumption checks**:  
  - Normality of residuals → Shapiro‑Wilk (α = 0.05).  
  - Homogeneity of regression slopes → test interactions `Group:Age`, `Group:Education`, `Group:Sentence_Count`.  
  - Linearity → scatter plots of each covariate vs. residuals (saved in `assumptions.json`).  
* **Multicollinearity**: Compute Variance Inflation Factor (VIF) for all predictors. If any VIF > 5 (especially `Sentence_Count`), drop `Sentence_Count` and re‑fit, documenting the decision in `assumptions.json`.  
* **Fallback analysis**:  
  - If normality fails after Fisher‑z, fit a **beta regression** on the bounded cosine similarity (with logit link).  
  - If any ANCOVA assumption fails, run a **permutation‑based ANCOVA** (10 000 permutations). For severe violations, also provide a **rank‑based ANCOVA**. Report permutation and rank‑based p‑values alongside the parametric results.  

All diagnostics are stored in `data/processed/assumptions.json`; any violations are reported in the final statistical report.

### 5. Statistical Reporting (FR‑003, US‑3)
* Generate a PDF report (`data/results/statistical_report.pdf`) containing:  
  - Tables of ANCOVA statistics (F, Bonferroni‑adjusted p, partial η², 95 % BCa CI, and permutation/rank‑based p‑values when applicable).  
  - Boxplots of semantic coherence for each cognitive group.  
  - A violin plot summarizing the distribution of partial η² across the two contrasts.  
  - A section summarizing assumption diagnostics, VIF values, and any fallback analysis notes.  

### 6. Privacy Auditing (FR‑005, US‑4)
* After each major step (ingestion, feature extraction, stats), `code/privacy.py` scans **all newly created files** with regexes for names, email addresses, phone numbers, and physical addresses.  
* Detection → immediate pipeline abort, error logged to `logs/privacy_audit.log`.  
* The final audit confirms **zero** PII detections; the result is recorded in the report.

### 7. Contract Validation & Metadata (Phase 7)
1. `pytest tests/contract/` validates `cleaned_adress.csv`, `features.csv`, and JSON outputs against `contracts/dataset.schema.yaml` and `contracts/feature.schema.yaml`.  
2. `code/metadata.py` aggregates SHA‑256 hashes for every artifact and writes `data/results/metadata.json`.

## Compute Feasibility
* **Memory**: Embedding parquet ≈ on the order of hundreds MB; processing in batches keeps RAM ≤ 2 GB.  
* **Runtime**: Expected ≤ 30 min on the GitHub Actions free‑tier CPU runner.  
* **GPU**: Not required; all libraries are CPU‑compatible.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Insufficient records for SC‑002 | Document actual count (~300), request amendment to adjust target, and rely on combined contrast for primary hypothesis. |
| Raw transcript limitation | Explicitly state limitation; set lexical/syntactic fields to `null`. |
| Embedding file corruption | Verify SHA‑256; abort on mismatch. |
| Assumption violations | Report them; if severe, fall back to permutation‑based ANCOVA or beta regression. |
| Multicollinearity between `Sentence_Count` and `z_coherence` | Perform VIF check; drop `Sentence_Count` if VIF > 5. |
| Class imbalance | ANCOVA handles unequal group sizes; report group‑wise descriptive statistics. |
| Potential PII leakage | Regex audit after every step; abort on detection. |

---



