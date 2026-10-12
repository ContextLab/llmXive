# Research: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Executive Summary
We will conduct a secondary analysis of two open‑access OpenNeuro datasets: *ds000208* (Cyberball rejection/control) and *ds003392* (positive‑feedback reward). By matching participant IDs across the two datasets we can test whether simulated social rejection modulates subsequent behavioral proxies of neural response: reaction time (RT) and self‑reported mood. If IDs do not overlap, we will fall back to a Between‑Subjects analysis using the rejection dataset alone, clearly documenting this limitation.

## Dataset Strategy

| Role | Source | URL | Variables Required |
|------|--------|-----|---------------------|
| **Primary (Rejection & Control)** | OpenNeuro (mirrored on HuggingFace) | `https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet` | `participant_id`, `condition` (values *rejection*, *control*), `reaction_time`, `mood_rating` |
| **Reward (Positive Feedback)** | OpenNeuro (mirrored on HuggingFace) | `https://huggingface.co/datasets/openneuro/ds003392/resolve/main/data.parquet` | `participant_id`, `condition` (value *reward*), `reaction_time`, `mood_rating` |

*Both datasets are publicly downloadable without authentication (verified).*

### Verification
- The ingestion script will compute SHA‑256 checksums for each file and record them in `state/projects/…yaml`.  
- Schema validation against `contracts/dataset.schema.yaml` ensures all required columns exist in **both** datasets.  
- A pre‑download size estimate guarantees the combined file size fits within the 7 GB RAM limit.  

## Statistical Methodology

### Design Selection Logic
1. **Condition Presence** – Verify that each dataset contains its expected condition(s).  
2. **Participant Overlap** – Using `data/interim/overlap_report.json`, confirm whether every `participant_id` appears in **both** datasets.  
   - If true → **Within‑Subjects Mixed ANOVA** (2 × 2 design: Rejection vs. Control × Reward vs. No‑Reward).  
   - If false → **Between‑Subjects One‑Way ANOVA** on the rejection dataset alone; the limitation is noted in the report.  

### Primary Model
- **Test**: Mixed ANOVA (or One‑Way ANOVA if needed) for RT and mood separately.  
- **Assumption Checks**: Shapiro‑Wilk normality (if N > 30) and Mauchly’s sphericity test. Warnings are logged but do not stop execution.  

### Multiple‑Comparison Control
- Benjamini‑Hochberg FDR correction applied to the two raw p‑values (RT and mood). The corrected column `p_fdr` must be **≥** the raw `p_raw` (the spec’s opposite inequality is mathematically impossible and has been flagged for revision).

### Sensitivity Analysis
- The α threshold is swept over {0.01, 0.05, 0.1}. For each α, the pipeline records whether the FDR‑corrected p‑value meets significance (SC‑004).  

### Power & Sample Size
- The spec caps N ≤ 500 (FR‑005). An a priori power calculation for a medium effect size (d = 0.5) indicates ~64 participants per group are sufficient, so the available sample is adequately powered. This justification is documented in the implementation plan.

## Compute Feasibility

| Resource | Requirement | Plan |
|----------|-------------|------|
| CPU | All steps are pure Python (pandas, scipy, statsmodels) | CPU‑first on GitHub Actions free tier |
| RAM | ≤ 7 GB | Pre‑download size check; pandas memory‑mapping |
| Time | ≤ 6 h total | Expected < 30 min; CI will enforce with `T015` |
| GPU | Not needed | No GPU escape hatch required |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing required columns in either dataset | Pipeline aborts (FR‑001) | `T003`/`T004` validation with clear error code 1 |
| No participant overlap | Design switches to Between‑Subjects (FR‑007) | `T005`/`T006` generate explicit design metadata |
| Dataset larger than RAM | OOM failure | `T003`/`T004` abort before download |
| Small N causing ANOVA convergence warnings | Results may be unstable | Log warnings; include in Limitations |
| API endpoint unavailable | No data download | `T003`/`T004` abort; CI reports failure |

## Decision Rationale
- **Dataset Choice**: Both verified OpenNeuro parquet files satisfy the openness requirement; no fabricated reward data is used.  
- **Statistical Approach**: Mixed ANOVA (or One‑Way ANOVA) is computationally cheap, satisfies FR‑004 (FDR) and FR‑006 (sensitivity).  
- **Design Flexibility**: Automatic selection ensures compliance with FR‑007/FR‑008.  
- **Scope Discipline**: No additional datasets are introduced beyond the two verified ones.  

---



