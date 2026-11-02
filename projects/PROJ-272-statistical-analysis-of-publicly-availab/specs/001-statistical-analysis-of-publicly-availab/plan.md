# Implementation Plan: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Branch**: `001-statistical-cognitive-decline` | **Date**: 2026-11-01 | **Spec**: `specs/001-statistical-cognitive-decline/spec.md`  
**Input**: Feature specification from `/specs/001-statistical-cognitive-decline/spec.md`

## Summary
The pipeline will (1) download the publicly‑available ADReSS Challenge sentence‑embedding dataset, verify its integrity, and create a cleaned CSV that records participant IDs, clinical labels, demographics, **sentence count** (derived from the embeddings) and the path to each participant’s embedding array; (2) compute the **semantic coherence** metric (mean pairwise cosine similarity of sentence‑level embeddings) and apply a **Fisher‑z transformation** to address boundedness; (3) run ANCOVA models (Control vs AD, Control vs MCI) for this feature, **including age, education, and sentence count as covariates** (no prior residualization), applying **Bonferroni‑corrected α = 0.05 / (N_features × 2) = 0.025** across the two group contrasts; (4) perform an a‑priori power analysis targeting **≥ 80 % power** to detect a **medium effect size (partial η² ≈ 0.06, corresponding to Cohen’s f ≈ 0.25)** for each feature, with significance level α adjusted for both the number of features **and** the two contrasts; (5) verify ANCOVA assumptions (normality, homogeneity of regression slopes, linearity); if any assumption fails, fall back to a **permutation‑based ANCOVA** (10 000 permutations) and, for severe violations, a **rank‑based ANCOVA**; (6) audit all intermediate files for PII with a regex‑based scanner; (7) generate a PDF report containing tables, boxplots, and a violin plot of effect sizes; (8) validate all output files against JSON schemas and record SHA‑256 checksums in `metadata.json`.  

**Specification Amendment Note** – FR‑001 (raw transcript ingestion) and FR‑002 (lexical & syntactic feature extraction) cannot be satisfied with any currently open dataset because raw transcripts are not publicly available. The plan therefore proceeds with semantic‑coherence only and **requests a formal spec amendment** to relax or replace these requirements. Likewise, SC‑002 (≥ 1000 records) is unattainable with the ADReSS dataset (~300 usable participants); a **spec amendment** to adjust the success criterion is also required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `sentence-transformers==2.2.*` (provides **all‑MiniLM‑L6‑v2**, validated in arXiv:2607.07974), `datasets==2.19.*`, `pyyaml==6.0.*`, `tqdm==4.66.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `pytest==8.2.*`, `black==24.3.*`, `ruff==0.3.*`, `detect-secrets==1.4.*`  
- **Storage**: Local filesystem under `data/` (raw, interim, processed, results).  
- **Testing**: `pytest` (unit, contract, integration).  
- **Target Platform**: Linux (`ubuntu‑latest` GitHub Actions runner).  
- **Performance Goals**: End‑to‑end ≤ 30 min, peak RAM ≤ 6 GB.  
- **Constraints**: CPU‑only; all code must run on the free GitHub Actions tier; no synthetic data.

## Constitution Check

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed seeds (`np.random.seed(42)`, `random.seed(42)`); `requirements.txt` pins all packages; dataset fetched from the same Hugging Face URL each run; SHA‑256 checksums recorded in `state/projects/…yaml`. |
| **II. Verified Accuracy** | Only the ADReSS embedding URL (verified) is cited; no unverified sources used. |
| **III. Data Hygiene** | Raw embeddings are immutable; all transformations write new files; checksums stored; privacy audit guarantees no PII. |
| **IV. Single Source of Truth** | All numbers in the final manuscript are generated from the CSV/JSON artifacts produced by the pipeline; no manual transcription. |
| **V. Versioning Discipline** | Content hashes for every data artifact are recorded in the project state file; any change updates the hash automatically. |
| **VI. Linguistic Feature Transparency** | Semantic coherence is computed exactly as `mean(pairwise_cosine(embeddings))` followed by Fisher‑z transformation, using `all‑MiniLM‑L6‑v2` (arXiv:2607.07974). |
| **VII. Clinical Ground Truth Independence** | Labels come from ADReSS clinical assessments; features are derived solely from embeddings, guaranteeing independence. |

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
├── ingestion.py         # download, checksum, filter, create cleaned CSV, exclusions.log, raw_record_count.json, group_counts.json
├── features.py          # semantic coherence computation + Fisher‑z transform
├── stats.py             # ANCOVA (with age, education, sentence_count), assumption checks, bootstrap η² CIs, fallback permutation & rank‑based ANCOVA
├── power.py             # a‑priori ANCOVA power analysis (corrected α)
├── privacy.py           # regex‑based PII scanner
├── metadata.py          # SHA‑256 aggregation, timestamps → metadata.json
├── contracts.py         # helper to load/validate schemas
└── main.py              # orchestrates full pipeline
```

