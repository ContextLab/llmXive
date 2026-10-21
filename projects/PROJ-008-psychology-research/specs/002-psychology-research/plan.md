# Implementation Plan: Mindfulness Components and Delivery Formats in ASD Social Skills

**Branch**: `feat/mindfulness-asd-meta-analysis` | **Date**: 2026-10-20  
**Spec**: `specs/001-psychology-research/spec.md`  
**Input**: Feature specification for meta‑analysis of mindfulness interventions for children (6‑12) with ASD.

## Summary
Develop a fully reproducible CI‑runnable pipeline that:

1. Programmatically retrieves eligible RCTs from ClinicalTrials.gov and OSF (FR‑001, FR‑002, Constitution VI).  
2. Supplements registry records with PubMed article metadata to obtain means/SDs when not present in registries (addresses data_resources‑3159ae52).  
3. Cleans and standardizes study records, extracting intervention components, delivery format, social‑skill domains, risk‑of‑bias (RoB2) ratings, and DOI information (FR‑003, FR‑008, FR‑009, FR‑010, FR‑007, methodology‑2d4e176d).  
4. Computes Hedges’ g with small‑sample correction (FR‑004, FR‑013), **preferentially using change‑score data** (pre‑post differences). When only post‑intervention statistics are available, applies a baseline‑adjusted conversion using an assumed pre‑post correlation (r = 0.5) and records this limitation (addresses scientific_soundness‑458296b4).  
5. Performs meta‑analysis with **REML estimator and Hartung‑Knapp adjustment** (methodology‑75f57409). Heterogeneity statistics guide model choice (fixed‑effects if I² ≤ 50 %; otherwise random‑effects).  
6. Generates forest and funnel plots, conducting Egger’s test when appropriate (FR‑006).  
7. Validates all intermediate files against JSON‑Schema contracts (FR‑007) and records SHA‑256 checksums (Constitution III, V).  

All steps are deterministic, logged, and executed on the CPU‑only GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `requests`, `jsonschema`, `pyyaml`, `biopython` (for Entrez PubMed queries)  
- **Storage**: CSV/JSON files under `data/` (`raw/`, `processed/`, `results/`)  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Constraints**: CPU‑only; all libraries run on the runner without GPU.  

## Constitution Check
| Principle | Requirement | Plan Mapping |
|-----------|-------------|--------------|
| **I. Reproducibility** | Fresh runner, deterministic scripts, fixed seeds | All scripts under `code/` are deterministic; seeds fixed in `code/config/constants.py`. |
| **II. Verified Accuracy** | Registry URLs and DOIs must be verified | Registry query strings, timestamps, **DOI validation via Crossref** are logged in `data/metadata/registry_log.json`. |
| **III. Data Hygiene** | Checksums, no in‑place mutation | After each stage a SHA‑256 checksum file (`*.sha256`) is written; raw files never overwritten. |
| **IV. Single Source of Truth** | One data row per figure/statistic | Plots reference `study_id`; tables are generated directly from `effect_sizes.csv`. |
| **V. Versioning Discipline** | Content hashes for all artifacts | CI job records hashes in `state/projects/PROJ-008-psychology-research.yaml` after each step. |
| **VI. Clinical Trial Registry Integrity** | Only ClinicalTrials.gov & OSF (2015‑2024) | `collector.py` filters by registry and registration date; query strings are logged. |
| **VII. Caregiver‑Mediated Delivery Verification** | Tag `delivery_format`; exclude ambiguous | `cleaner.py` enforces a non‑null `delivery_format` enum; ambiguous records are flagged and omitted from primary subgroup analysis. |
| **SC‑005** | Reproducibility on fresh runner | Entire pipeline is invoked via a single `make run` command that works on a clean runner. |

