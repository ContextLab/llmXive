# Research: The Impact of Text Message Tone on Perceived Emotional Support

**Feature**: `001-text-tone-emotional-support`  
**Date**: 2026-08-08  

## Overview
This document outlines the empirical strategy, dataset considerations, statistical methods, and methodological safeguards required to answer the central question: *How does the tone of a text message (emoji count, punctuation style, length) interact with the relational context (close friend vs. acquaintance) to shape perceived emotional support?*  

All decisions are grounded in the functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑005) from the specification. No un‑specified thresholds or metrics are introduced.

## Dataset Strategy

| Dataset | Source | Access | Role |
|---------|--------|--------|------|
| **Stimuli metadata** | Generated locally from base scenarios (see Phase 1) | Programmatic (no external download) | Provides the objective cue features for each text message. |
| **Human ratings** | Collected via Prolific (real participants) and stored in `data/raw/real_ratings.csv` | Uploaded by the research team after collection; **not** fetched from an external URL. | Primary dependent variable (multi‑point Likert rating of perceived emotional support). |
| **Consent records** | Stored under `data/consent/` (JSON) | Internal only | Guarantees compliance with Principle VI (anonymity & consent). |

> **Note**: No open‑source dataset matching the required structure exists. The plan therefore relies on the *real* dataset produced by the Prolific study, as mandated by FR‑002. The pipeline validates its presence and integrity before any analysis.

## Methods Rationale

| Analysis Component | Method | Library (CPU‑only) | Justification |
|--------------------|--------|--------------------|---------------|
| Cue‑intensity computation | Weighted sum of three binary features (emoji, punctuation, length) | `pandas` | Directly implements the operationalization defined in FR‑001 and FR‑005. |
| **Power analysis** | **Simulation‑based LMM power estimation**: generate 1 000 synthetic datasets using the planned random‑effects structure, fit the LMM, and compute the proportion of significant interaction effects (α = 0.05). | `statsmodels`, `numpy` | Aligns with FR‑002’s requirement and avoids the inappropriate ANOVA‑based calculation. |
| Linear Mixed‑Effects Model (primary) | `statsmodels.MixedLM` with random intercepts for `participant_id` and `stimulus_id` | `statsmodels` | Provides a well‑established frequentist LMM framework compatible with CPU‑only CI runners (Principle VII). |
| Degrees of freedom | Wald Z (normal approximation) – `statsmodels` does not implement Satterthwaite for MixedLM; this limitation is explicitly reported. | `statsmodels` | Transparent reporting of the limitation; satisfies SC‑001 without mis‑claiming Satterthwaite. |
| Post‑hoc pairwise comparisons | Tukey HSD (`statsmodels.stats.multicomp.pairwise_tukeyhsd`) | `statsmodels` | Controls family‑wise error rate as required by SC‑003. |
| Sensitivity analysis | Re‑fit LMM under three alternative cue‑intensity weightings (equal, emoji‑dominant, punctuation‑dominant) | `statsmodels` (same pipeline) | Directly addresses FR‑005 and SC‑002. |
| Straight‑lining detection | Variance‑zero check per participant across all stimulus ratings | `numpy`/`pandas` | Implements FR‑006. |
| Missing‑data handling | Listwise deletion of participants with incomplete rows (documented) | `pandas` | Satisfies FR‑006 and ensures model assumptions. |
| Randomization & Counterbalancing | Per‑participant random order generation; each stimulus presented once in each relationship context (block‑balanced). | `numpy` | Guarantees internal validity (addresses methodology concerns). |

### Statistical Rigor Checklist
- **Multiple comparisons** – Tukey HSD applied to all post‑hoc tests (SC‑003).  
- **Power justification** – Simulation‑based LMM power analysis; target N = 60 participants (SC‑001).  
- **Causal inference** – The design is observational (participants rate pre‑generated stimuli). All claims will be framed as *associational*; no causal language is used (complies with statistical rigor).  
- **Measurement validity** – The Likert scale is a standard, validated measure of perceived support in affective research (no new instrument introduced).  
- **Collinearity** – Cue‑intensity is a composite; its components are not entered as separate predictors, avoiding multicollinearity concerns.  

## Execution Plan Summary (mirrors `plan.md` phases)
1. **Stimulus generation** – creates `stimuli.csv` with fully crossed feature matrix and balanced context assignment (FR‑001).  
2. **Data verification** – checks existence, checksum, straight‑lining, and missingness (FR‑002, FR‑006, FR‑007).  
3. **Pre‑processing** – merges stimulus metadata with ratings, computes cue‑intensity (FR‑001, FR‑005).  
4. **Primary LMM** – tests `relationship × cue_intensity` interaction (FR‑003, SC‑001) using Wald Z.  
5. **Post‑hoc Tukey** – conditional on a significant interaction (FR‑004, SC‑003).  
6. **Sensitivity analysis** – three alternative weightings, reports stability (FR‑005, SC‑002).  
7. **Reporting & CI** – aggregates results, ensures runtime ≤ 6 h (SC‑005), runs contract tests, validates artifact manifest (Principle V).  

All steps are ordered so that data is downloaded/validated before any downstream computation, satisfying the “producer‑before‑consumer” ordering required by the methodology panel.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient participants (N < 60) | Power loss → SC‑001 not met | Early recruitment monitoring; if N < 60 after a pre‑registered window, pause analysis and report limitation. |
| Straight‑lining participants inflate variance | Bias in estimates | Automatic detection and exclusion; exclusion counts reported in `report.md`. |
| Missing ratings for a subset of stimuli | Reduced data completeness | Listwise deletion; documented missing‑data log; sensitivity check on reduced sample size. |
| Prolific data export format changes | Pipeline breakage | Version‑pin the export schema; include fallback parsing logic. |

No additional constraints beyond those explicitly listed in the specification are introduced. 
