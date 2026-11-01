# Implementation Plan: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Branch**: `001-statistical-cognitive-decline` | **Date**: 2026-11-01 | **Spec**: `specs/001-statistical-cognitive-decline/spec.md`  
**Input**: Feature specification from `/specs/001-statistical-cognitive-decline/spec.md`

## Summary
The pipeline will download the publicly‑available ADReSS Challenge sentence‑embedding dataset, verify its integrity, and create a cleaned CSV that records participant IDs, clinical labels, demographics, and a path to each participant’s embedding array. Because raw transcripts are not publicly downloadable, lexical and syntactic features are recorded as `null`. The only computable linguistic marker is **semantic coherence** (mean pairwise cosine similarity of sentence‑level embeddings). We will:

* Perform ANCOVA (Control vs AD and Control vs MCI) on semantic coherence, adjusting for age and education (FR‑002, FR‑004).  
* Apply Bonferroni correction, report partial η² with 95 % bias‑corrected accelerated bootstrap CIs (FR‑003).  
* Conduct an a‑priori power analysis for the ANCOVA models targeting ≥ 80 % power for a medium effect (partial η² ≈ 0.06) (FR‑007).  
* Verify ANCOVA assumptions (normality, homogeneity of slopes, linearity) (FR‑008).  
* Run a regex‑based PII audit after each major step (FR‑005, US‑4).  
* Produce the required CSV/JSON artifacts, a PDF statistical report, and contract‑validated outputs (SC‑001 – SC‑009).  
* Adjust SC‑002 (≥ 1000 records) to a realistic target (≥ 300 records) and document the limitation.