### Data Layout

```
data/
├── raw/
│   └── adress_embeddings.parquet                # verified source
├── interim/
│   ├── cleaned_adress.csv                       # participant_id, label, text (empty), age, education, embedding_path, sentence_count
│   ├── exclusions.log                           # records omitted (missing label or <5 sentences)
│   ├── raw_record_count.json                    # total participants before exclusions
│   └── group_counts.json                        # per‑group counts after exclusions
├── processed/
│   ├── features.csv                             # z‑transformed semantic coherence + null placeholders for lexical/syntactic features
│   ├── ancova_results.json                      # test stats, corrected p‑values, η², CI
│   └── assumptions.json                         # Shapiro‑Wilk, homogeneity, linearity diagnostics
└── results/
    ├── metadata.json                            # checksums, timestamps, data‑hygiene info
    ├── power_analysis.txt                       # a‑priori power analysis output
    ├── statistical_report.pdf                   # final PDF/HTML report
    └── privacy_audit.log                        # PII audit log (should contain “0 detections”)
```

## Mapping of Functional & Success Criteria to Plan Phases

| FR / SC | Requirement | Phase / Task |
|---------|-------------|--------------|
| **FR‑001** | Ingest raw transcripts and labels | **Phase 3** – `code/ingestion.py` (download → checksum → filter → create CSV → exclusions.log → raw_record_count.json → group_counts.json). *Current open dataset lacks raw text; spec amendment required.* |
| **FR‑002** | Extract lexical, syntactic, **and** semantic features | **Phase 4** – `code/features.py` (semantic coherence only). *Lexical/syntactic extraction omitted pending spec amendment.* |
| **FR‑003** | Generate comprehensive report | **Phase 5** – `code/main.py` (PDF/HTML generation). |
| **FR‑004** | Covariate adjustment (age, education, sentence count) | **Phase 4** – built into ANCOVA model. |
| **FR‑005** | PII audit | **Phase 6** – `code/privacy.py`. |
| **FR‑007** | A‑priori power analysis (≥ 80 % power) | **Phase 2** – `code/power.py` (α corrected for features × 2 contrasts). |
| **FR‑008** | ANCOVA assumption verification | **Phase 4** – `code/stats.py` (diagnostics, fallback permutation & rank‑based ANCOVA). |
| **SC‑001** | At least one feature significant after Bonferroni | **Phase 5** – results evaluated; if none, note exploratory status. |
| **SC‑002** | ≥ 1000 records after exclusions | **UNACHIEVABLE WITH CURRENT OPEN DATA**; flagged for spec amendment. |
| **SC‑003** | PDF report generated with required visualizations | **Phase 5** – `statistical_report.pdf`. |
| **SC‑004** | Privacy audit reports zero PII detections | **Phase 6** – `privacy.py` aborts on detection. |
| **SC‑009** | Power analysis confirms ≥ 80 % power or documents limitation | **Phase 2** – `power.py` output saved; limitation documented if needed. |

## Detailed Phase Tasks

### Phase 0 – Specification Review
* Recognize that FR‑001, FR‑002, and SC‑002 cannot be satisfied with any currently open dataset. Raw transcripts are not publicly available. Flag these for a formal spec amendment (see concerns).  

### Phase 1 – Project Setup
1. Create `pyproject.toml` with Black and Ruff configurations.  
2. Add `.pre-commit-config.yaml` containing `detect-secrets`, `black`, and `ruff` hooks.  
3. Install pre‑commit hooks in CI (`pre-commit install`).  

### Phase 2 – Power Analysis
* Run `code/power.py` using `statsmodels.stats.power.FTestAnovaPower`, targeting **80 % power**, **α = 0.05 / (N_features × 2) = 0.025**, and a medium effect size (partial η² ≈ 0.06 ⇒ Cohen’s f ≈ 0.25).  
* With the available ≈ 300 usable participants, the analysis predicts **≥ 80 % power for the Control vs AD contrast**; power for Control vs MCI falls to [deferred]. Results saved to `data/results/power_analysis.txt`. If power < 80 %, the limitation is explicitly documented.

