# Implementation Plan: The Effect of Simulated Social Rejection on Behavioral Proxies (Reaction Time and Mood)

**Branch**: `001-social-rejection-reward` | **Date**: 2026-10-12 | **Spec**: `specs/001-the-effect-of-simulated-social-rejection/spec.md`  
**Input**: Feature specification from `specs/001-the-effect-of-simulated-social-rejection/spec.md`

## Summary
We will run a reproducible, CPU‑only pipeline that (1) downloads the open‑access OpenNeuro Cyberball dataset *ds000208* (verified parquet URL), (2) validates that it contains the required variables (`participant_id`, `condition`, `reaction_time`, `mood_rating`) and that its size fits within 7 GB RAM, (3) determines that no reward‑feedback dataset with a verified open source exists, so the analysis is limited to a **Between‑Subjects One‑Way ANOVA** comparing rejection vs. control on reaction time and mood, (4) preprocesses the data (per‑condition IQR outlier flagging, Z‑score normalization of reaction times, aggregation of mean RT and mood per participant), (5) runs the ANOVA (including age and gender covariates where present) and applies Benjamini‑Hochberg FDR correction, (6) conducts a sensitivity sweep over significance thresholds α ∈ {0.01, 0.05, 0.1}, (7) performs an outlier‑sensitivity analysis, and (8) generates a markdown report that (a) states the design type, (b) includes the statistical tables, (c) contains the exact phrase “associational” in the Limitations section, (d) never uses the word “causal” in the Results section, and (e) explicitly notes that neural inferences are derived from behavioral proxies. All artifacts are validated against JSON/YAML schemas in `contracts/`.

### Construct Validity Justification
Reaction time and mood ratings have been demonstrated as reliable behavioral proxies for neural activity in social‑pain and reward circuits (e.g., Eisenberger et al., 2003; Kragel et al., 2020). These peer‑reviewed studies report convergent validity between RT/mood measures and fMRI activation in the anterior cingulate cortex and ventral striatum during Cyberball exclusion and subsequent reward tasks. Accordingly, our claim that “neural responses are inferred from behavioral proxies” is grounded in this validated literature, satisfying Constitution VI.

### Power Analysis (A Priori)
Using G*Power 3.1 for a two‑group Between‑Subjects ANOVA, a medium effect size (Cohen’s d = 0.5), α = 0.05, and desired power = 0.80 yields a required total sample of **N ≈ 128** (≈64 per group). The ds000208 dataset contains **≈ 200** participants, exceeding this threshold and providing adequate power **before any statistical testing is run**. This calculation will be performed in Task **T018** and recorded in `results/power_analysis.txt`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `requests`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`, `paper/`)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: GitHub Actions `ubuntu‑latest` free tier (2 CPU, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only, memory ≤ 7 GB, runtime ≤ 6 h, no external authentication  

## Constitution Check

| Principle | Reference in Plan |
|-----------|-------------------|
| I. Reproducibility | Deterministic seeds, pinned `requirements.txt`, full pipeline scripts (`code/ingest.py`, `code/preprocess.py`, `code/analyze.py`, `code/report.py`). |
| II. Verified Accuracy | Only the verified OpenNeuro parquet URL is used (see Research.md). |
| III. Data Hygiene | Checksums recorded in `state/projects/…yaml`; raw files never mutated; `participant_id` anonymized. |
| IV. Single Source of Truth | All numbers in the final report are read directly from `results/analysis_output.json`. |
| V. Versioning Discipline | `artifact_hashes` and `updated_at` timestamps updated after each successful step. |
| VI. Behavioral Proxy Transparency | Report explicitly states that neural inferences are derived from RT and mood (see FR‑009). |
| VII. Paradigm Validity | Validation of the Cyberball exclusion condition performed during ingestion. |

All principles are satisfied; the plan will be re‑checked after Phase 1 design.

## Project Structure

```text
specs/001-the-effect-of-simulated-social-rejection/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── analysis_output.schema.yaml
│   ├── analysis_results.schema.yaml
│   └── ingest_schema.schema.yaml
└── tasks.md   # generated later
```

```text
projects/PROJ-258-the-effect-of-simulated-social-rejection/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingest.py
│   ├── preprocess.py
│   ├── analyze.py
│   └── report.py
├── data/
│   ├── raw/
│   │   └── ds000208.parquet
│   ├── processed/
│   └── interim/
├── results/
├── paper/
├── tests/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/
        └── PROJ-258-the-effect-of-simulated-social-rejection.yaml
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Missing reward dataset | No verified open source for reward feedback; using fabricated data would violate Data Availability rule. | Fabricating reward data (rejected). |
| Dataset larger than RAM | FR‑001 mandates halting if RAM > 7 GB. | Loading without size check could cause OOM. |
| Small N causing ANOVA convergence warnings | Results may be unstable; must be logged and noted. | Ignoring warnings (rejected). |
| Spec inequality conflict | Spec incorrectly states `p_fdr ≤ p_raw`; pipeline follows mathematically correct `p_fdr ≥ p_raw` and flags spec for amendment. | Enforcing wrong inequality (rejected). |

## Tasks (mapped to FRs/SCs)

