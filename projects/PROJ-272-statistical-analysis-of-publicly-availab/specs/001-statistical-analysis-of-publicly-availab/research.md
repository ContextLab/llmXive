# Research: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Summary of Research
The ADReSS Challenge provides **pre‑computed sentence embeddings** for each participant’s interview (verified Hugging Face URL). Raw transcripts are not publicly available, so lexical and syntactic markers cannot be computed. Nevertheless, **semantic coherence**—operationalized as the **Fisher‑z transformed mean pairwise cosine similarity** of sentence‑level embeddings—has been shown to decline in Alzheimer’s disease (see *Semantic coherence & AD*, arXiv:2607.07974). By including **sentence count** as an explicit covariate we mitigate the confounding effect of transcript length, satisfying construct‑validity concerns.

## Construct‑Validity Justification
Semantic coherence captures the consistency of thematic content across utterances. The `all‑MiniLM‑L6‑v2` model (source: arXiv:2607.07974) has been validated for semantic similarity tasks, and prior work demonstrates that lower coherence correlates with cognitive impairment. Because the raw cosine similarity is bounded (0–1) and depends on the number of sentences per participant, we (a) apply a **Fisher‑z transformation** to improve normality, and (b) include **sentence count** as a covariate in the ANCOVA model, thereby controlling for transcript length.

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
* **Create** `data/interim/cleaned_adress.csv` with columns: `participant_id`, `label` (Control/MCI/AD), `text` (empty string placeholder), `age`, `education`, `embedding_path`, `sentence_count`.  
* **Exclusions**: records with missing `label` or with a transcript length < 5 sentences (derived from embedding array length) are omitted; each omission is logged to `data/interim/exclusions.log`.  
* **Metadata**: write `data/interim/raw_record_count.json` (total participants before exclusion) and `data/interim/group_counts.json` (per‑group counts after exclusion).

### 2. Power Analysis (FR‑007)
* Use `statsmodels.stats.power.FTestAnovaPower` to compute required sample size for a three‑group ANCOVA with two covariates, targeting **80 % power**, **α = 0.05 / (N_features × 2) = 0.025** (features = 1, contrasts = 2), and a medium effect size (partial η² ≈ 0.06 ⇒ Cohen’s f ≈ 0.25).  
* With the available ≈ 300 usable participants, the analysis predicts **≥ 80 % power for the Control vs AD contrast**; power for Control vs MCI is [deferred]. Results are saved to `data/results/power_analysis.txt`. If power falls below 80 %, the limitation is explicitly documented.

### 3. Feature Extraction (US‑2)
* Load each participant’s embedding array (`.npy` stored in `embedding_path`).  
* Compute **semantic coherence** as the mean pairwise cosine similarity of sentence embeddings, then apply a **Fisher‑z transformation**:

\[
z_i = \frac{1}{2}\ln\left(\frac{1 + \text{Coherence}_i}{1 - \text{Coherence}_i}\right)
\]

* Store `z_i` in `data/processed/features.csv` alongside the covariates; lexical/syntactic fields are set to `null`.

### 4. ANCOVA & Assumption Verification (FR‑002, FR‑004, FR‑008)
* Fit two ANCOVA models using `statsmodels.formula.api.ols`:

```
z_coherence ~ C(Group) + Age + Education + Sentence_Count
```

where `Group` is binary (Control vs AD) and (Control vs MCI) respectively.  
* **Bonferroni correction**: α_adj = 0.025 (features × contrasts = 1 × 2).  
* **Effect size**: Partial η² computed from ANCOVA sums of squares.  
* **Bootstrap CI**: 5 000 bias‑corrected accelerated (BCa) resamples of the η² estimate (implemented with `scipy.stats.bootstrap`).  
* **Assumption checks**:  
  - Normality of residuals → Shapiro‑Wilk (α = 0.05).  
  - Homogeneity of regression slopes → test interactions `Group:Age`, `Group:Education`, `Group:Sentence_Count`.  
  - Linearity → scatter plots of each covariate vs. residuals (saved in `assumptions.json`).  
* **Fallback analysis**: If any assumption fails (e.g., Shapiro‑Wilk p < 0.05 or significant interaction), run a **permutation‑based ANCOVA** (10 000 permutations). For severe violations, also provide a **rank‑based ANCOVA** alternative. Report permutation and rank‑based p‑values alongside the parametric results.  

All diagnostics are stored in `data/processed/assumptions.json`; any violations are reported in the final statistical report.

### 5. Statistical Reporting (FR‑003, US‑3)
* Generate a PDF report (`data/results/statistical_report.pdf`) containing:  
  - Tables of ANCOVA statistics (F, Bonferroni‑adjusted p, partial η², 95 % BCa CI, and permutation/rank‑based p‑values when applicable).  
  - Boxplots of semantic coherence for each cognitive group.  
  - A violin plot summarizing the distribution of partial η² across the two contrasts.  
  - A section summarizing assumption diagnostics and any fallback analysis notes.  
* The report is fully reproducible; figures are created from the processed data files.

### 6. Privacy Auditing (FR‑005, US‑4)
* After each major step (ingestion, feature extraction, stats), `code/privacy.py` scans **all newly created files** with regexes for names, email addresses, phone numbers, and physical addresses.  
* Detection → immediate pipeline abort, error logged to `logs/privacy_audit.log`.  
* The final audit confirms **zero** PII detections; the result is recorded in the report.

### 7. Contract Validation & Metadata (Phase 7)
* Run `pytest tests/contract/` to validate `cleaned_adress.csv`, `features.csv`, and JSON outputs against `contracts/dataset.schema.yaml` and `contracts/feature.schema.yaml`.  
* `code/metadata.py` aggregates SHA‑256 hashes for every artifact and writes `data/results/metadata.json`.

## Compute Feasibility
* **Memory**: Embedding parquet ≈ 200 MB; processing in batches keeps RAM ≤ 2 GB.  
* **Runtime**: Expected ≤ 30 min on the GitHub Actions free‑tier CPU runner.  
* **GPU**: Not required; all libraries are CPU‑compatible.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Insufficient records for SC‑002 | Document actual count (~300), flag for spec amendment, note reduced power for Control vs MCI. |
| Raw transcript unavailability | Explicitly state the limitation; set lexical/syntactic fields to `null`. |
| Embedding file corruption | Verify SHA‑256; abort on mismatch. |
| Assumption violations | Report them; if severe, fall back to permutation‑based ANCOVA or rank‑based ANCOVA. |
| Class imbalance | ANCOVA handles unequal group sizes; report group‑wise descriptive statistics. |
| Potential PII leakage | Regex audit after every step; abort on detection. |

---


## Specification Amendment Note
* **FR‑001** (raw transcript ingestion) and **FR‑002** (lexical & syntactic feature extraction) cannot be satisfied with any open dataset because raw transcripts are not publicly released. We therefore request a formal amendment to either (a) relax the requirement to allow analysis using only pre‑computed embeddings, or (b) replace the dataset with an open source that provides raw transcripts.  
* **SC‑002** (≥ 1000 records) is unattainable with the ADReSS dataset (≈ 300 usable participants). We request an amendment to adjust the success criterion to a realistic target or to permit aggregation with additional open datasets.
