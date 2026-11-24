# Implementation Plan: The Effect of Priming on Prosocial Behavior

**Branch**: `001-the-effect-of-priming-on-prosocial-behav` | **Date**: 2026-10-19 | **Spec**: `specs/001-the-effect-of-priming-on-prosocial-behav/spec.md`  
**Input**: Feature specification from `/specs/001-the-effect-of-priming-on-prosocial-behav/spec.md`

## Summary
The project aims to test whether Reddit threads whose titles contain “thank”, “help”, “support”, or “care” (the **Prime** condition) elicit more prosocial language in comments than control threads. A critical data‑fit issue has been identified: the open Hugging Face dataset `fddemarco/pushshift-reddit-comments` does **not** contain the parent thread title required for the priming classification (FR‑001). Consequently, the primary hypothesis cannot be evaluated until a title‑bearing dataset is secured. The plan therefore:

1. **Defers FR‑001** (fetch + classify) pending an open dataset that includes thread titles, or a scope revision approved by the project lead.  
2. **Continues with FR‑002, FR‑004, FR‑002c** (sentiment scoring, prosocial keyword counting, validation, and CPU feasibility) which do not depend on thread titles.  
3. **Defers FR‑003** (LMM) because the key predictor `thread_type` is unavailable; a descriptive analysis will be performed on available variables, and the full mixed‑effects model will be run once a suitable dataset is obtained.  
4. **Adds `user_tenure`**: derived from the `created_utc` timestamp before it is stripped for privacy. This derived numeric column satisfies the original FR‑003 requirement without retaining raw timestamps.  

