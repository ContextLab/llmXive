# Implementation Plan: The Impact of Parasocial Relationships with AI Companions on Loneliness

**Branch**: `001-ai-companion-loneliness-impact` | **Date**: 2026-07-07 | **Spec**: [link to spec]  
**Input**: Feature specification from `/specs/001-ai-companion-loneliness-impact/spec.md`

## Summary
The project must (1) download the Reddit Loneliness Longitudinal Dataset (Zenodo) and Pull AI interaction logs from Pushshift, (2) match users via SHA‑256 hashed usernames, (3) compute weekly usage metrics and attachment‑style proxies, and (4) fit a linear mixed‑effects model with bootstrap‑derived confidence intervals. Success criteria (SC‑001‑SC‑004) guide the quantitative targets. The plan enumerates concrete phases that each address a functional requirement (FR‑001‑FR‑007).

**Critical Note on Data Validity**: This plan assumes the existence of a specific longitudinal dataset on Zenodo containing `username` or `username_hash` fields. If the dataset lacks these linkable identifiers (common in de-identified surveys), the pipeline will halt with a "Data Linkage Impossible" error (Phase 1).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `requests==2.31.*`, `tqdm==4.66.*`, `scikit‑learn==1.4.*`, `statsmodels==0.14.*`, `pyarrow==15.*`, `hashlib` (standard library)  
- **Storage**: CSV/Parquet files under `data/` (raw, intermediate, final)  
- **Testing**: `pytest==8.*` with fixture data; contract validation via `jsonschema`  
- **Target Platform**: Linux runner (GitHub Actions free tier)  
- **Project Type**: Data‑science pipeline / CLI tool  
- **Performance Goals**: Entire pipeline ≤ 6 h on 2‑CPU free‑tier runner; peak RAM ≤ 5 GB  
- **Constraints**: CPU‑only (no GPU), no external large‑model inference, respect API rate limits (≤ 100 req/min)  

## Constitution Check
| Principle | How the Plan Satisfies |
|-----------|------------------------|
| I. Reproducibility | All scripts are deterministic (fixed random seeds), dependencies pinned, data fetched from canonical URLs, and the pipeline can be re‑run end‑to‑end on a fresh runner. |
| II. Verified Accuracy | No external citation is added beyond the URLs listed in the "Verified datasets" block; any required dataset lacking a verified URL is explicitly flagged as a gap. |
| III. Data Hygiene | Raw downloads are stored unchanged; each transformation writes a new file with a checksum recorded in `state/...yaml`. No PII is written; usernames are hashed before any persistence. |
| IV. Single Source of Truth | Every figure/table in the eventual paper will be generated directly from the final CSV/Parquet outputs; no manual transcription is permitted. |
| V. Versioning Discipline | All artifacts (scripts, data files) are content‑hashed; the plan references these hashes via the repository's state file. |
| VI. Longitudinal Analysis Integrity | Random‑effect structure (random intercepts + random slopes) is hard‑coded in the modeling script prior to any data inspection. |
| VII. Self‑Report Instrument Validation | The UCLA Loneliness Scale is documented with its established reliability (α ≈ 0.90). The pipeline explicitly calculates and logs **response completion rates** and missing-data handling procedures before inclusion in analysis. |

## Project Structure
```text
specs/001-ai-companion-loneliness-impact/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── unified_dataset.schema.yaml

src/
├── ingest/
│   ├── download_loneliness.py
│   └── fetch_pushshift.py
├── match/
│   └── user_match.py
├── features/
│   ├── usage_metrics.py
│   └── attachment_proxy.py
├── modeling/
│   ├── mixed_effects.py
│   └── bootstrap_ci.py
└── utils/
    └── logging.py

tests/
├── contract/
│   └── test_unified_schema.py
├── unit/
│   ├── test_download.py
│   └── test_features.py
└── integration/
    └── test_full_pipeline.py
```

## Phase Mapping (FR → Plan Steps)

| Phase | Description | FR(s) Addressed |
|-------|-------------|-----------------|
| **Phase 0 – Setup** | Create virtualenv, install `requirements.txt`; verify checksums of any pre‑downloaded assets. | – |
| **Phase 1 – Data Ingestion & Validation** | `download_loneliness.py` pulls Zenodo DOI. **Crucial Check**: Validates that the dataset contains `username` or `username_hash` fields AND at least 6 months of scores. If linkable IDs are missing, halts with "Data Linkage Impossible". `fetch_pushshift.py` pulls logs for `r/Replika`, `r/characterAI`, `r/AICompanions` covering the exact date span. Implements exponential back‑off (max 3 retries, 60 s timeout). | FR‑001, FR‑002 |
| **Phase 2 – User Matching** | `user_match.py` hashes raw usernames with SHA‑256, joins on hash, drops unmatched rows (FR‑003). Generates `matched_users.parquet`. | FR‑003 |
| **Phase 3 – Feature Engineering** | `usage_metrics.py` aggregates weekly usage frequency and **session duration** (defined as total time span of activity blocks, capped at a duration consistent with operational constraints) per user (FR‑004). `attachment_proxy.py` scans baseline posts with **ECR-RS keyword proxy** (anxiety & avoidance), computes normalized scores, adds `missing_attachment_flag` when no baseline (FR‑004). **Contract Check**: Validates output columns against `contracts/unified_dataset.schema.yaml`. | FR‑004 |
| **Phase 4 – Modeling** | `mixed_effects.py` fits a linear mixed-effects model with random intercepts & random slopes for `UsageFrequency` (statsmodels MixedLM) using **lagged predictors (Usage T -> Loneliness T+1) while controlling for Baseline Loneliness T** (FR‑005). | FR‑005 |
| **Phase 5 – Bootstrap & Robustness** | `bootstrap_ci.py` runs 1 000 **cluster bootstrap** resamples (resampling at User level, seed = 42) to obtain 95 % CIs for all coefficients (FR‑006). Includes diagnostics for normality/homoscedasticity; if violated, bootstrap CIs are used. | FR‑006 |
| **Phase 6 – Subgroup Analysis** | Re‑fit model on subset `age ≥ 60` (excluding missing ages) and compare effect sizes (FR‑007). | FR‑007 |
| **Phase 7 – Validation & Reporting** | Compute match rate (SC‑001), marginal R² gain (SC‑002), significance check via bootstrap CIs (SC‑003), and log total runtime (SC‑004). **Gate**: If match rate < 80% OR N < 500, halt with "Power Insufficient" error. Export `model_results.csv` and a concise HTML report. | SC‑001‑SC‑004 |

All phases are ordered to respect data dependencies (download → match → features → model → validation).

---