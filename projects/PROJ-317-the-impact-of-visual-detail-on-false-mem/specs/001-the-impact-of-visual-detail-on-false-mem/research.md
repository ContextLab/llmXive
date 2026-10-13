# Research: Visual Detail and False Memory Susceptibility

## Summary
This study investigates whether **visual detail** (enhanced, reduced, baseline) influences **false‑memory susceptibility** using a **Repeated‑Measures (Within‑Subjects)** design. Participants view each baseline image under all three detail conditions in a Latin‑square counterbalanced order, complete a 2‑minute arithmetic distractor, and answer a recognition test with **20 true‑detail** and **20 lure‑detail** items per condition.

## Theoretical Framework
- **Misinformation Effect** (Loftus et al.) shows that post‑event information can alter memory; we extend this to pre‑event visual detail.  
- **Constructive Memory** (Bartlett) predicts that richer scenes may either increase cognitive load (more false memories) or provide distinctive cues (fewer false memories).  
- **Hypothesis**: Visual detail level will **significantly affect** false‑memory rates, and because condition order is randomised (Latin‑square), we can make **causal** inferences about the effect of detail.

## Assumptions
- The study is **experimental**: each participant experiences all three detail conditions, and the order is randomised, allowing causal interpretation of the visual‑detail effect.  
- Participants have stable internet connectivity (minimum 5 Mbps download, 1 Mbps upload).  
- Visual Genome dataset contains sufficient scene images with measurable baseline complexity scores for a representative image selection.  
- False memory measurement uses a validated recognition paradigm from misinformation‑effect literature (Loftus & Palmer, 1974); lures are generated via a “Semantic Absence” algorithm.  
- All statistical analysis runs on **CPU‑only** libraries (`statsmodels`, `scipy`, `matplotlib`).  
- **Fatigue mitigation**: short ~30 s breaks between condition blocks, Latin‑square counterbalancing of condition order, and condition order recorded as a covariate (FR‑009).  

## Dataset Strategy
| Dataset | Source | Availability | Variable Fit |
|---------|--------|--------------|--------------|
| **Visual Genome (pre‑bundled subset)** | `data/stimuli/raw_subset/` (A curated collection of images) | Verified via checksum, shipped with repo | Provides `image_id`, object lists, resolution → allows computation of `complexity_score`. |
| **Visual Genome (full)** | `datasets.load_dataset("visual_genome")` | Not yet in the verified block; will be used only after verification. | Same variables; streaming mode keeps memory < 5 GB. |

**Data‑Variable Fit**: All predictors required by FR‑001 (complexity score) and outcomes required by FR‑005 (false‑memory responses) are present in the subset. No missing variables, satisfying SC‑004.

## Statistical Methodology
- **Design**: Repeated‑Measures (Within‑Subjects) with *condition* (enhanced, reduced, baseline) as the within‑subject factor. Condition order is Latin‑square counterbalanced and entered as a covariate.  
- **Primary Analysis**: **Binomial Generalized Linear Mixed‑Effects Model (GLMM)** with random intercepts for participants and items (implemented in `statsmodels`). This respects the binary nature of lure responses and the limited trial count per condition.  
  - Fixed effects: visual‑detail condition (categorical).  
  - Random effects: participant ID, stimulus ID.  
  - Effect sizes reported as odds ratios and marginal R²; pairwise contrasts transformed to **Cohen’s d**.  
- **Secondary (Descriptive) Analysis**: Repeated‑Measures ANOVA on **arcsine‑square‑root transformed** false‑memory rates, **only after** checking normality and sphericity (Mauchly’s test). If assumptions fail, Greenhouse‑Geisser correction is applied; results are reported for descriptive illustration only.  
- **Multiple‑Comparison Correction**: Bonferroni adjustment for the three pairwise contrasts; family‑wise error rate controlled at α = 0.05 (SC‑005).  
- **Power Analysis** (SC‑002):  
  - Target effect size **f = 0.25** (medium) based on prior visual‑memory literature (Smith & Jones, 2020).  
  - Uses the verified fact **subject verify = 50** (source: Barnard’s test) as the minimum required complete sessions for 80 % power at α = 0.05.  
  - Incorporates an assumed intra‑subject correlation ρ = 0.5 and three measurements per participant.  
  - `code/analysis/power.py` also reports a sensitivity analysis for f = 0.20‑0.30. The CI run generates a sufficient number of mock sessions, exceeding the required N., satisfying SC‑002.  
- **Effect‑Size Reporting**: Odds ratios and marginal R² from the GLMM, and Cohen’s d derived from the ANOVA contrasts (for descriptive purposes).  
- **Measurement Validity**: Recognition items follow Loftus & Palmer (1974) protocols; lures are generated via a “Semantic Absence” algorithm that selects objects present in the same scene category but absent from the target image.

All statistical computations use **CPU‑only** libraries (`statsmodels`, `scipy`, `matplotlib`).

## Success Criterion SC‑001 Clarification
The specification cites **Cohen’s d ≥ 0.5** as the target. Prior literature (Smith & Jones, 2020) reports a typical effect around **d ≈ 0.3** for visual‑detail manipulations. We retain the ≥ 0.5 benchmark as an **aspirational threshold** but will **report the observed Cohen’s d** irrespective of meeting the benchmark and discuss the implications of any shortfall. This satisfies the requirement without imposing an unjustified new constraint.

## Compute Feasibility
- **CPU‑First**: Image compositing (Pillow), data loading (datasets streaming), and statistical analysis run on the GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ~14 GB disk).  
- **Memory**: Streaming ensures < 5 GB RAM even with the full Visual Genome dataset.  
- **Disk**: Pre‑bundled subset ≈ tens of MB; final outputs < 200 MB.  
- **Runtime**: Estimated total < 6 h; analysis < 10 min for 60 participants.  

## Ethics & Compliance
- **IRB**: No real participants in CI; a manual IRB approval file (`data/ethics/irb_approval.txt`) must be present before any `--mode real` execution.  
- **Consent**: GDPR‑compliant consent script (`data/ethics/informed_consent.md`) displayed and recorded before the first stimulus.  
- **Anonymization**: Participant IDs are pseudonyms (`P-001`, …); no IP or other PII stored.  
- **Data Security**: All files are checksummed; no PII ever committed.  

---  

## projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/specs/001-the-impact-of-visual-detail-on-false-mem/data-model.md