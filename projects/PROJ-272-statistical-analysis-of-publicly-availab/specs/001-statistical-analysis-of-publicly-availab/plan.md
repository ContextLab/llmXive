# Implementation Plan: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Branch**: `001-statistical-cognitive-decline` | **Date**: 2026-10-24 | **Spec**: `specs/001-statistical-cognitive-decline/spec.md`  
**Input**: Feature specification from `/specs/001-statistical-cognitive-decline/spec.md`

## Summary
The pipeline will ingest the publicly‑available ADReSS Challenge embeddings (verified Hugging Face URL). Because raw transcripts are not publicly downloadable, lexical and syntactic markers cannot be computed; instead we will use **semantic coherence** (mean pairwise cosine similarity of sentence‑level embeddings) as the primary linguistic marker. The analysis will:

* Perform ANCOVA (Control vs AD and Control vs MCI) on the semantic coherence metric, adjusting for age and education (FR‑002, FR‑004).  
* Apply Bonferroni correction and report partial η² with 95 % bias‑corrected accelerated bootstrap CIs (FR‑003).  
* Conduct an a‑priori power analysis for the ANCOVA models targeting ≥ 80 % power for a medium effect (partial η² ≈ 0.06) (FR‑007).  
* Run a full privacy audit after each processing step (FR‑005, US‑4).  
* Produce the required CSV/JSON artifacts, a PDF statistical report, and all contract‑validated outputs (SC‑001 – SC‑009).

Where the specification cannot be satisfied (e.g., SC‑002’s “≥ 1000 records after exclusions”), the limitation is documented and the success criterion is re‑framed as “report the actual record count and note the power limitation” (see Research).

## Technical Context
* **Language/Version**: Python 3.11  
* **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `sentence-transformers==2.2.*`, `pyyaml==6.0.*`, `tqdm==4.66.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `pytest==8.2.*`, `black==24.3.*`, `ruff==0.3.*`, `detect-secrets==1.4.*`  
* **Storage**: Local filesystem under `data/` (raw, interim, processed, results).  
* **Testing**: `pytest` (unit, contract, integration).  
* **Target Platform**: Linux (`ubuntu‑latest` GitHub Actions runner).  
* **Performance Goals**: End‑to‑end ≤ 30 min, peak RAM ≤ 6 GB.  
* **Constraints**: CPU‑only; all code runs on the free GitHub Actions tier; no synthetic data; strict reproducibility.  

## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed seeds (`np.random.seed(42)`, `random.seed(42)`), `requirements.txt` pins all packages, dataset fetched from the same Hugging Face URL each run, SHA‑256 checksums recorded in `state/projects/…yaml`. |
| **II. Verified Accuracy** | Only the ADReSS embeddings URL (verified) is cited; no unverified sources. |
| **III. Data Hygiene** | Raw embeddings are immutable; every transformation writes a new file; checksums stored; no PII in any artifact. |
| **IV. Single Source of Truth** | All numbers in the eventual manuscript are generated from the JSON/CSV artifacts produced by the pipeline; no manual transcription. |
| **V. Versioning Discipline** | Content hashes for every data artifact are recorded in the project state file; any change updates the hash automatically. |
| **VI. Linguistic Feature Transparency** | Semantic coherence is computed exactly as `mean(pairwise_cosine(embeddings))` using `sentence-transformers` version `all-MiniLM-L6-v2`. |
| **VII. Clinical Ground Truth Independence** | Labels come from ADReSS clinical assessments; features are derived solely from embeddings, guaranteeing independence. |
| **VIII. FR‑001 Limitation** | Raw transcripts are unavailable; the plan proceeds with embeddings as a proxy and explicitly documents this limitation. |
| **IX. SC‑002 Feasibility** | The ADReSS dataset yields ≈ 300 usable records after exclusions (well below 1 000). The plan records the actual count, updates SC‑002 to “≥ 300 records after exclusions”, and notes the power limitation in the report. |

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
├── ingestion.py         # download, checksum, create cleaned CSV, exclusion log
├── features.py          # semantic coherence computation
├── stats.py             # ANCOVA, assumption checks, bootstrap η² CIs
├── power.py             # a‑priori ANCOVA power analysis (F‑test)
├── modeling.py          # logistic regression / random forest with covariates (optional)
├── privacy.py           # regex‑based PII scanner
├── metadata.py          # aggregate checksums, timestamps → metadata.json
├── contracts.py         # helper to load/validate schemas
└── main.py              # orchestrates full pipeline
```