## Project Structure
```text
code/
├── data/
│   ├── collector.py      # FR‑001, FR‑002, rate‑limiting (FR‑002), DOI extraction & validation
│   ├── pubmed_fetcher.py # New: queries PubMed for full‑text outcome data
│   └── cleaner.py        # FR‑003, FR‑008, FR‑009, FR‑010, FR‑007, RoB extraction, DOI logging
├── analysis/
│   ├── effect_sizes.py   # FR‑004, FR‑013, retains n_treatment & n_control (addressing d39c5e07)
│   └── meta_analysis.py  # FR‑005, FR‑011, FR‑012, FR‑014, uses REML+Hartung‑Knapp (methodology‑75f57409)
├── viz/
│   └── plotting.py       # FR‑006
├── utils/
│   ├── validation.py     # FR‑007 (schema enforcement)
│   └── checksum.py       # Constitution III
├── config/
│   └── constants.py      # seeds, thresholds
└── run_pipeline.py       # orchestrates all steps, logs checksums
tests/
├── unit/
│   ├── test_effect_sizes.py
│   └── test_meta_analysis.py
├── integration/
│   └── test_end_to_end.py   # runs full pipeline on a tiny sample (first 5 studies)
└── contract/
    └── test_schemas.py      # validates CSV/JSON against contracts
data/
├── raw/                     # immutable API downloads + PubMed XML
├── processed/
│   ├── cleaned_studies.csv
│   └── effect_sizes.csv
├── results/
│   ├── meta_analysis.json
│   └── plots/
│       ├── forest.png
│       └── funnel.png   # only if N ≥ 10
└── metadata/
    ├── registry_log.json   # query strings, timestamps, DOI validation status, and checksums
    ├── pubmed_log.json     # PubMed query logs and extracted outcome statistics
    └── rob_log.json        # Risk‑of‑bias ratings per study
contracts/
├── cleaned_study.schema.yaml
└── effect_size.schema.yaml
docs/
└── quickstart.md
```

## Implementation Phases & Tasks
| Phase | Tasks (covers FR / SC) |
|-------|------------------------|
| **Phase 0 – Foundations** | • Create `contracts/cleaned_study.schema.yaml` & `contracts/effect_size.schema.yaml` (FR‑007).<br>• Implement `utils/validation.py` using `jsonschema`.<br>• Add `utils/checksum.py` for SHA‑256 generation. |
| **Phase 1 – Data Collection (US1)** | • `collector.py` queries ClinicalTrials.gov API (v2) and OSF API with exponential backoff (FR‑001, FR‑002).<br>• Extracts DOI from registry metadata and validates via Crossref (addresses plan_consistency‑a02b0bf1).<br>• Stores raw JSON in `data/raw/registry_snapshot_YYYYMMDD.json`.<br>• Calls `pubmed_fetcher.py` to retrieve associated PubMed records and extracts means/SDs when missing from registries (data_resources‑3159ae52).<br>• Logs query strings, timestamps, DOIs, and response hashes in `metadata/registry_log.json`. |
| **Phase 2 – Cleaning & Tagging** | • `cleaner.py` loads raw JSON, filters by age (6‑12) and ASD diagnosis.<br>• **Design filter**: retains only RCTs (`design == 'rct'`); quasi‑experimental studies are logged for a **sensitivity analysis** (methodology‑588d7186).<br>• Extracts intervention components via regex (FR‑003) **and** flags records where extraction relied solely on abstracts; such records are marked `abstract_only=True` and **excluded from all subgroup analyses** (methodology‑0074e207).<br>• Tags `delivery_format` (caregiver‑mediated, child‑led, hybrid, unknown) (FR‑008, VII).<br>• Tags `social_skill_domain` (communication, peer_interaction, emotional_regulation, adaptive_behavior, unknown) (FR‑010).<br>• Extracts RoB2 ratings from trial protocols or associated publications; stores in `metadata/rob_log.json` (methodology‑2d4e176d).<br>• Handles multi‑arm studies **by combining** treatment arms (weighted means/SDs) rather than splitting controls, following Cochrane guidance (methodology‑603f7e57).<br>• Falls back to abstract‑only extraction when full‑text OCR unavailable (FR‑009).<br>• Writes `cleaned_studies.csv` and `excluded_studies.log`. |
| **Phase 3 – Effect‑Size Computation** | • `effect_sizes.py` computes Hedges’ g with small‑sample correction (FR‑004, FR‑013).<br>• **Primary**: uses change‑score data (pre‑post differences) when both baseline and post‑intervention means/SDs are present; otherwise, uses post‑scores **adjusted for baseline imbalance** using an assumed pre‑post correlation (r = 0.5) and notes the limitation (addresses scientific_soundness‑458296b4).<br>• Calculates standard error and 95 % CI.<br>• **Retains** `n_treatment` and `n_control` columns in the output (addressing d39c5e07).<br>• Validates rows against `effect_size.schema.yaml` (FR‑007).<br>• Outputs `effect_sizes.csv`. |
| **Phase 4 – Meta‑Analysis & Subgroups** | • `meta_analysis.py` calculates Q, I², selects **REML** estimator with **Hartung‑Knapp** adjustment (methodology‑75f57409).<br>• Performs subgroup analyses for (a) mindfulness component, (b) delivery format, (c) social‑skill domain, (d) follow‑up duration (FR‑011, FR‑012).<br>• Applies Bonferroni correction across the four subgroup families.<br>• If total N < 10, skips meta‑regression, funnel plot, Egger’s test and records a descriptive synthesis note (FR‑014).<br>• Includes **risk‑of‑bias rating** as a moderator in sensitivity analyses.<br>• Saves results to `meta_analysis.json`. |
| **Phase 5 – Visualization** | • `plotting.py` creates forest plot with study‑specific CIs and pooled diamond (FR‑006).<br>• Generates funnel plot and runs Egger’s test only when N ≥ 10 (FR‑006).<br>• Saves PNGs to `results/plots/`. |
| **Phase 6 – Reporting & Integrity** | • `run_pipeline.py` orchestrates phases 1‑5, writes SHA‑256 checksums for every artifact, and updates `state/projects/PROJ-008-psychology-research.yaml` with hashes (Constitution III, V). |
| **Phase 7 – Testing** | • Unit tests for each module.<br>• Integration test (`test_end_to_end.py`) runs the full pipeline on a deterministic sample of multiple studies to verify reproducibility.<br>• Contract tests validate CSV/JSON against schemas. |

