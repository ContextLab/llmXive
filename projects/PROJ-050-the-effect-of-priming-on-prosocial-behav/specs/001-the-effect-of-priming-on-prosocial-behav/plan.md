# Implementation Plan: The Effect of Priming on Prosocial Behavior in Online Communities

**Branch**: `001-the-effect-of-priming-on-prosocial-behav` | **Date**: 2026-06-25  
**Spec**: `specs/001-the-effect-of-priming-on-prosocial-behav/spec.md`

## Summary

This project implements an observational study to quantify the correlation between prosocial priming cues in Reddit thread titles and the frequency of prosocial action verbs in subsequent comments. The technical approach involves: (1) Ingesting and filtering a **verified multi‑subreddit Reddit dataset**; (2) Classifying threads into “Prime” (containing non‑negated keywords: “help”, “support”, “charity”) and “Control” groups; (3) Anonymizing PII via SHA‑256 hashing; (4) Computing `prosocial_action_count` and VADER sentiment scores using CPU‑only NLP libraries; (5) Validating metrics against a **human‑generated gold standard**; and (6) Fitting a Linear Mixed‑Effects Model (LMM) to test the hypothesis while controlling for thread age and comment count.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `nltk`, `vaderSentiment`, `statsmodels`, `scikit-learn`, `matplotlib`, `pyyaml`  
**Storage**: Local `data/` directory (Parquet/CSV), `code/` for scripts, `contracts/` for schemas.  
**Testing**: `pytest` (unit tests for classification logic, integration tests for pipeline).  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU‑only, 2 cores, 7 GB RAM).  
**Performance Goals**: Full pipeline (10 k comments) < 4 h; Memory < 7 GB.  
**Constraints**: No GPU; all listed dependencies have CPU‑only wheels.

## Constitution Check

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. Dataset sources fixed to verified URLs. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs cited are from the verified block. No hallucinated sources. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`. Derivations in `data/processed/`. Checksums recorded. |
| **IV. Single Source of Truth** | **PASS** | All stats in `paper/` trace to `data/processed/analysis_results.json`. |
| **V. Versioning Discipline** | **PASS** | After each artifact is written, its SHA‑256 checksum is computed and the central state file `state/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav.yaml` is updated with the new hash, ensuring traceability. |
| **VI. Measurement Validity** | **PASS** | FR‑010/FR‑011 mandate human annotation validation (Cohen’s Kappa ≥ 0.7). VADER and lexicon validated on stratified sample. |
| **VII. Participant Privacy** | **PASS** | FR mandates SHA‑256 hashing of usernames and stripping timestamps before storage. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-effect-of-priming-on-prosocial-behav/
├── plan.md               # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest.py          # Data retrieval, filtering, anonymization
│   ├── 02_classify.py        # Prime/Control logic, negation handling
│   ├── 03_score.py           # VADER + Prosocial Lexicon scoring
│   ├── 04_validate.py        # Human annotation validation (Cohen's Kappa)
│   ├── 05_analyze.py         # LMM fitting, sensitivity analysis, plotting
│   └── utils/
│       ├── constants.py      # Keywords, subreddits, seeds
│       └── anonymize.py      # SHA‑256 hashing
├── data/
│   ├── raw/                  # Downloaded parquet (checksummed)
│   ├── processed/            # Anonymized, classified, scored data
│   └── validation/           # Human annotation gold standard
├── contracts/                # (Symlinked or copied from specs)
└── tests/
    ├── test_classification.py
    └── test_anonymization.py
```

**Structure Decision**: Single‑project structure; sequential pipeline stages fit the `code/` pattern for computational projects. No web/mobile components required.

## Phase Plan (Computational Task Ordering)

1. **Phase 0: Research & Validation Strategy**  
   * Confirm dataset availability for the 5 target subreddits.  
   * Define the “Prosocial Action Lexicon” (excluding prime keywords).  
   * Draft the Human Annotation Protocol (codebook, rater recruitment, annotation format).  

2. **Phase 1: Data Ingestion & Anonymization (FR‑001, FR‑001a, FR‑009)**  
   * Download the **primary verified multi‑subreddit source** `pushshift/reddit` from HuggingFace.  
   * **Verify** that **all five** target subreddits are present. If any are missing, **attempt** to load the **fallback dataset** `pushshift/reddit` (same source but refreshed). If the fallback also lacks required subreddits, **abort with a clear error** (fulfills FR‑001a).  
   * Filter by the target subreddits.  
   * Compute `thread_age` **before** stripping timestamps (difference between comment timestamp and thread start, expressed in hours). Store the derived column.  
   * Hash usernames with SHA‑256, truncate to 16 characters for `user_id`.  
   * Remove plaintext timestamps and usernames.  
   * Save `data/processed/raw_anonymized.parquet`.  

3. **Phase 2: Classification (FR‑002, FR‑002a)**  
   * Apply keyword logic with NLTK word tokenization, excluding titles where a negation word (`no`, `not`, `never`, `without`) appears within three tokens before a keyword.  
   * Label `thread_type` as “Prime” or “Control”.  
   * Log any “Negation Exclusions”.  
   * Save `data/processed/classified.parquet`.  