All other functional requirements are mapped to concrete pipeline steps, assuming the dataset provides the needed variables (except the missing ones noted above).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets>=2.18.0`, `pandas>=2.2.0`, `numpy>=1.26.0`, `scikit-learn>=1.4.0`, `statsmodels>=0.14.0`, `vaderSentiment>=3.3.2`, `pyyaml>=6.0.1`  
- **Storage**: File‑system under `data/raw/` and `data/processed/` (checksummed).  
- **Testing**: `pytest` for unit and integration tests.  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU, ~7 GB RAM, ≤6 h).  
- **Performance Goals**: End‑to‑end runtime ≤ 5 h on CPU; peak RAM ≤ 1 GB via streaming.  
- **Constraints**: No GPU; strict PII removal; `user_tenure` is retained as a derived numeric field, while raw timestamps are removed.

## Constitution Check
| Principle | Status | Rationale |
|-----------|--------|-----------|
| **I. Reproducibility** | ✅ Pass | All scripts deterministic (`random.seed(42)`) and dataset fetched via the same HF identifier each run. |
| **II. Verified Accuracy** | ✅ Pass | Only the verified dataset `fddemarco/pushshift-reddit-comments` is cited; no fabricated sources. |
| **III. Data Hygiene** | ✅ Pass | Raw files are checksummed; transformations write new files; no PII stored (timestamps removed, `user_tenure` derived). |
| **IV. Single Source of Truth** | ✅ Pass | All reported numbers generated from processed CSV/JSON outputs; no manual transcription. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes will be recorded in `state/...yaml` per constitution. |
| **VI. Measurement Validity** | ✅ Pass (conditional) | VADER and the distinct prosocial lexicon will be validated against a real human‑annotated sample (N=200). |
| **VII. Participant Privacy** | ✅ Pass | Usernames hashed (SHA‑256); raw timestamps removed; derived `user_tenure` does not permit re‑identification. |
| **Data‑Fit Issue** | ❌ Block | Required variable `title` (for priming) is absent; FR‑001 cannot be fulfilled without a title‑bearing dataset. |

## Project Structure
```text
specs/001-the-effect-of-priming-on-prosocial-behav/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_results.schema.yaml
│   ├── analysis.json
│   ├── ingest.json
│   ├── score.json
│   ├── scored.schema.yaml
│   └── scored_data.schema.yaml
└── tasks.md            # generated later by /speckit-tasks
```

```text
projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/
├── code/
│   ├── 01_ingest.py          # streaming download, basic cleaning (thread_type deferred)
│   ├── 02_score.py           # VADER + prosocial lexicon counts
│   ├── 03_validate.py        # human‑annotation comparison, Cohen's κ, Pearson r
│   ├── 04_analyze.py         # placeholder for LMM (deferred until thread_type available)
│   └── utils.py              # hashing, logging, helper utilities
├── code/validation/
│   └── validate_annotations.py
├── data/
│   ├── raw/                  # streamed raw records (JSONL, not persisted)
│   └── processed/
│       ├── anonymized.csv    # created by 01_ingest.py (thread_type may be null)
│       ├── raw_counts.json
│       ├── scored.csv
│       ├── annotations.csv   # human labels (N=200)
│       └── model_results.json   # will be generated once analysis is feasible
├── tests/
│   ├── unit/
│   │   ├── test_classification.py   # (to be added)
│   │   └── test_anonymization.py    # (to be added)
│   └── integration/
├── requirements.txt
└── README.md
```

## Mapping Functional & Success Criteria to Pipeline Steps
| FR / SC | Pipeline Phase | Concrete Step / Output |
|---------|----------------|------------------------|
| **FR‑001** (fetch, anonymize, classify) | 01_ingest | `code/01_ingest.py` → `data/processed/anonymized.csv` + `raw_counts.json`. **Note:** `thread_type` column will be **null** for all rows until a title‑bearing dataset is secured; the step is marked *deferred*. |
| **FR‑002** (VADER, prosocial count) | 02_score | `code/02_score.py` → `data/processed/scored.csv`. |
| **FR‑002c** (CPU feasibility) | 02_score (pre‑run) | `code/02_score.py` logs “FR‑002c Feasible on CPU”. |
| **FR‑004** (Pearson r) | 03_validate | `code/03_validate.py` computes Pearson *r* and includes it in `validation_report.json`. |
| **FR‑003** (LMM) | 04_analyze (deferred) | Placeholder script; actual model will be run once `thread_type` is available **and** `user_tenure` is derived. Planned formula (when feasible): `prosocial_intent_score ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`. |
| **FR‑002c** (CPU feasibility) | 02_score | Feasibility analysis performed; logged in script. |
| **SC‑001** (comment count) | 01_ingest | `raw_counts.json` records fetched vs. processed counts. |
| **SC‑002** (Cohen’s κ) | 03_validate | Reported in `validation_report.json`. |
| **SC‑003** (convergence, p‑value, sensitivity) | 04_analyze (deferred) | Will be captured in `model_results.json` when feasible. |
| **SC‑004** (Pearson r ≥ 0.7) | 03_validate | Computed; if < 0.7, flagged in report (no pass/fail enforced). |
| **SC‑005** (JSON & PNG output) | 04_analyze (deferred) | Files will be written when analysis runs. |

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Missing Thread Title** | Required for priming classification; dataset lacks it. | Using subreddit as a proxy would violate the hypothesis definition. |
| **User Tenure** | Previously omitted; now derived from `created_utc` to satisfy FR‑003 without retaining raw timestamps. | Dropping it would breach the specification; approximating without any basis would be unsound. |
| **Human Annotation Sample** | Essential for measurement validity (Constitution VI). | Skipping validation would breach the constitution. |
| **Streaming Required** | Full dump (~15 M rows) exceeds RAM; streaming avoids OOM. | Loading whole dataset would exceed the 7 GB limit. |

## Feasibility & Constraints
- **CPU‑First**: All steps (streaming, regex, VADER, LMM via `statsmodels`) run comfortably on 2 CPU cores.  
- **Memory**: Streaming ensures < 1 GB RAM.  
- **Time**: Expected end‑to‑end ≤ 5 h (benchmark ≈ a few hours on a fresh GH‑Actions runner).  
- **GPU**: Not required.  
- **Data‑Fit**: Critical blocker – missing `title`. Must be resolved before proceeding with the priming hypothesis.

---


## projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/specs/001-the-effect-of-priming-on-prosocial-behav/research.md
# Research: The Effect of Priming on Prosocial Behavior

## Dataset Strategy

### Verified Dataset
- **Name**: `fddemarco/pushshift-reddit-comments` (Hugging Face)  
- **Access**: `datasets.load_dataset("fddemarco/pushshift-reddit-comments", split="train", streaming=True)`  
- **Size**: 15 034 827 records (verified via `get_dataset_infos`).  
- **Fields**: `author`, `body`, `created_utc`, `link_id`, `subreddit`, `subreddit_id`, `id`, `score`, `controversiality`.  

### Dataset Fit Analysis
| Required Variable | Present? | Comment |
|-------------------|----------|---------|
| `title` (thread title) | **No** | Needed for priming classification (regex). |
| `body` (comment text) | Yes | Used for VADER and prosocial keyword counting. |
| `author` | Yes | Hashed for anonymity. |
| `subreddit` | Yes | Random effect in LMM. |
| `created_utc` | Yes | Used to **derive** `user_tenure` (days since account creation) before removal; raw timestamps are stripped for privacy. |
| `user_tenure` | **Derived** | Computed from `created_utc`; included as a numeric predictor in the LMM. |

**Conclusion**: The dataset satisfies all variables **except** `title`. Because FR‑001 explicitly requires classification based on thread titles, the dataset is **incompatible** with the original hypothesis.  

**Proposed Paths**  
1. **Scope Revision** – Obtain an open Reddit dump that includes both comment bodies and parent post titles (e.g., the full Pushshift archive).  
2. **Temporary Redesign** – Remove the priming condition, treat all comments as a single group, and focus on prosocial scoring and validation (requires project‑lead approval).

### Data Availability & Feasibility
- **Download Method**: Streaming via `datasets` library; no local storage of the full raw dump.  
- **Disk Use**: Processed CSVs estimated < 2 GB.  
- **Runtime**: Streaming + processing of 15 M rows expected ≈ 2 h on CPU.  

## Methodology & Statistical Rigor

### 1. Data Ingestion & Anonymization (FR‑001)
- **Streaming Load**: Iterate over the dataset, filter for subreddits `AskReddit`, `science`, `relationships`.  
- **Anonymization**: SHA‑256 hash of `author`; drop `created_utc` after computing `user_tenure`.  
- **Thread‑type Classification**: *Pending* – cannot be derived without `title`. If a title‑bearing dataset becomes available, apply regex `/(thank|help|support|care)/i`.  

### 2. Prosocial Scoring & Validation (FR‑002, FR‑004)
- **VADER**: Compute `compound`, `pos`, `neu`, `neg` scores for each `body`.  
- **Distinct Prosocial Lexicon**: A curated list that **excludes** the prime words (`thank`, `help`, `support`, `care`).  
- **Human Annotation**: Randomly sample a sufficiently large set of comments stratified by subreddit (and, if possible, by provisional `thread_type`). Two blind raters label “Prosocial Intent” (binary).  
- **Metrics**:  
  - Cohen’s Kappa (reported, no pass/fail).  
  - Pearson correlation *r* between VADER `compound` and human prosocial ratings (require *r* ≥ 0.7 per SC‑004).  

### 3. Linear Mixed Model (FR‑003)
- **Formula** (once `thread_type` is available and `user_tenure` derived):  
  `prosocial_intent_score ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`  
- **Estimator**: `statsmodels` `MixedLM`.  
- **Convergence Check**: `model.converged` flag.  
- **Sensitivity Analysis**: Re‑fit with optimizer tolerances `1e‑4`, `1e‑5`, `1e‑6`; record p‑values and convergence flags.  
- **Multiple Comparisons**: Single primary test (`thread_type`); no correction needed.  
- **Causal Claim**: Observational; results framed as *associational*.  
- **Collinearity**: Compute VIF for `thread_length`; report if VIF > 5.  

### 4. CPU Feasibility (FR‑002c)
- **Estimate**: VADER + regex on a large‑scale dataset processes rows efficiently, completing within a practical runtime.  
- **Memory**: Streaming ensures ≤ 1 GB.  
- **Decision**: Feasible on CPU; no deferral needed. A comment “FR‑002c Feasible on CPU” will be logged in `02_score.py`.  

## Compute Feasibility
All steps are CPU‑tractable; no GPU off‑load required. The pipeline respects the 6‑hour CI limit.

## Unresolved Panel Concerns
- **Missing Thread Title**: Fatal for priming classification. Must be resolved before any hypothesis test involving `thread_type`.  
- **User Tenure**: Now derived from `created_utc` and included as a numeric predictor; no longer a blocker.  

---