## Rigor & Risk Mitigation
- **Power / Sample‑Size**: Subgroup‑specific detectable effect sizes are reported (methodology‑df176453). If eligible study count N < 10, pipeline switches to descriptive synthesis and notes limited power (SC‑005).  
- **Multiple Comparisons**: Bonferroni correction applied to all subgroup p‑values.  
- **Publication Bias**: Funnel plot & Egger’s test only when total included studies **N ≥ 10** (FR‑006).  
- **Collinearity**: Delivery format and component tags are orthogonal by definition; no regression claims of independent effects beyond subgroup means.  
- **Measurement Validity**: Only studies reporting validated social‑skill instruments (e.g., SRS‑2, VABS) are included; instrument name stored in `cleaned_studies.csv`.  
- **Risk‑of‑Bias**: RoB2 ratings extracted and used as a moderator; low‑quality studies can be down‑weighted in sensitivity checks.  

---



## projects/PROJ-008-psychology-research/specs/002-psychology-research/research.md
# Research: Mindfulness Components and Delivery Formats in ASD Social Skills

## Research Question
What is the efficacy of mindfulness‑based interventions for improving social skills in children aged 6‑12 with Autism Spectrum Disorder (ASD), and how do effects vary by (a) mindfulness component (breathing, body‑scan, mindful movement, combined) and (b) delivery format (caregiver‑mediated vs. child‑led)?

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
| PubMed (Entrez) | https://www.ncbi.nlm.nih.gov/ | `biopython` Entrez API | Retrieves full‑text articles to obtain means/SDs when not present in registries (addresses data_resources‑3159ae52) |

All sources are openly downloadable; no credentials required (Constitution VI). Registry records are archived verbatim under `data/raw/` and checksummed. PubMed queries are logged in `data/metadata/pubmed_log.json`.

## Inclusion / Exclusion Criteria
- **Population**: Children up to 12 years old, confirmed ASD diagnosis (DSM‑5 or ICD‑10).  
- **Design**: **Only randomized controlled trials (RCTs)** are included (`design == 'rct'`). Any quasi‑experimental studies discovered are logged for a **sensitivity analysis** but are excluded from the primary meta‑analysis (addresses methodology‑588d7186).  
- **Intervention**: Must contain at least one core mindfulness component (breathing, body‑scan, mindful movement).  
- **Outcome**: Must report a validated social‑skill measure (e.g., Social Responsiveness Scale‑2, Vineland Adaptive Behavior Scales) and provide sufficient summary statistics (means, SDs, Ns) either in the registry entry or in the associated journal article (addressing data_resources‑3159ae52).  
- **Registration**: Listed in ClinicalTrials.gov or OSF, registration date between 2015‑01‑01 and 2024‑12‑31.  
- **Exclusions**: Age outside 6‑12, no control group, no social‑skill outcome, duplicate publications, ambiguous delivery format, or missing outcome statistics that cannot be retrieved from PubMed. Records where component or delivery‑format extraction relied solely on abstracts are flagged `abstract_only=True` and **excluded from all subgroup analyses** (methodology‑0074e207).  

## Methodological Rigor

### Effect‑Size Computation
- **Metric**: Hedges’ g with small‑sample correction (J = 1 − 3/(4N − 9)).  
- **Preferred Input**: **Change‑score data** (pre‑post differences) when both baseline and post‑intervention means/SDs are available.  
- **Fallback**: If change scores are unavailable, compute Hedges’ g from post‑intervention means/SDs **adjusted for baseline imbalance** using an assumed pre‑post correlation (r = 0.5) and note the limitation (addresses scientific_soundness‑458296b4).  
- **SE & CI**: Standard error computed per conventional formulas; 95 % CI via normal approximation.  