4. **Phase 3: Scoring (FR‑003, FR‑003b, FR‑012)**  
   * Compute VADER sentiment scores (`compound`, `pos`, `neu`, `neg`).  
   * Define `neg_score` as the VADER `neg` component (0‑1).  
   * Compute `prosocial_action_count` using the secondary lexicon of action verbs (e.g., “offer”, “give”, “assist”, “contribute”) **excluding** the prime keywords and their semantic equivalents.  
   * Ensure CPU‑only execution; runtime monitored to stay < 4 h for TARGET_N = 10 000 comments.  
   * Save `data/processed/scored.parquet`.  

5. **Phase 4: Validation (FR‑010, FR‑011)**  
   * **Human Annotation Protocol** (no simulation):  
     1. Recruit **at least three independent raters**.  
     2. Provide a **codebook** defining “prosocial action” (action‑verb list) and “negative sentiment” (VADER neg interpretation).  
     3. Perform **stratified random sampling** by the cross‑product of `thread_type` and `subreddit` with a **minimum of 50 samples per stratum**. If a stratum has < 50, merge with the most similar subreddit until the threshold is met.  
   * Raters annotate the sampled comments; their labels are compiled into `data/validation/gold_standard.csv` which must contain a `human_raters` metadata field listing the rater IDs.  
   * `04_validate.py` loads this file, computes Cohen’s Kappa for both the prosocial lexicon and VADER negativity against the human labels, and **aborts** if Kappa < 0.7 (SC‑006). No simulated or rule‑based gold standard is used.  

6. **Phase 5: Analysis (FR‑004, FR‑005, FR‑005a, SC‑001, SC‑002)**  
   * Fit a **base** Linear Mixed‑Effects Model using `statsmodels`:

     ```python
     model_base = smf.mixedlm(
         "prosocial_action_count ~ thread_type + thread_age + comment_count",
         data=df,
         groups=df["thread_id"]
     ).fit()
     ```

   * **Diagnostic**: Examine the variance component for `user_id`.  
     - If the variance is **positive**, `user_id` appears in both Prime and Control groups, and the model converges, fit a **second model** adding `(1|user_id)`.  
     - If the variance is zero, non‑identifiable, or `user_id` never appears across both conditions, **omit** the `user_id` random effect, log a warning, and retain `model_base`.  
   * Perform sensitivity analysis reporting significance at thresholds p < 0.01, p < 0.05, p < 0.10.  
   * Generate a boxplot PNG comparing `prosocial_action_count` distributions across `thread_type`.  
   * Output `results/analysis_results.json` and `results/boxplot.png`.  

7. **Phase 6: Reporting (FR‑006, SC‑003, SC‑004, SC‑005, SC‑007, SC‑008)**  
   * Verify total runtime < 4 h (SC‑004).  
   * Run a PII scan on the final `data/processed/` files to confirm zero plaintext usernames or timestamps (SC‑005).  
   * Compile the final JSON report (conforming to `contracts/output.schema.yaml`) which includes model summary, sensitivity analysis, validation results (Kappa and pass flag), and metadata (sample sizes, runtime).  

## FR/SC Mapping

| ID | Type | Plan Element |
| :--- | :--- | :--- |
| FR-001 | Req | Phase 1 ingestion logic, subreddit filter, TARGET_N handling. |
| FR-001a | Req | Phase 1 verification of subreddit presence; fallback to `pushshift/reddit` or abort. |
| FR-002 | Req | Phase 2 keyword classification with negation exclusion. |
| FR-002a | Req | Phase 2 logging of “Negation Exclusions”. |
| FR-003 | Req | Phase 3 VADER scoring implementation. |
| FR-003b | Req | Phase 3 secondary lexicon construction (exclude prime words). |
| FR-004 | Req | Phase 5 LMM fixed effect for `thread_type`. |
| FR-005 | Req | Phase 5 LMM controls (`thread_age`, `comment_count`). |
| FR-005a | Req | Phase 5 sensitivity analysis thresholds. |
| FR-006 | Req | Phase 6 boxplot generation. |
| FR-009 | Req | Phase 1 SHA‑256 hashing, timestamp stripping. |
| FR-010 | Req | Phase 4 stratified sampling (thread_type × subreddit) with ≥ 50 per stratum. |
| FR-011 | Req | Phase 4 Human Annotation Protocol (3 raters, codebook). |
| FR-012 | Req | Phase 3 CPU‑only constraint, runtime monitoring. |
| SC-001 | Metric | Phase 5 LMM p‑value < 0.05 check. |
| SC-002 | Metric | Phase 5 coefficient stability after controls. |
| SC-003 | Metric | Phase 5 reporting of p‑value and CI. |
| SC-004 | Metric | Phase 3/5 runtime < 4 h verification. |
| SC-005 | Metric | Phase 6 PII scan report. |
| SC-006 | Metric | Phase 4 Kappa ≥ 0.7 report. |
| SC-007 | Metric | Phase 4 confirmation that gold standard was produced by human raters. |
| SC-008 | Metric | Phase 3 `neg_score` definition check (VADER `neg` component). |

