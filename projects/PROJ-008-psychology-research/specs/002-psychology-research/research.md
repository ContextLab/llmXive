# Research: Mindfulness Components and Delivery Formats in ASD Social Skills

## Research Question
What is the efficacy of mindfulness‑based interventions for improving social skills in children aged 6‑12 with Autism Spectrum Disorder (ASD), and how do the effects vary by (a) mindfulness component (breathing, body‑scan, mindful movement, combined) and (b) delivery format (caregiver‑mediated vs. child‑led)?

## Hypotheses
| # | Hypothesis | Expected Direction |
|---|------------|--------------------|
| H1 (Primary) | Mindfulness interventions produce a positive pooled effect (Hedges’ g > 0) on validated social‑skill outcomes. | Positive |
| H2 (Component) | Interventions containing **multiple** mindfulness components yield larger effects than single‑component interventions. | Larger g |
| H3 (Delivery) | Caregiver‑mediated delivery yields a larger pooled effect than child‑led delivery. | Larger g |
| H4 (Follow‑up) | Effects are sustained (or increase) at ≥ 3‑month follow‑up compared with immediate post‑intervention. | Non‑decreasing g |

## Dataset Strategy

| Dataset | Source | Access Method | Role |
|---------|--------|---------------|------|
| ClinicalTrials.gov | https://clinicaltrials.gov/ | `requests` to public API (v2) | Primary source of registered RCTs (2015‑2024) |
| OSF | https://osf.io/ | `requests` to OSF public API | Supplemental source for pre‑registered trials |
| PubMed Central (Open‑Access) | https://www.ncbi.nlm.nih.gov/pmc/ | `biopython` Entrez API (PMC) | Retrieves **open‑access** full‑text articles to obtain means/SDs when not present in registries; if no open‑access full text is available, falls back to abstract extraction (FR‑023, FR‑031, updated for open‑access constraint). |

All sources are openly downloadable; no credentials required (Constitution VI). Registry records are archived verbatim under `data/raw/` and checksummed. PubMed queries are logged in `data/metadata/pubmed_log.json`.

## Inclusion / Exclusion Criteria
- **Population**: Children up to 12 years old, confirmed ASD diagnosis (DSM‑5 or ICD‑10).  
- **Design**: **Only randomized controlled trials (RCTs)** are included (`design == 'rct'`). Quasi‑experimental studies are logged for a **sensitivity analysis** but excluded from the primary meta‑analysis (addresses methodology‑588d7186).  
- **Intervention**: Must contain at least one core mindfulness component (breathing, body‑scan, mindful movement).  
- **Outcome**: Must report a validated social‑skill measure (e.g., Social Responsiveness Scale‑2, Vineland Adaptive Behavior Scales) and provide sufficient summary statistics (means, SDs, Ns) either in the registry entry or in the associated **open‑access** journal article (addressing data_resources‑96035540).  
- **Registration**: Listed in ClinicalTrials.gov or OSF, registration date between 2015‑01‑01 and 2024‑12‑31.  
- **Exclusions**: Age outside 6‑12, no control group, no social‑skill outcome, duplicate publications, ambiguous delivery format, or missing outcome statistics that cannot be retrieved from PubMed Central. Records where component or delivery‑format extraction relied solely on abstracts are flagged `abstract_only=True` and **included** in the primary analysis with a flag; a separate sensitivity analysis will compare results with and without these flagged records (methodology‑abf95ff3).  

## Methodological Rigor

### Effect‑Size Computation
- **Metric**: Hedges’ g with small‑sample correction (J = 1 − 3/(4N − 9)).  
- **Preferred Input**: **Change‑score data** (pre‑post differences) when both baseline and post‑intervention means/SDs are available.  
- **Fallback**: If change scores are unavailable, compute Hedges’ g from post‑intervention means/SDs **adjusted for baseline imbalance** using a **sensitivity analysis** over three plausible pre‑post correlations (r = 0.3, 0.5, 0.7). The range of resulting g values will be reported (addresses methodology‑dc72a3a8, scientific_soundness‑cb3b5961).  
- **SE & CI**: Standard error computed per conventional formulas; 95 % CI via normal approximation.  

### Risk‑of‑Bias Assessment
- Extract RoB2 ratings from trial protocols or associated publications (methodology‑2d4e176d).  
- Store ratings in `metadata/rob_log.json` under the field `rob_rating`.  
- Use `rob_rating` as a moderator and as a weighting factor in sensitivity analyses (FR‑030).

### Meta‑Analysis Model
- **Model**: **Random‑effects** model using **REML** estimator with **Hartung‑Knapp** adjustment for **all** analyses, regardless of heterogeneity (methodology‑80dd5ee8).  
- Compute Q, I², τ² for reporting.  

### Subgroup Analyses & Power
- **Component**: breathing, body‑scan, mindful movement, combined.  
- **Delivery Format**: caregiver‑mediated, child‑led, hybrid.  
- **Social‑Skill Domain**: communication, peer interaction, emotional regulation, adaptive behavior.  
- **Follow‑up**: ≤ 3 months vs. > 3 months.  
- **Additional Moderators**: intervention dosage (sessions/week), therapist training level (certified/non‑certified), baseline severity (mean baseline score).  
- **Multiple Comparisons**: Bonferroni correction across the four primary subgroup families.  
- **Power**: Assuming a moderate sample size per study, the overall analysis is powered to detect a medium pooled effect size at [deferred] power. For subgroups, power calculations are performed for **g = 0.3, 0.5, 0.6**; required numbers of studies are reported for each scenario (methodology‑f1ea8fca, scientific_soundness‑d8a28d8d).  
- Subgroups with fewer than 15 studies are not pursued to avoid severe under‑power.

### Publication Bias
- Funnel plot & Egger’s regression test only if total included studies **N ≥ 10** (FR‑006).  
- Otherwise, report “insufficient studies for bias assessment”.

### Multi‑Arm Study Handling
- Combine multiple treatment arms into a single arm (averaging effect sizes) per Cochrane guidance (methodology‑603f7e57).  
- Record the combination rationale in `metadata/multi_arm_log.json`.

### Component & Delivery‑Format Extraction
- Use curated regex dictionary; each match receives a confidence score (0‑1).  
- Records with confidence < 0.7 or where extraction relied solely on abstracts are flagged `abstract_only=True` and **included** with a flag; a sensitivity analysis will compare results with and without these records (methodology‑abf95ff3).

### DOI Verification
- Extract DOI from registry metadata; validate via Crossref API.  
- Log DOI verification status in `metadata/registry_log.json` (plan_consistency‑a02b0bf1).

### Power & Sample‑Size Considerations
- Overall detectable g is estimated to be moderate, based on a modest sample size.  
- Subgroup detectable g at a moderate level with a modest sample size.  
- If final eligible N < 10, pipeline switches to descriptive synthesis and notes limited power (SC‑005).

## Compute Feasibility
- All calculations use `numpy`, `scipy`, and `statsmodels` (CPU‑only).  
- Expected study count ≤ 100 → Dataframe size < 10 MB; memory use < 200 MB.  
- End‑to‑end runtime on GitHub Actions [deferred] (well within 6 h limit).

## Decision Rationale
- **Hedges’ g** chosen for small‑sample bias correction.  
- **Random‑effects (REML + Hartung‑Knapp)** as the **pre‑specified** primary model because mindfulness interventions differ in dosage, modality, and therapist training.  
- **Delivery‑format tagging** mandated by Constitution VII to directly test the caregiver‑mediated hypothesis.  
- **Bonferroni** correction ensures family‑wise error control across multiple subgroup families.  

---