### Phase 3 – Data Ingestion & Cleaning
1. `code/ingestion.py --download` fetches the ADReSS embeddings parquet from the verified Hugging Face URL.  
2. Verify SHA‑256 checksum; record hash in project state.  
3. Load accompanying metadata (age, education) if present, otherwise set to `null`.  
4. **filter_records()** removes rows with missing `label` or with a transcript length < 5 sentences (derived from embedding array length).  
5. Log each exclusion to `data/interim/exclusions.log`.  
6. Write `data/interim/cleaned_adress.csv` with columns: `participant_id`, `label`, `text` (empty string), `age`, `education`, `embedding_path`, `sentence_count`.  
7. Write `data/interim/raw_record_count.json` (total rows before exclusion) and `data/interim/group_counts.json` (per‑group counts after exclusion).

### Phase 4 – Feature Extraction & Statistical Testing
1. `code/features.py` reads each participant’s embedding array (`.npy`), computes **semantic coherence** as the mean pairwise cosine similarity of sentence embeddings, then applies a **Fisher‑z transformation** to obtain an approximately normal variable.  
2. Store the transformed coherence in `data/processed/features.csv` alongside `null` placeholders for lexical/syntactic features; include `sentence_count` as a covariate for downstream ANCOVA.  
3. `code/stats.py` fits two ANCOVA models (Control vs AD, Control vs MCI) with covariates **Age, Education, Sentence_Count**:

```
z_coherence ~ C(Group) + Age + Education + Sentence_Count
```

4. **Bonferroni correction**: α_adj = 0.025 (features × contrasts = 1 × 2).  
5. Compute partial η² and 5 000‑resample BCa confidence intervals.  
6. **Assumption checks**:  
   - Normality of residuals → Shapiro‑Wilk (α = 0.05).  
   - Homogeneity of regression slopes → test interactions `Group:Age`, `Group:Education`, `Group:Sentence_Count`.  
   - Linearity → scatter plots of each covariate vs. residuals (saved in `assumptions.json`).  
7. **Fallback analysis**: If any assumption fails (e.g., Shapiro‑Wilk p < 0.05 or significant interaction), run a **permutation‑based ANCOVA** (10 000 permutations). For severe violations, also provide a **rank‑based ANCOVA** alternative. Report permutation and rank‑based p‑values alongside parametric results.  

All results saved to `data/processed/ancova_results.json` and diagnostics to `data/processed/assumptions.json`.

### Phase 5 – Reporting
* `code/main.py` assembles tables, creates boxplots of the (z‑transformed) semantic coherence for each cognitive group, and a violin plot summarizing the two partial η² effect sizes.  
* Compile a PDF report (`data/results/statistical_report.pdf`) containing:  
  - Tables of ANCOVA statistics (F, Bonferroni‑adjusted p, partial η², 95 % BCa CI, and permutation/rank‑based p‑values when applicable).  
  - Boxplots per group.  
  - Violin plot of effect sizes.  
  - A section summarizing assumption diagnostics and any fallback analysis notes.  

### Phase 6 – Privacy Auditing
* After Phases 3‑5, run `code/privacy.py` which scans **all newly created files** with regexes for names, email addresses, phone numbers, and physical addresses.  
* Detection → immediate pipeline abort, error logged to `logs/privacy_audit.log`.  
* The final audit confirms **zero** PII detections; this result is referenced in the report.  

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
| Insufficient records for SC‑002 | Document actual count (~300), flag for spec amendment, note reduced power for Control vs MCI. |
| Raw transcript unavailability | Explicitly state the limitation; lexical/syntactic fields set to `null`. |
| Embedding file corruption | Verify SHA‑256; abort on mismatch. |
| Assumption violations | Report them; if severe, fall back to permutation‑based ANCOVA or rank‑based ANCOVA. |
| Class imbalance | ANCOVA handles unequal group sizes; report group‑wise descriptive statistics. |
| Potential PII leakage | Regex audit after every step; abort on detection. |

---


## Constitution Check

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed seeds, version‑pinned dependencies, deterministic data fetch, checksum logging. |
| **II. Verified Accuracy** | Only the verified ADReSS embedding URL is used; no unverified sources. |
| **III. Data Hygiene** | Raw embeddings immutable; all transformations produce new files with recorded hashes; privacy audit guarantees no PII. |
| **IV. Single Source of Truth** | All manuscript numbers derived from CSV/JSON artifacts; no manual transcription. |
| **V. Versioning Discipline** | Content hashes recorded in project state; any change updates the hash. |
| **VI. Linguistic Feature Transparency** | Semantic coherence computed as mean pairwise cosine similarity followed by Fisher‑z transformation, using `all‑MiniLM‑L6‑v2` (arXiv:2607.07974). |
| **VII. Clinical Ground Truth Independence** | Labels from ADReSS clinical assessments; features derived solely from embeddings. |
