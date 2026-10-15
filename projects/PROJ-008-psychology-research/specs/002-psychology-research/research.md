# Research: Mindfulness Components and Delivery Formats in ASD Social Skills

## Research Question
What is the efficacy of mindfulness‑based interventions for improving social skills in children aged 6‑12 with Autism Spectrum Disorder (ASD), and how do effects vary by (a) mindfulness component (breathing, body‑scan, mindful movement, combined) and (b) delivery format (caregiver‑mediated vs. child‑led)?

## Hypotheses
| # | Hypothesis | Expected Direction |
|---|------------|--------------------|
| H1 (Primary) | Mindfulness interventions produce a positive pooled effect (Hedges’ g > 0) on validated social‑skill outcomes. | Positive |
| H2 (Component) | Interventions that include **multiple** mindfulness components yield larger effects than single‑component interventions. | Larger g |
| H3 (Delivery) | Caregiver‑mediated delivery yields a larger pooled effect than child‑led delivery. | Larger g |
| H4 (Follow‑up) | Effects are sustained (or increase) at ≥ 3‑month follow‑up compared with immediate post‑intervention. | Non‑decreasing g |

## Dataset Strategy

| Dataset | Source | Access Method | Role |
|---------|--------|---------------|------|
| ClinicalTrials.gov | https://clinicaltrials.gov/ | `requests` to the public API (v2) | Primary source of registered RCTs (2015‑2024) |
| OSF | https://osf.io/ | `requests` to OSF public API | Supplemental source for pre‑registered trials |

Both sources are openly downloadable; no credentials required (Constitution Principle VI). All retrieved records are archived verbatim under `data/raw/` and hashed.

## Inclusion / Exclusion Criteria
- **Population**: Children 6‑12 years, confirmed ASD diagnosis (DSM‑5 or ICD‑10).  
- **Intervention**: Must contain at least one core mindfulness component (breathing, body‑scan, mindful movement).  
- **Outcome**: Must report a validated social‑skill measure (e.g., Social Responsiveness Scale‑2, Vineland Adaptive Behavior Scales).  
- **Design**: Randomized controlled trial (parallel or crossover) or quasi‑experimental with a concurrent control group.  
- **Registration**: Trial must be listed in ClinicalTrials.gov or OSF and have a registration date between 2015‑01‑01 and 2024‑12‑31.  
- **Exclusions**: Age outside 6‑12, no control group, no social‑skill outcome, duplicate publications, or ambiguous delivery format.

## Methodological Rigor

### Effect‑Size Computation
- **Metric**: Hedges’ g with small‑sample correction (J = 1 − 3/(4N − 9)).  
- **Inputs**: Post‑intervention means, SDs, and Ns for treatment and control groups (FR‑013).  
- **Standard Error**: Calculated per standard formulas; 95 % CI derived using normal approximation.

### Meta‑Analysis Model
- Compute Cochran’s Q and I².  
- **Model Selection**: Fixed‑effects if I² ≤ 50 %; otherwise random‑effects (DerSimonian‑Laird).  
- Report both models for sensitivity (FR‑005).

### Subgroup Analyses
- **Component**: breathing, body‑scan, mindful movement, combined.  
- **Delivery Format**: caregiver‑mediated, child‑led, hybrid.  
- **Social‑Skill Domain**: communication, peer interaction, emotional regulation, adaptive behavior.  
- **Follow‑up**: ≤ 3 months vs. > 3 months.  
- Apply Bonferroni correction across the four subgroup families (FR‑014).

### Publication Bias
- Funnel plot & Egger’s regression test only if total included studies **N ≥ 10** (FR‑006).  
- Otherwise, report “insufficient studies for bias assessment”.

### Multi‑Arm Study Handling
- Select a single primary control arm per treatment arm (closest in description to the primary control condition).  
- Record the selection rationale in `metadata/multi_arm_log.json`. This avoids unit‑of‑analysis inflation (FR‑008).

### Data Extraction Strategy
- Use a structured keyword dictionary for components and delivery formats; each match receives a confidence score (0‑1).  
- Entries with confidence < 0.7 are flagged for manual review; the reviewer must confirm before inclusion (ensures construct validity).  
- Abstract‑only fallback when full text unavailable (FR‑009).

### Power & Sample‑Size Considerations
- Anticipated median N per study ≈ 30 (typical ASD RCT).  
- With ≤ 30 studies, the detectable pooled g at 80 % power ≈ 0.45 (two‑tailed α = 0.05).  
- If the final eligible N < 10, the pipeline switches to descriptive synthesis and notes limited statistical power (SC‑005 compliance).

### Measurement Validity
- Only validated instruments (SRS‑2, VABS, ADOS social‑communication subscale) are accepted. Instrument name is stored in `cleaned_studies.csv`; validity is documented in the protocol (see `docs/instrument_validity.md`).

### Collinearity Note
- Delivery format and component tags are orthogonal by definition; no regression claims of independent effects beyond subgroup means are made.

## Compute Feasibility
- All calculations use `numpy`, `scipy`, and `statsmodels` (CPU‑only).  
- Expected study count ≤ 100 → Dataframe size < 10 MB; memory use < 200 MB.  
- End‑to‑end runtime on GitHub Actions ≈ 4 min (well within 6 h limit).  

## Decision Rationale
- **Hedges’ g** chosen for small‑sample bias correction.  
- **Random‑effects** as primary model because mindfulness interventions differ in dosage, modality, and therapist training.  
- **Delivery‑format tagging** mandated by Constitution Principle VII to directly test the caregiver‑mediated hypothesis.  
- **Bonferroni** correction ensures family‑wise error control across multiple subgroup families.  

---
