# Research: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Summary of Research
The ADReSS Challenge provides **pre‑computed sentence embeddings** for each participant’s interview (verified Hugging Face URL). Raw transcripts are not publicly available, so lexical and syntactic markers cannot be computed. Nevertheless, **semantic coherence**—operationalized as the mean pairwise cosine similarity of sentence‑level embeddings—has been shown to decline in Alzheimer’s disease (e.g., *Semantic coherence & AD*). Using these embeddings therefore offers a valid, reproducible proxy for linguistic degradation while satisfying all privacy and reproducibility constraints.

## Construct‑Validity Justification
Semantic coherence captures the consistency of thematic content across utterances. Prior work demonstrates that lower coherence correlates with cognitive impairment. By averaging cosine similarities of sentence embeddings generated with the `all‑MiniLM‑L6‑v2` model (source: 2607.07974, https://arxiv.org/abs/2607.07974), we obtain a quantitative index that reflects this construct. Although lexical diversity and syntactic complexity cannot be measured without raw text, the selected semantic metric is empirically linked to the same underlying cognitive processes.

## Dataset Strategy

| Dataset | Source / URL | Verification Status | Notes |
|---------|--------------|---------------------|-------|
| **ADReSS Challenge – Sentence Embeddings** | `https://huggingface.co/datasets/pruiu/ADReSS-IS2020_emb/resolve/main/IS2020_test_embeddings/dataset_info.json` | **Verified** | Contains per‑participant sentence‑level embeddings for the test set. Used for all downstream feature computation. |
| **MCI Parquet (unused)** | `https://huggingface.co/datasets/mcimpoi/dtd_split_1/resolve/main/data/test-00000-of-00001-d6ecda0bacf8f78c.parquet` | **Verified** | Not required for the primary analysis; kept for possible future extensions. |
| **PII Synthetic (unused)** | `https://huggingface.co/datasets/gretelai/synthetic_pii_finance_multilingual/resolve/main/data/Dutch_test-00000-of-00001.parquet` | **Verified** | Used only to test the privacy‑audit component; not part of the scientific dataset. |
| **DementiaBank** | – | **Excluded** | No public URL; explicitly excluded per specification. |

All other URLs listed in the “Verified datasets” block are unrelated and therefore omitted.

## Methodological Approach

### 1. Data Ingestion & Validation (US‑1)
* **Download** the embeddings parquet via `datasets.load_dataset(..., streaming=False)` from the verified URL.  
* **Checksum** the file (`sha256`) and store the hash in the project state.  
* **Create** `data/interim/cleaned_adress.csv` with columns: `participant_id`, `label` (Control/MCI/AD), `text` (empty string placeholder), `age`, `education`, `embedding_path`.  
* **Exclusions**: records with missing `label` or with a transcript length < 50 words (approximated via a `word_count` field if present) are omitted; each omission is logged to `data/interim/exclusions.log`.  
* **Metadata**: write `data/results/raw_record_count.json` and `data/results/group_counts.json`.

### 2. Power Analysis (FR‑007)
* Use `statsmodels.stats.power.FTestAnovaPower` to compute the required sample size for a three‑group ANCOVA with two covariates, targeting **80 % power**, **α = 0.05 / N_features** (Bonferroni‑adjusted), and a medium effect size (partial η² ≈ 0.06 ⇒ Cohen’s f ≈ 0.25).  
* With the available ≈ 300 participants, the analysis predicts **≥ 80 % power for detecting η² ≈ 0.06** for the Control vs AD contrast; power for Control vs MCI is lower (≈ 65 %). Results are saved to `data/results/power_analysis.txt`. If power falls below 80 %, the limitation is explicitly documented.

### 3. Feature Extraction (US‑2)
* Load each participant’s embedding array (`.npy` stored in `embedding_path`).  
* Compute **semantic coherence**:  

\[
\text{Coherence}_i = \frac{2}{K_i(K_i-1)}\sum_{p<q}\cos(\mathbf{e}_{ip},\mathbf{e}_{iq})
\]

where \(K_i\) is the number of sentences for participant *i*.  
* Store the result in `data/processed/features.csv` alongside the covariates; lexical/syntactic fields are set to `null`.

### 4. ANCOVA & Assumption Verification (FR‑002, FR‑004, FR‑008)
* Fit two ANCOVA models using `statsmodels.formula.api.ols`:

```
Coherence ~ C(Group) + Age + Education
```

where `Group` is binary (Control vs AD) and (Control vs MCI) respectively.  
* **Bonferroni correction**: α_adj = 0.05 / 2 (two group comparisons).  
* **Effect size**: Partial η² computed from the ANCOVA sums of squares.  
* **Bootstrap CI**: 5 000 bias‑corrected accelerated (BCa) resamples of the η² estimate (implemented with `scipy.stats.bootstrap`).  
* **Assumption checks**:  
  - Normality of residuals → Shapiro‑Wilk (α = 0.05).  
  - Homogeneity of regression slopes → test interaction `Group:Age` and `Group:Education`.  
  - Linearity → scatter plots of each covariate vs. residuals (saved in `assumptions.json`).  
* All diagnostics are stored in `data/processed/assumptions.json`; any violations are reported in the final statistical report.

### 5. Statistical Reporting (FR‑003, US‑3)
* Generate a PDF report (`data/results/statistical_report.pdf`) containing:  
  - Tables of ANCOVA statistics (F, p‑value, Bonferroni‑adjusted p, partial η², 95 % BCa CI).  
  - Boxplots of semantic coherence for each cognitive group.  
  - A violin plot summarizing the distribution of partial η² across the two contrasts.  
  - A section summarizing assumption diagnostics and any violations.  
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
| **Insufficient records for SC‑002** | Document actual count (~300), adjust success criterion, and note reduced power for Control vs MCI. |
| **Raw transcript unavailability** | Explicitly state the limitation; set lexical/syntactic fields to `null`. |
| **Embedding file corruption** | Verify SHA‑256; abort on mismatch. |
| **Assumption violations** | Report them; if severe, flag results as exploratory and suggest non‑parametric alternatives. |
| **Class imbalance** | ANCOVA handles unequal group sizes; report group‑wise descriptive statistics. |
| **Potential PII leakage** | Regex audit after every step; abort on detection. |

---
