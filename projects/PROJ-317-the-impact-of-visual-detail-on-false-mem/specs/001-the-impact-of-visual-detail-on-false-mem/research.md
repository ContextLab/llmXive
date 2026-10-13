# Research: Visual Detail and False Memory Susceptibility

## Summary
This study examines whether **visual detail** (enhanced vs. reduced vs. baseline) modulates **false‑memory susceptibility** using a **Repeated‑Measures (Within‑Subjects) design**. Participants view all three stimulus conditions in a counter‑balanced order, complete a brief arithmetic distractor, and answer a recognition questionnaire containing true and lure items. The primary outcome is the **false‑memory rate** (proportion of “Yes” responses to lure items) per condition.

## Theoretical Framework
- **Misinformation Effect** (Loftus et al.) demonstrates that post‑event information can alter memory. Here we test a *pre‑event* manipulation: visual detail.
- **Constructive Memory** (Bartlett) predicts that gaps are filled with plausible details; richer visual scenes may either **(a)** increase cognitive load → more lures accepted, or **(b)** provide more distinctive cues → fewer lures. The direction is exploratory.
- **Hypothesis**: Visual detail will **significantly affect** false‑memory rates across conditions.

## Dataset Strategy
The verified datasets block contains only a math parquet file, which is **not applicable**. Therefore:

| Dataset | Source | Availability | Variable Fit |
|---------|--------|--------------|--------------|
| **Visual Genome (Pre‑bundled subset)** | `data/stimuli/raw_subset/` (A collection of curated images.) | **Verified** by content hash, shipped with repo | Provides scene images, object annotations, and can be used to compute `complexity_score`. |
| **Visual Genome (Full)** | `datasets.load_dataset("visual_genome")` | **Pending verification** – not listed in verified block. The pipeline includes a switch (`--source visual_genome`) for the final study once verification is obtained. | Same variables as above; streaming mode will be used to stay within memory limits. |

*Data‑Variable Fit*: The subset includes `image_id`, object lists, and resolution metadata; we compute a derived `complexity_score` (edge density + object count) to satisfy FR‑001. The outcome variable (false‑memory rate) is derived from participant responses, satisfying SC‑001.

**Data Availability Plan**  
- CI runs use the pre‑bundled subset (no external download).  
- For the full study, we will stream Visual Genome (`streaming=True`) and sample a limited subset of images to stay within the allocated RAM budget.  
- All image files are stored under `data/stimuli/`; checksums recorded in `state/...yaml`.

## Statistical Methodology
- **Design**: Repeated‑Measures (Within‑Subjects) with *condition* (enhanced, reduced, baseline) as the within‑subject factor. Condition order is **Latin‑square counterbalanced** across participants and recorded as a covariate.
- **Model**: **Generalized Linear Mixed‑Effects Model (GLMM)** with a binomial (logit) link to model the binary lure responses. Implemented via `statsmodels` (`statsmodels.genmod.bayes_mixed_glm.BinomialBayesMixedGLM` or equivalent). Participant IDs are included as random intercepts; condition order is added as a fixed effect covariate to control for fatigue/learning.
- **Assumption Checks**:  
  - **Overdispersion**: Examine Pearson residuals.  
  - **Random‑effects adequacy**: Compare models with vs. without random intercepts via likelihood ratio test.  
- **Multiple‑Comparison**: Bonferroni correction for the three pairwise contrasts (enhanced vs baseline, reduced vs baseline, enhanced vs reduced).
- **Power Analysis** (SC‑002):  
  - **Effect size justification**: Prior visual‑memory work (Brady et al.) reported a medium effect. for detail‑related memory differences; we adopt this as a baseline.  
  - **Sensitivity analysis**: `code/analysis/power.py` computes required N for effect sizes f = 0.20, 0.25, 0.30 (see Table 1). For f = 0.25, α = 0.05, power = 0.80 → **N ≈ 50** participants. The script will abort real data collection if the projected N falls below 50.  
- **Effect Size Reporting**: Report odds ratios and marginal R² for the GLMM, and Cohen’s d for pairwise log‑odds contrasts.  
- **Measurement Validity**: Recognition items follow the paradigm of Loftus & Palmer (1974); lures are generated via a “Semantic Absence” algorithm that selects objects present in the same scene category but absent from the target image.  

All statistical steps are performed with **CPU‑only** libraries (`statsmodels`, `scipy`, `matplotlib`).

## Compute Feasibility
- **CPU‑First**: All image compositing (PIL), data loading (datasets streaming), and statistical analysis run on the GitHub Actions free tier.  
- **Memory**: Streaming ensures < 5 GB RAM even with full Visual Genome.  
- **Disk**: Pre‑bundled subset ≈ a moderate size on the order of tens of megabytes; full streamed images processed on‑the‑fly, final outputs < 200 MB.  
- **Runtime**: Estimated < 6 h total; analysis < 10 min for 60 participants.  

## Ethics & Compliance
- **IRB**: No real participants are recruited in CI; a manual IRB approval checkpoint (`data/ethics/irb_approval.txt`) must be satisfied before any `--mode real` run.  
- **Consent**: `data/ethics/informed_consent.md` contains a GDPR‑compliant consent script; participants must click “I Agree” before the first stimulus.  
- **Anonymization**: Participant IDs are generated as pseudonyms (`P-001`, …) and stored separately from any IP logs.  
- **Data Security**: All files under `data/` are checksummed; no PII is ever written to the repository.  

--- 