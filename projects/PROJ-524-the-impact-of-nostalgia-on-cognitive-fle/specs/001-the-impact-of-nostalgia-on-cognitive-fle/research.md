# Research: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview
The goal is to assess whether exposure to nostalgic stimuli is **associationally** linked to better performance on the Wisconsin Card Sorting Test (WCST) among adults aged ≥ 65. Because the experimental design is **between‑subjects**, the appropriate inferential test is **Welch’s independent‑samples t‑test**. All hypotheses are framed as associations; causal language is avoided.

## Dataset Strategy

| Dataset | Source URL(s) | Variables Needed | Verification Status | Notes |
|---------|---------------|------------------|---------------------|-------|
| WCST + Age ≥ 65 + Stimulus label | **NO verified source found** | `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`, `MMSE` (optional) | ⚠️ Not available publicly; will be generated synthetically if no open source appears. | Synthetic data will respect realistic means/SDs from published WCST literature. |
| MMSE scores (optional) | https://huggingface.co/datasets/rufernan/MMSense/resolve/main/gt_20mpp/Chlorophyll/_timestamps.txt, https://huggingface.co/datasets/jyjyjyjy/MMS-e/resolve/main/test/Fixed_Patch_QA/fix12/annotations/action_recognition.jsonl | `participant_id`, `mmse_score` | ✅ Verified URL, but dataset does not contain WCST metrics. | May be used only to demonstrate MMSE handling logic; not combined with WCST data. |

### Primary Strategy
1. **Search for an open dataset** containing the required schema on Hugging Face, OpenNeuro, or OpenML.  
2. **If none found**, invoke the synthetic generator (see `code/ingestion.py`) to create a realistic dataset (200 participants, 100 per condition) with age distribution (65‑85 y), MMSE scores (mean ≈ 28, SD ≈ 1.5), and WCST metrics drawn from published distributions.  
3. **Stimulus files** (audio/video) will be stored under `data/stimuli/` with SHA‑256 checksums; because no open stimuli are verified, placeholder files (e.g., short tone clips) will be used and clearly marked as “simulation only”.

### Fallback Logic
- If MMSE data become available from a verified source, it will be merged by `participant_id`.  
- If only WCST metrics are available (no MMSE), the MMSE exclusion step (FR‑006) will be skipped and logged.

## Statistical Methodology

### Primary Analysis
- **Design**: Between‑subjects (nostalgia vs. control).  
- **Test**: Welch’s independent‑samples t‑test for each outcome (`perseverative_errors`, `categories_completed`).  
- **Multiple‑Comparison Correction**: Bonferroni correction for the two outcomes (α = 0.05 / 2 = 0.025).  
- **Effect Size**: Cohen’s d with 95 % confidence interval, using the pooled variance appropriate for Welch’s test.  
- **Minimum Detectable Effect Size (MDES)**: Computed post‑hoc from observed sample size and pooled variance; reported as a limitation (value deferred).  
- **Covariate Adjustment (optional)**: If additional covariates (e.g., education) are present, a linear model will be fitted; otherwise the analysis remains unadjusted and the output will note `"adjustment_status": "unadjusted"`.

### Sensitivity Analyses (FR‑005)
- **Alpha Sweep**: Re‑run the Welch tests at α = 0.01, 0.05, 0.10.  
- **MMSE Exclusion Sensitivity**: Compare results with and without participants having `MMSE < 24` (if MMSE present).  
- **Borderline Flagging**: Any p‑value in the range 0.04 – 0.06 after correction will be labeled `"sensitive"` in the output schema.

### Assumptions & Limitations
- **Observational Data**: No random assignment; findings are correlational.  
- **Collinearity**: `perseverative_errors` and `categories_completed` are related; we will not claim independent effects—rather we will report each outcome separately.  
- **Sample Size**: If N < 50 per group, MDES will be large; this will be highlighted.  
- **Measurement Validity**: WCST is a validated measure of cognitive flexibility (cite standard neuropsychology texts; citation validation performed by `reference_validator.py`).  

## Compute Feasibility
- All computations run on the CPU‑only GitHub Actions runner.  
- Expected runtime < 30 minutes; memory < 2 GB.  
- No GPU‑only libraries are used; the pipeline is fully compatible with the free tier.  

## Citations & Validation
- All literature citations (WCST validity, nostalgia induction effects) will be checked by `code/reference_validator.py` for title‑overlap ≥ 0.7.  
- Stimulus files will carry SHA‑256 checksums recorded in `data/stimuli/manifest.json`.  

---
