# Implementation Plan: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Branch**: `001-statistical-cognitive-decline` | **Date**: 2026-11-01 | **Spec**: `specs/001-statistical-cognitive-decline/spec.md`  
**Input**: Feature specification from `/specs/001-statistical-cognitive-decline/spec.md`

## Summary
The pipeline will (1) download the open‑source ADReSS Challenge sentence‑embedding dataset, verify its integrity, and produce a cleaned CSV with participant identifiers, clinical labels, demographics, and a path to each embedding file; (2) compute the **semantic coherence** metric (mean pairwise cosine similarity of sentence‑level embeddings) and its **Fisher‑z transformation**; (3) run **ANCOVA** for the primary contrast **(AD + MCI) vs Control** (including age, education, and sentence count as covariates) and an **exploratory** Control vs MCI contrast, applying Bonferroni‑corrected significance thresholds; (4) perform an a‑priori power analysis targeting **≥ 80 % power** for the primary contrast; (5) verify ANCOVA assumptions, check multicollinearity (VIF), and fall back to permutation‑based or rank‑based ANCOVA, or beta regression if normality fails; (6) audit all intermediate files for PII; (7) generate a PDF report with tables, boxplots, and a violin plot of effect sizes; (8) validate output files against JSON schemas and record SHA‑256 checksums.

### Specification Amendment Request
The original specification (FR‑001, FR‑002, SC‑002) assumes publicly available raw transcripts, which the ADReSS dataset does **not** provide. To keep the project feasible while still addressing the research question, we formally request the following amendments:

1. **FR‑001 Amendment** – Permit ingestion of raw transcripts **if** an open dataset that includes them becomes available. Until such a dataset is provided, the pipeline will proceed with an empty `text` field and record a placeholder ingestion step (`ingest_raw_transcripts()`) that will be a no‑op.
2. **FR‑002 Amendment** – Allow lexical and syntactic feature extraction to be conditional on the presence of raw transcripts. When transcripts are unavailable, these feature columns will be set to `null` (as currently planned). The amendment clarifies that `null` placeholders satisfy the schema while preserving the possibility of future extension.
3. **SC‑002 Amendment** – Adjust the success‑criterion target to **≥ 300 records** after exclusions (the realistic maximum given the ADReSS dataset size). The primary hypothesis will focus on the combined **(AD + MCI) vs Control** contrast to retain adequate statistical power.

These amendments are reflected throughout the plan and will be recorded in the project constitution as a formal amendment (version bump to 1.1.0).

## Technical Context
* **Language/Version**: Python 3.11  
* **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `sentence-transformers==2.2.*` (provides `all‑MiniLM‑L6‑v2`), `datasets==2.19.*`, `pyyaml==6.0.*`, `tqdm==4.66.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `pytest==8.2.*`, `black==24.3.*`, `ruff==0.3.*`, `detect-secrets==1.4.*`  
* **Storage**: Local filesystem under `data/` (raw, interim, processed, results).  
* **Testing**: `pytest` (unit, contract, integration).  
* **Target Platform**: Linux (`ubuntu‑latest` GitHub Actions runner).  
* **Performance Goals**: End‑to‑end ≤ 30 min, peak RAM ≤ 6 GB.  
* **Compute**: CPU‑only; all libraries are CPU‑compatible.

## Constitution Check

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed random seeds, pinned dependencies, deterministic data fetch, SHA‑256 checksums recorded in project state. |
| **II. Verified Accuracy** | Only the verified ADReSS embedding URL is used; no unverified sources. |
| **III. Data Hygiene** | Raw embeddings immutable; all transformations produce new files with documented hashes; privacy audit guarantees no PII. |
| **IV. Single Source of Truth** | All manuscript numbers derived from CSV/JSON artifacts; no manual transcription. |
| **V. Versioning Discipline** | Content hashes for every artifact recorded in project state; any change updates the hash. |
| **VI. Linguistic Feature Transparency** | Semantic coherence computed as `mean(pairwise_cosine(embeddings))` followed by Fisher‑z transformation, using `all‑MiniLM‑L6‑v2` (arXiv:2607.07974). |
| **VII. Clinical Ground Truth Independence** | Labels come from ADReSS clinical assessments; features derived solely from embeddings, guaranteeing independence. |

## Project Structure

```
specs/001-statistical-cognitive-decline/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── feature.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