### Data Layout
```
data/
├── raw/
│   └── adress_embeddings.parquet                # verified source
├── interim/
│   ├── cleaned_adress.csv                       # participant_id, label, text (empty), age, education, embedding_path
│   └── exclusions.log                           # records of dropped rows
├── processed/
│   ├── features.csv                             # semantic similarity + null placeholders
│   ├── ancova_results.json                      # test stats, corrected p‑values, η², CI
│   ├── assumptions.json                         # Shapiro‑Wilk, homogeneity, linearity diagnostics
│   └── model_results.json (optional)
└── results/
    ├── raw_record_count.json                    # total participants after download
    ├── group_counts.json                        # per‑group counts after exclusions
    ├── metadata.json                            # checksums, timestamps, data‑hygiene info
    └── statistical_report.pdf                   # final PDF/HTML report
```

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Requirement | Phase / Task |
|---------|-------------|--------------|
| **FR‑001** | Ingest ADReSS embeddings, create cleaned CSV, log exclusions | Phase 3 – `code/ingestion.py` (download → checksum → create CSV → exclusions.log) |
| **FR‑002** | Extract semantic coherence, perform ANCOVA with age & education covariates | Phase 4 – `code/features.py` (semantic similarity) → `code/stats.py` (ANCOVA) |
| **FR‑003** | Generate report with Bonferroni‑corrected p‑values, η² & CI | Phase 5 – `code/stats.py` (bootstrap CI) → `code/main.py` (PDF/HTML generation) |
| **FR‑004** | Covariate adjustment (age, education) in ANCOVA | Phase 4 – built into the ANCOVA model (`statsmodels.formula.api.ols`) |
| **FR‑005** | Regex‑based PII audit after each step | Phase 6 – `code/privacy.py` (run after ingestion, feature extraction, stats) |
| **FR‑007** | A‑priori power analysis for ANCOVA (≥ 80 % power, medium effect) | Phase 2 – `code/power.py` (run before statistical testing) |
| **FR‑008** | Verify ANCOVA assumptions (normality, homogeneity, linearity) | Phase 4 – `code/stats.py` (diagnostics stored in `assumptions.json`) |
| **SC‑001** | At least one feature significant after Bonferroni | Phase 5 – results evaluated; if none, note exploratory status |
| **SC‑002** | ≥ 1000 records after exclusions (unattainable) | Phase 3 – record actual count; update success criterion to “≥ 300 records” and document limitation |
| **SC‑003** | PDF report generated, includes required visualizations | Phase 5 – `statistical_report.pdf` with boxplots & effect‑size violin plot |
| **SC‑004** | Privacy audit reports zero PII detections | Phase 6 – `privacy.py` aborts on detection; final audit log stored |
| **SC‑009** | Power analysis confirms ≥ 80 % power or documents limitation | Phase 2 – `power.py` output saved to `data/results/power_analysis.txt` |

## Detailed Phase Tasks
### Phase 0 – Specification Review
* Verify that SC‑002 is infeasible; amend the success criterion (documented in research.md).

### Phase 1 – Project Setup
1. Create `pyproject.toml` with Black & Ruff config.  
2. Add `.pre-commit-config.yaml` (detect‑secrets, black, ruff).  
3. Install pre‑commit hooks in CI (`pre-commit install`).  

### Phase 2 – Power Analysis
* Run `code/power.py` using `statsmodels.stats.power.FTestAnovaPower`.  
* Target α = 0.05 / N_features (Bonferroni‑adjusted).  
* Output → `data/results/power_analysis.txt`.

### Phase 3 – Data Ingestion & Cleaning
1. `code/ingestion.py --download` fetches `adress_embeddings.parquet` from the verified URL.  
2. Verify SHA‑256 checksum (recorded in `state/projects/...yaml`).  
3. Load accompanying metadata CSV (age, education) if present; otherwise set to `null`.  
4. Apply exclusion rules (missing label, < 50 words – approximated via `word_count` field if available; otherwise skip).  
5. Write `data/interim/cleaned_adress.csv` and `data/interim/exclusions.log`.  
6. Write `data/results/raw_record_count.json` and `data/results/group_counts.json`.

### Phase 4 – Feature Extraction & Statistical Testing
1. `code/features.py` reads each embedding array, computes mean pairwise cosine similarity → `sentence_embedding_cosine_similarity`.  
2. Merge with cleaned CSV → `data/processed/features.csv`.  
3. `code/stats.py` fits two ANCOVA models (Control vs AD, Control vs MCI) with covariates age & education.  
4. Perform Bonferroni correction (α = 0.05 / 2).  
5. Compute partial η² for each model; generate 5 000‑resample bias‑corrected accelerated bootstrap CIs.  
6. Verify assumptions: Shapiro‑Wilk on residuals, Levene’s test for homogeneity of slopes, scatter plots for linearity (saved in `assumptions.json`).  
7. Save results → `data/processed/ancova_results.json`.

### Phase 5 – Reporting
1. `code/main.py` assembles tables, creates boxplots for semantic similarity per group, and a violin plot of effect sizes.  
2. Compile a PDF (via `matplotlib.backends.backend_pdf` or `reportlab`).  
3. Save to `data/results/statistical_report.pdf`.

### Phase 6 – Privacy Auditing
* After each of Phases 3‑5, run `code/privacy.py` which scans all newly created files with regexes for names, emails, phones, addresses.  
* If any match → abort pipeline, log to `logs/privacy_audit.log`.  
* Final audit log stored alongside the report.

### Phase 7 – Contract Validation & Metadata Aggregation
1. `code/contracts.py` validates `cleaned_adress.csv`, `features.csv`, and JSON results against the schemas in `contracts/`.  
2. `code/metadata.py` aggregates SHA‑256 checksums, timestamps, and writes `data/results/metadata.json`.  

## Compute Feasibility
* **Memory**: Embedding parquet ≈ 200 MB; processing in chunks ≤ 1 GB.  
* **Runtime**: Expected ≤ 30 min on the free GitHub Actions CPU runner.  
* **GPU**: Not required; all libraries run on CPU.  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Raw transcripts unavailable → lexical/syntactic features missing | Explicitly document omission; focus on semantic coherence; set missing fields to `null`. |
| Sample size < 1000 (SC‑002) | Record actual count, adjust success criterion, and note reduced power in the report. |
| Embedding file corrupted or checksum mismatch | Abort pipeline with clear error; checksum stored in project state. |
| Class imbalance | Use ANCOVA which handles unequal group sizes; report group‑wise descriptive stats. |
| Insufficient power for Control vs MCI | Power analysis will flag; findings labeled exploratory. |
| Potential PII leakage | Regex‑based audit after every step; abort on detection. |
| Assumption violations (e.g., non‑normal residuals) | Report violations; if severe, note that ANCOVA results are tentative and consider non‑parametric alternatives in future work. |

---