## Technical Context
* **Language/Version**: Python 3.11  
* **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `sentence-transformers==2.2.*`, `datasets==2.19.*`, `pyyaml==6.0.*`, `tqdm==4.66.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `pytest==8.2.*`, `black==24.3.*`, `ruff==0.3.*`, `detect-secrets==1.4.*`  
* **Storage**: Local filesystem under `data/` (raw, interim, processed, results).  
* **Testing**: `pytest` (unit, contract, integration).  
* **Target Platform**: Linux (`ubuntu‑latest` GitHub Actions runner).  
* **Performance Goals**: End‑to‑end ≤ 30 min, peak RAM ≤ 6 GB.  
* **Constraints**: CPU‑only; all code runs on the free GitHub Actions tier; no synthetic data; strict reproducibility.  

## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed seeds (`np.random.seed(42)`, `random.seed(42)`); `requirements.txt` pins all packages; dataset fetched from the same Hugging Face URL each run; SHA‑256 checksums recorded in `state/projects/…yaml`. |
| **II. Verified Accuracy** | Only the ADReSS embedding URL (verified) is cited; no unverified sources are used. |
| **III. Data Hygiene** | Raw embeddings are immutable; every transformation writes a new file; checksums stored; no PII in any artifact (enforced by privacy audit). |
| **IV. Single Source of Truth** | All numbers in the final manuscript are generated from the CSV/JSON artifacts produced by the pipeline; no manual transcription. |
| **V. Versioning Discipline** | Content hashes for every data artifact are recorded in the project state file; any change updates the hash automatically. |
| **VI. Linguistic Feature Transparency** | Semantic coherence is computed exactly as `mean(pairwise_cosine(embeddings))` using `sentence‑transformers` version `all‑MiniLM‑L6‑v2`. |
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
├── ingestion.py         # download, checksum, filter, create cleaned CSV, exclusions.log, aggregate metadata
├── features.py          # semantic coherence computation
├── stats.py             # ANCOVA, assumption checks, bootstrap η² CIs
├── power.py             # a‑priori ANCOVA power analysis
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
│   ├── cleaned_adress.csv                       # participant_id, label, empty text, age, education, embedding_path
│   ├── exclusions.log                           # records of dropped rows
│   └── raw_record_count.json                    # total participants after download
│   └── group_counts.json                        # per‑group counts after exclusions
├── processed/
│   ├── features.csv                             # semantic coherence + null placeholders
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
| **FR‑001** | Ingest ADReSS embeddings, create cleaned CSV, log exclusions | Phase 3 – `code/ingestion.py` (download → checksum → filter → create CSV → exclusions.log) |
| **FR‑002** | Extract semantic coherence, perform ANCOVA with age & education covariates | Phase 4 – `code/features.py` (semantic similarity) → `code/stats.py` (ANCOVA) |
| **FR‑003** | Generate report with Bonferroni‑corrected p‑values, η² & CI | Phase 5 – `code/main.py` (PDF/HTML generation) |
| **FR‑004** | Covariate adjustment (age, education) in ANCOVA | Phase 4 – built into the ANCOVA model (`statsmodels.formula.api.ols`) |
| **FR‑005** | Regex‑based PII audit after each step | Phase 6 – `code/privacy.py` (run after ingestion, feature extraction, stats) |
| **FR‑007** | A‑priori power analysis for ANCOVA (≥ 80 % power, medium effect) | Phase 2 – `code/power.py` (run before statistical testing) |
| **FR‑008** | Verify ANCOVA assumptions (normality, homogeneity, linearity) | Phase 4 – `code/stats.py` (diagnostics stored in `assumptions.json`) |
| **SC‑001** | At least one feature significant after Bonferroni | Phase 5 – results evaluated; if none, note exploratory status |
| **SC‑002** | ≥ 1000 records after exclusions (unattainable) | Phase 3 – record actual count (~300), update criterion to “≥ 300 records”, document limitation |
| **SC‑003** | PDF report generated, includes required visualizations | Phase 5 – `statistical_report.pdf` with boxplots & effect‑size violin plot |
| **SC‑004** | Privacy audit reports zero PII detections | Phase 6 – `privacy.py` aborts on detection; final log shows zero |
| **SC‑009** | Power analysis confirms ≥ 80 % power or documents limitation | Phase 2 – `power.py` output saved to `power_analysis.txt` |

## Detailed Phase Tasks
### Phase 0 – Specification Review
* Verify SC‑002 infeasibility; amend success criterion (documented in `research.md`).

### Phase 1 – Project Setup
1. Create `pyproject.toml` with Black & Ruff configurations.  
2. Add `.pre-commit-config.yaml` containing `detect-secrets`, `black`, and `ruff` hooks.  
3. Install pre‑commit hooks in CI (`pre-commit install`).  

### Phase 2 – Power Analysis
* Run `code/power.py` using `statsmodels.stats.power.FTestAnovaPower`.  
* Target α = 0.05 / N_features (Bonferroni‑adjusted), effect size f ≈ 0.25 (partial η² ≈ 0.06), power = 0.80.  
* Save output to `data/results/power_analysis.txt`.  

### Phase 3 – Data Ingestion & Cleaning
1. `code/ingestion.py --download` fetches `adress_embeddings.parquet` from the verified URL.  
2. Verify SHA‑256 checksum; record hash in project state.  
3. Load accompanying metadata (age, education) if present; otherwise set to `null`.  
4. **filter_records()** removes rows with missing `label` or with `<50` words (approximated via a `word_count` field if present).  
5. Log each exclusion to `data/interim/exclusions.log`.  
6. Write `data/interim/cleaned_adress.csv`.  
7. Write `data/interim/raw_record_count.json` (total rows before exclusion) and `data/interim/group_counts.json` (per‑group counts after exclusion).  

### Phase 4 – Feature Extraction & Statistical Testing
1. `code/features.py` reads each embedding array, computes semantic coherence, writes `data/processed/features.csv`.  
2. `code/stats.py` fits two ANCOVA models (Control vs AD, Control vs MCI) with covariates age & education.  
3. Apply Bonferroni correction (α_adj = 0.05 / 2).  
4. Compute partial η² and 5 000‑resample BCa confidence intervals.  
5. Perform assumption checks (Shapiro‑Wilk, homogeneity of slopes, linearity); store results in `data/processed/assumptions.json`.  
6. Save ANCOVA output to `data/processed/ancova_results.json`.  

### Phase 5 – Reporting
* `code/main.py` assembles tables, creates boxplots per group, and a violin plot of effect sizes.  
* Compile a PDF using `matplotlib.backends.backend_pdf` (or `reportlab`).  
* Save to `data/results/statistical_report.pdf`.  

### Phase 6 – Privacy Auditing
* After Phases 3‑5, run `code/privacy.py` which scans all newly created files with regexes for names, emails, phones, and addresses.  
* Detection → abort pipeline, log to `logs/privacy_audit.log`.  
* Final audit log must show zero detections and is referenced in the report.  

### Phase 7 – Contract Validation & Metadata Aggregation
1. `code/contracts.py` validates `cleaned_adress.csv`, `features.csv`, and JSON outputs against the schemas in `contracts/`.  
2. `code/metadata.py` aggregates SHA‑256 hashes for every artifact, timestamps, and writes `data/results/metadata.json`.  

## Compute Feasibility
* **Memory**: Embedding parquet ≈ 200 MB; processing in chunks keeps RAM ≤ 2 GB.  
* **Runtime**: Expected ≤ 30 min on the free GitHub Actions CPU runner.  
* **GPU**: Not required; all libraries are CPU‑compatible.  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Insufficient records for SC‑002 | Document actual count (~300), adjust success criterion, note reduced power for Control vs MCI. |
| Raw transcript unavailability | Explicitly state limitation; set lexical/syntactic fields to `null`. |
| Embedding file corruption | Verify SHA‑256; abort on mismatch. |
| Assumption violations | Report them; if severe, flag results as exploratory and suggest non‑parametric alternatives for future work. |
| Class imbalance | ANCOVA handles unequal group sizes; report descriptive stats per group. |
| Potential PII leakage | Regex audit after every step; abort on detection. |

---