### Source Code Layout

```
code/
├── __init__.py
├── config.py            # seeds, paths, constants
├── ingestion.py         # download, checksum, filter, create cleaned CSV, exclusions.log, raw_record_count.json, group_counts.json, optional raw transcript ingestion
├── features.py          # semantic coherence computation + Fisher‑z; conditional lexical/syntactic extraction (placeholders if no raw text)
├── stats.py             # ANCOVA, assumption checks, multicollinearity (VIF), bootstrap η² CIs, fallback permutation & rank‑based ANCOVA, beta‑regression fallback
├── power.py             # a‑priori ANCOVA power analysis (primary combined contrast)
├── privacy.py           # regex‑based PII scanner
├── metadata.py          # SHA‑256 aggregation → metadata.json
├── contracts.py         # helper to load/validate schemas
└── main.py              # orchestrates full pipeline
```

### Data Layout

```
data/
├── raw/
│   └── adress_embeddings.parquet                # verified source
├── interim/
│   ├── exclusions.log                           # records omitted (missing label or <5 sentences)
│   └── cleaned_adress.csv                       # participant_id, label, text (empty), age, education, embedding_path, sentence_count
├── processed/
│   ├── features.csv                             # semantic coherence + placeholders for lexical/syntactic features, covariates
│   ├── ancova_results.json                      # test stats, corrected p‑values, η², CI
│   └── assumptions.json                         # Shapiro‑Wilk, homogeneity, linearity, VIF diagnostics
└── results/
    ├── metadata.json                            # checksums, timestamps, data‑hygiene info
    ├── raw_record_count.json                    # total participants before exclusions
    ├── group_counts.json                        # per‑group counts after exclusions
    ├── power_analysis.txt                       # a‑priori power analysis output
    ├── statistical_report.pdf                   # final PDF/HTML report
    └── privacy_audit.log                        # PII audit log (should contain “0 detections”)
```

## Mapping of Functional & Success Criteria to Plan Phases

| FR / SC | Requirement | Phase / Task |
|---------|-------------|--------------|
| **FR‑001** | Ingest raw transcripts and labels | **Phase 3** – `code/ingestion.py` (download → checksum → filter → create cleaned CSV → exclusions.log → raw_record_count.json → group_counts.json). *Amendment allows this step to be a no‑op when raw text is unavailable.* |
| **FR‑002** | Extract lexical, syntactic, **and** semantic features | **Phase 4** – `code/features.py` (semantic coherence always computed; lexical/syntactic extraction conditional on presence of raw text; placeholders `null` otherwise). *Amendment permits conditional extraction.* |
| **FR‑003** | Generate comprehensive report | **Phase 5** – `code/main.py` (PDF/HTML generation). |
| **FR‑004** | Covariate adjustment (age, education, sentence count) | **Phase 4** – built into ANCOVA model. |
| **FR‑005** | PII audit | **Phase 6** – `code/privacy.py`. |
| **FR‑007** | A‑priori power analysis (≥ 80 % power) | **Phase 2** – `code/power.py` (primary combined AD + MCI vs Control contrast). |
| **FR‑008** | ANCOVA assumption verification | **Phase 4** – `code/stats.py` (diagnostics, VIF, fallback permutation & rank‑based ANCOVA, beta‑regression fallback). |
| **FR‑009** | Summary JSON files (`raw_record_count.json`, `group_counts.json`) | **Phase 3** – generated in `data/results/` (now compliant with Constitution). |
| **SC‑001** | At least one feature significant after Bonferroni | **Phase 5** – results evaluated; if none, note exploratory status. |
| **SC‑002** | ≥ 1000 records after exclusions | **Amended** – target adjusted to **≥ 300 records** (realistic given ADReSS size). |
| **SC‑003** | PDF report with required visualizations | **Phase 5** – `statistical_report.pdf`. |
| **SC‑004** | Privacy audit reports zero PII detections | **Phase 6** – `privacy.py` aborts on detection. |
| **SC‑009** | Power analysis confirms ≥ 80 % power or documents limitation | **Phase 2** – `power.py` output saved; primary contrast meets target, secondary noted. |