### Risk‑of‑Bias Assessment
- Extract RoB2 ratings from trial protocols or associated publications (methodology‑2d4e176d).  
- Store ratings in `metadata/rob_log.json`.  
- Use RoB rating as a moderator in sensitivity analyses and as a weight adjustment if needed.

### Meta‑Analysis Model
- Compute Cochran’s Q and I².  
- **Model Selection**: Fixed‑effects if I² ≤ 50 %; otherwise random‑effects using **REML** estimator with **Hartung‑Knapp** adjustment (methodology‑75f57409).  
- Report both models for sensitivity (FR‑005).  

### Subgroup Analyses & Power
- **Component**: breathing, body‑scan, mindful movement, combined.  
- **Delivery Format**: caregiver‑mediated, child‑led, hybrid.  
- **Social‑Skill Domain**: communication, peer interaction, emotional regulation, adaptive behavior.  
- **Follow‑up**: ≤ 3 months vs. > 3 months.  
- **Power**: Assuming a moderate sample size per study, the overall analysis is powered to detect a medium pooled effect size at [deferred] power. For subgroups (with a typical moderate number of studies), detectable g rises substantially; this limitation is reported (methodology‑df176453). Subgroup families with fewer than 15 studies are **not pursued** to avoid severe under‑power.  

### Publication Bias
- Funnel plot & Egger’s regression test only if total included studies **N ≥ 10** (FR‑006).  
- Otherwise, report “insufficient studies for bias assessment”.

### Multi‑Arm Study Handling
- Combine multiple treatment arms into a single arm (aggregating means/SDs weighted by sample size) per Cochrane guidance (methodology‑603f7e57).  
- Record the combination rationale in `metadata/multi_arm_log.json`.

### Component & Delivery‑Format Extraction
- Use curated regex dictionary; each match receives a confidence score (0‑1).  
- Records with confidence < 0.7 or where extraction relied solely on abstracts are flagged `abstract_only=True` and **excluded from subgroup analyses** (methodology‑0074e207).

### DOI Verification
- Extract DOI from registry metadata; validate via Crossref API.  
- Log DOI verification status in `metadata/registry_log.json` (plan_consistency‑a02b0bf1).

### Power & Sample‑Size Considerations
- Overall detectable g is of moderate magnitude, based on a sample of several dozen observations.  
- Subgroup detectable g at a moderate magnitude (with a modest sample size on the order of tens).  
- If final eligible N < 10, pipeline switches to descriptive synthesis and notes limited power (SC‑005).

## Compute Feasibility
- All calculations use `numpy`, `scipy`, and `statsmodels` (CPU‑only).  
- Expected study count ≤ 100 → Dataframe size < 10 MB; memory use < 200 MB.  
- End‑to‑end runtime on GitHub Actions [deferred] (well within 6 h limit).

## Decision Rationale
- **Hedges’ g** chosen for small‑sample bias correction.  
- **Random‑effects (REML + Hartung‑Knapp)** as primary model because mindfulness interventions differ in dosage, modality, and therapist training.  
- **Delivery‑format tagging** mandated by Constitution VII to directly test the caregiver‑mediated hypothesis.  
- **Bonferroni** correction ensures family‑wise error control across multiple subgroup families.  

---



## projects/PROJ-008-psychology-research/specs/002-psychology-research/contracts/cleaned_study.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Cleaned Study Schema"
type: "object"
required:
  - "study_id"
  - "registry"
  - "age_min"
  - "age_max"
  - "n_treatment"
  - "n_control"
  - "delivery_format"
  - "included"
  - "social_skill_domain"
properties:
  study_id:
    type: "string"
    pattern: "^(ctgov|osf)_.*$"
  registry:
    type: "string"
    enum: ["clinicaltrials.gov", "osf.io"]
  age_min:
    type: "integer"
    minimum: 6
    maximum: 12
  age_max:
    type: "integer"
    minimum: 6
    maximum: 12
  n_treatment:
    type: "integer"
    minimum: 1
  n_control:
    type: "integer"
    minimum: 1
  delivery_format:
    type: "string"
    enum: ["caregiver_mediated", "child_led", "hybrid", "unknown"]
  social_skill_domain:
    type: "string"
    enum: ["communication", "peer_interaction", "emotional_regulation", "adaptive_behavior", "unknown"]
  mean_treatment:
    type: "number"
  sd_treatment:
    type: "number"
    minimum: 0
  mean_control:
    type: "number"
  sd_control:
    type: "number"
    minimum: 0
  follow_up_months:
    type: "integer"
    minimum: 0
  included:
    type: "boolean"
  exclusion_reason:
    type: "string"
  abstract_only:
    type: "boolean"
  doi:
    type: "string"
  retrieval_timestamp:
    type: "string"
    format: "date-time"
additionalProperties: false