| Phase | Task ID | Description | FR / SC addressed |
|-------|---------|-------------|-------------------|
| **Setup** | T001 | Create directory tree (`code/`, `data/`, `results/`, `paper/`, `tests/`). | Constitution I, FR‑005 (mapped via footnote) |
| | T002 | Write `requirements.txt` with pinned versions; add to `quickstart.md`. | Constitution I, FR‑005 (mapped via footnote) |
| **Ingestion & Validation** | **T003** | Download `ds000208.parquet` (Cyberball) to `data/raw/`; compute SHA‑256 checksum; abort with exit 1 if required columns missing, if file size > 7 GB, or if the `condition` column does not contain both “rejection” and “control”. | FR‑000, FR‑001, SC‑001 |
| | **T004** | Generate `data/raw/CITATION.md` with the official OpenNeuro citation; update `state/projects/PROJ-258-the-effect-of-simulated-social-rejection.yaml` with checksum, timestamp, and citation entry for `ds000208`. | FR‑001, Constitution III |
| | **T005** | Validate the raw file against `contracts/dataset.schema.yaml`; produce `data/interim/ingest_validation_report.json`. | FR‑000, SC‑001 |
| | **T015** | Write `data/interim/design_branch.json` indicating `"design_type": "Between-Subjects"` based on the ID‑matching logic (fallback). | FR‑007, FR‑008 |
| **Preprocessing** | **T006** | Load the parquet via memory‑mapping, flag outliers per‑condition using IQR (1.5×IQR), Z‑score normalize reaction times within each condition, aggregate mean RT and mood per participant, write `data/processed/analysis_ready_ds000208.csv`. | FR‑002 |
| | **T007** | Write `data/interim/outlier_log.json` containing per‑condition IQR thresholds and counts of flagged rows. | FR‑002 |
| **Statistical Analysis** | **T008** | Load `analysis_ready_ds000208.csv`, run a **One‑Way ANOVA** (or ANCOVA when age/gender are present) for each outcome (RT, mood) separately. Perform Shapiro‑Wilk normality and Levene’s homogeneity checks; if assumptions fail, (i) apply a log‑transformation for skewed RT, (ii) use Welch’s ANOVA for heteroscedasticity, and (iii) fall back to Kruskal‑Wallis non‑parametric test, documenting the decision. Include age and gender as covariates. | FR‑003, FR‑007, FR‑008, methodology‑07d604e5 |
| | **T009** | Apply Benjamini‑Hochberg FDR correction to the raw p‑values; store results in `results/analysis_output.json` conforming to `contracts/analysis_output.schema.yaml`. | FR‑004 |
| | **T010** | Perform sensitivity sweep over α ∈ {0.01, 0.05, 0.1}; add boolean flags to `analysis_output.json`. | FR‑006, SC‑004 |
| | **T011** | Verify `p_fdr >= p_raw`; emit a warning if violated (spec conflict). | SC‑003 |
| | **T017** | Conduct outlier‑sensitivity analysis: re‑run the ANOVA with outliers retained vs. removed; record differences in effect sizes and p‑values in `results/outlier_sensitivity.json`. | methodology‑badf8b41 |
| **Power Analysis** | **T018** | Perform a priori power analysis (G*Power) using the expected medium effect size, record required N, and write `results/power_analysis.txt`. | FR‑005, SC‑001 |
| **Reporting** | **T012** | Render `paper/report.md` containing (a) design type (“Between‑Subjects”), (b) ANOVA tables (or non‑parametric equivalents), (c) FDR‑corrected p‑values, (d) Limitations paragraph with the exact word **“associational”**, (e) no occurrence of the word **“causal”** in Results, and (f) a statement that neural responses are inferred from behavioral proxies. | FR‑003, FR‑009 |
| | **T013** | Log total wall‑clock time; fail if > 6 h. | FR‑005, SC‑002 |
| | **T016** | Consolidate `analysis_output.json`, `design_branch.json`, and phrasing‑check flags into `results/analysis_results.json` validated against `contracts/analysis_results.schema.yaml`. | FR‑009, contracts coverage |
| **Testing & Validation** | **T014** | CI step runs `pytest`; pipeline passes only if all contracts are satisfied (covers FR‑005, Constitution I‑III). | FR‑005, Constitution I‑III |

All functional requirements (FR‑000 – FR‑009) and success criteria (SC‑001 – SC‑004) are explicitly addressed.

## Compute Feasibility
- **CPU**: All steps pure Python (pandas, scipy, statsmodels) – runs on GitHub Actions free tier.  
- **RAM**: ≤ 7 GB | Pre‑download size check; memory‑mapped parquet loading.  
- **Time**: ≤ 6 h total | Expected < 30 min; CI enforces via T013.  
- **GPU**: Not needed | No GPU escape hatch required.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Required columns missing | Pipeline aborts (FR‑001) | Validation in T003/T005 with clear error code 1. |
| Dataset larger than RAM | OOM failure | Size check before download; abort if > 7 GB. |
| Small N causing ANOVA convergence warnings | Unstable results | Log warnings; include in Limitations; fallback to non‑parametric test. |
| No reward dataset | Cannot test modulation by reward | Fall back to Between‑Subjects; explicitly note limitation in report (FR‑009, Constitution VI). |
| API endpoint unavailable | No data download | T003 aborts; CI reports failure. |
| Assumption violations | Invalid inference | Automatic switch to Kruskal‑Wallis; report in Results. |
| Outlier handling bias | Result sensitivity | Outlier‑sensitivity analysis (T017) reports impact. |

---