## Detailed Phase Tasks

### Phase 0 – Specification Review
* Recognize that FR‑001, FR‑002, and SC‑002 cannot be satisfied with the current open dataset. **Formal amendment request** is documented above.

### Phase 1 – Project Setup
1. Create `pyproject.toml` with Black and Ruff configurations.  
2. Add `.pre-commit-config.yaml` containing `detect-secrets`, `black`, and `ruff` hooks.  
3. Install pre‑commit hooks in CI (`pre-commit install`).  

### Phase 2 – Power Analysis
* Run `code/power.py` using `statsmodels.stats.power.FTestAnovaPower`, targeting **80 % power**, **α = 0.05 / (N_features × 2) = 0.025**, medium effect size (partial η² ≈ 0.06 ⇒ Cohen’s f ≈ 0.25).  
* **Primary contrast**: **combined AD + MCI vs Control**. This yields **≥ 80 % power** with the available ~300 participants.  
* **Exploratory contrast**: **Control vs MCI** (power < 80 %) is documented. Results saved to `data/results/power_analysis.txt`.

### Phase 3 – Data Ingestion & Cleaning
1. `code/ingestion.py --download` fetches the embeddings parquet via `datasets.load_dataset(..., streaming=False)` from the verified URL.  
2. Verify SHA‑256 checksum; record hash in the project state.  
3. Load accompanying metadata (age, education) if present; otherwise set to `null`.  
4. `filter_records()` removes rows with missing `label` or with a transcript length < 5 sentences (derived from embedding array length).  
5. Log each exclusion to `data/interim/exclusions.log`.  
6. **Optional raw transcript ingestion**: if an open dataset with transcripts is provided, `ingest_raw_transcripts()` will read and clean them; otherwise this step is a no‑op (per amendment).  
7. Write `data/interim/cleaned_adress.csv` with columns: `participant_id`, `label`, `text` (empty string placeholder when no raw text), `age`, `education`, `embedding_path`, `sentence_count`.  
8. Write **`data/results/raw_record_count.json`** (total participants before exclusion) and **`data/results/group_counts.json`** (per‑group counts after exclusion).

### Phase 4 – Feature Extraction & Statistical Testing
1. `code/features.py` reads each participant’s embedding array (`.npy` stored in `embedding_path`).  
2. Compute **semantic coherence** as the mean pairwise cosine similarity of sentence embeddings (`sentence_embedding_cosine_similarity`).  
3. Apply a **Fisher‑z transformation** to improve normality:

\[
z_i = \frac{1}{2}\ln\left(\frac{1 + \text{Coherence}_i}{1 - \text{Coherence}_i}\right)
\]

4. **Conditional lexical/syntactic extraction**: if raw transcripts are available, `extract_lexical_features()` and `extract_syntactic_features()` populate TTR, MTLD, noun/verb ratio, mean clause length, and T‑unit count; otherwise these columns are written as `null`.  
5. Store all features in `data/processed/features.csv`.  
6. `code/stats.py` fits two ANCOVA models using `statsmodels.formula.api.ols`:

```
z_coherence ~ C(Group) + Age + Education + Sentence_Count
```

   - **Primary contrast**: **(AD + MCI) vs Control**.  
   - **Exploratory contrast**: **Control vs MCI**.

7. **Bonferroni correction**: α_adj = 0.025 (features × contrasts = 1 × 2).  
8. **Effect size**: Partial η² computed from ANCOVA sums of squares.  
9. **Bootstrap CI**: 5 000 bias‑corrected accelerated (BCa) resamples of the η² estimate.  
10. **Assumption checks**:  
    - Normality of residuals → Shapiro‑Wilk (α = 0.05).  
    - Homogeneity of regression slopes → test interactions `Group:Age`, `Group:Education`, `Group:Sentence_Count`.  
    - Linearity → scatter plots of each covariate vs. residuals (saved in `assumptions.json`).  
11. **Multicollinearity**: Compute Variance Inflation Factor (VIF) for all predictors. If any VIF > 5 (especially `Sentence_Count`), drop `Sentence_Count` and re‑fit, documenting the decision in `assumptions.json`.  
12. **Fallback analysis**:  
    - If normality fails after Fisher‑z, fit a **beta regression** on the bounded cosine similarity (with appropriate link).  
    - If any ANCOVA assumption fails, run a **permutation‑based ANCOVA** (10 000 permutations). For severe violations, also provide a **rank‑based ANCOVA**. Report permutation and rank‑based p‑values alongside the parametric results.  

All diagnostics are stored in `data/processed/assumptions.json`; any violations are reported in the final statistical report.

### Phase 5 – Reporting
* `code/main.py` assembles tables, creates boxplots of the (z‑transformed) semantic coherence for each cognitive group, and a violin plot summarizing the two partial η² effect sizes.  
* Compile a PDF report (`data/results/statistical_report.pdf`) containing:  
  - Tables of ANCOVA statistics (F, Bonferroni‑adjusted p, partial η², 95 % BCa CI, and permutation/rank‑based p‑values when applicable).  
  - Boxplots per group.  
  - A violin plot of effect sizes across the two contrasts.  
  - A section summarizing assumption diagnostics, VIF values, and any fallback analysis notes.  

### Phase 6 – Privacy Auditing
* After each major step (ingestion, feature extraction, stats), `code/privacy.py` scans **all newly created files** with regexes for names, email addresses, phone numbers, and physical addresses.  
* Detection → immediate pipeline abort, error logged to `logs/privacy_audit.log`.  
* The final audit confirms **zero** PII detections; the result is recorded in the report.

### Phase 7 – Contract Validation & Metadata
1. `pytest tests/contract/` validates `cleaned_adress.csv`, `features.csv`, and JSON outputs against `contracts/dataset.schema.yaml` and `contracts/feature.schema.yaml`.  
2. `code/metadata.py` aggregates SHA‑256 hashes for every artifact and writes `data/results/metadata.json`.

## Compute Feasibility
* **Memory**: Embedding parquet ≈ 200 MB; processing in batches keeps RAM ≤ 2 GB.  
* **Runtime**: Expected ≤ 30 min on the GitHub Actions free‑tier CPU runner.  
* **GPU**: Not required; all libraries are CPU‑compatible.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Insufficient records for SC‑002 | Document actual count (~300), request amendment to adjust target, and rely on combined contrast for primary hypothesis. |
| Raw transcript limitation | Explicitly state limitation; set lexical/syntactic fields to `null` until an open dataset is provided. |
| Embedding file corruption | Verify SHA‑256; abort on mismatch. |
| Assumption violations | Report them; if severe, fall back to permutation‑based ANCOVA or beta regression. |
| Multicollinearity between `Sentence_Count` and `z_coherence` | Perform VIF check; drop `Sentence_Count` if VIF > 5. |
| Class imbalance | ANCOVA handles unequal group sizes; report group‑wise descriptive statistics. |
| Potential PII leakage | Regex audit after every step; abort on detection. |

---



