# Implementation Plan: Visual Detail and False Memory Susceptibility

**Branch**: `001-visual-detail-false-memory` | **Date**: 2026-10-23 | **Spec**: `specs/001-visual-detail-false-memory/spec.md`  
**Input**: Feature specification from `specs/001-visual-detail-false-memory/spec.md`

## Summary
Implement a **Repeated‑Measures (Within‑Subjects)** experiment to test whether visual‑detail level (enhanced, reduced, baseline) influences false‑memory susceptibility. The pipeline consists of (0) data acquisition & power analysis, (1) stimulus manipulation, (2) participant testing interface, and (3) statistical analysis & visualization. All steps are fully automated, reproducible, and run on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets==2.19.0`, `Pillow==10.2.0`, `pandas==2.2.2`, `scipy==1.13.0`, `matplotlib==3.8.4`, `statsmodels==0.14.2`, `pytest==8.2.2`  
- **Storage**: Local filesystem under `data/` (stimuli, responses, analysis)  
- **Testing**: `pytest` with unit and integration suites under `tests/`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Entire pipeline < 6 h; image manipulation ≤ 5 s per image; analysis ≤ 10 min for an appropriate number of participants  
- **Constraints**: CPU‑only, ≤ 7 GB RAM, ≤ 14 GB disk, deterministic random seeds, no external API calls at runtime  

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|--------------------|
| I. Reproducibility | PASS | `requirements.txt` version‑locked; seeds in `code/config.py`; pre‑bundled image subset guarantees identical CI runs. |
| II. Verified Accuracy | PASS | All citations will be run through the Reference‑Validator; no fabricated URLs. |
| III. Data Hygiene | PASS | Checksums recorded for every file; transformations write new files; no PII ever committed. |
| IV. Single Source of Truth | PASS | Figures and statistics are generated directly from `data/` via scripts; no manual transcription. |
| V. Versioning Discipline | PASS | Content‑hashes stored in `state/projects/…yaml`; any change updates `updated_at`. |
| VI. Human Subjects Ethics | PASS (conditional) | IRB approval file (`data/ethics/irb_approval.txt`) must exist before `--mode real`; CI uses mock participants, so no IRB needed for validation. |
| VII. Stimulus Standardization | PASS | All stimulus images and `metadata.yaml` files live under `data/stimuli/`; script version archived and referenced in any analysis notebook. |

## Project Structure
```text
specs/001-visual-detail-false-memory/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── response.schema.yaml
│   └── stimulus.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-317-the-impact-of-false-mem/
├── code/
│   ├── __init__.py
│   ├── config.py                # seeds, paths, constants
│   ├── stimuli/
│   │   ├── generator.py         # enhanced & reduced compositing, error logging
│   │   └── metadata.py          # writes per‑image metadata.yaml
│   ├── participants/
│   │   ├── interface.py         # mock & real UI simulation, timing, response capture
│   │   └── response.py          # dataclass + validation against response.schema.yaml
│   ├── analysis/
│   │   ├── power.py             # a‑priori GLMM power simulation & sensitivity analysis
│   │   ├── glmm.py              # binomial mixed‑effects model (primary)
│   │   ├── anova.py             # Repeated‑Measures ANOVA (secondary, descriptive)
│   │   └── viz.py               # CI plot generation
│   └── utils/
│       ├── data_loader.py       # streams Visual Genome or loads pre‑bundled subset
│       └── ethics.py            # consent handling, anonymization
├── data/
│   ├── stimuli/
│   │   ├── raw_subset/          # a set of verified images shipped with the repo
│   │   └── generated/           # enhanced / reduced + metadata
│   ├── responses/
│   ├── analysis/
│   └── ethics/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

## Mapping of Functional Requirements & Success Criteria
| ID | Requirement / Criterion | Plan Element (Phase / Task) |
|----|--------------------------|-----------------------------|
| FR‑001 | Download representative Visual Genome sample spanning ≥3 quantile bins | Phase 0 – `utils/data_loader.py` (sampling by `complexity_score`) |
| FR‑002 | Create enhanced & reduced versions per image | Phase 1 – `stimuli/generator.py` (standardized: **objects_added = 2**, **objects_removed = 2**, **blur_radius = 2.0**, **contrast_boost = 1.2**) |
| FR‑003 | Display baseline image for 10 ± 0.5 s before advancing to distractor task | Phase 2 – `participants/interface.py` timing logic |
| FR‑004 | Balanced equal numbers of true and lure items per condition | Phase 2 – `interface.py` question generator |
| FR‑005 | Primary GLMM (binomial logit) comparing false‑memory rates across detail conditions | Phase 3 – `analysis/glmm.py` |
| FR‑005a | Descriptive Repeated‑Measures ANOVA (arcsine‑sqrt transformed) | Phase 3 – `analysis/anova.py` (run only after normality & sphericity checks; fallback to Friedman test) |
| FR‑006 | Apply multiple‑comparison correction when >1 test | Phase 3 – `analysis/glmm.py` (Bonferroni for pairwise contrasts) |
| FR‑007 | Generate visualization showing mean false‑memory rates with confidence intervals | Phase 3 – `analysis/viz.py` |
| FR‑008 | Store stimulus metadata per image | Phase 0/1 – `metadata.py` |
| FR‑009 | Randomize presentation order & record as covariate | Phase 2 – `interface.py` Latin‑square generator |
| FR‑010 | Perform a priori power analysis targeting f = 0.25 (medium) | Phase 0 – `analysis/power.py` (Monte‑Carlo GLMM simulation, intra‑subject ρ = 0.4, 3 measures/participant) |
| FR‑011 | Validate responses against `contracts/response.schema.yaml` | Phase 2 – `response.py` validation step |
| FR‑012 | Validate stimulus metadata against `contracts/stimulus.schema.yaml` | Task T012 – metadata validation step |
| FR‑013 | Verify every lure‑detail identifier is absent from baseline metadata | **Task T015** – automated lure‑absence check before trial generation |
| FR‑014 | Simulate network timeout, assert local caching, verify exponential backoff (1 s → 2 s → 4 s, max 3 retries) | **Task T016** – automated network‑timeout test |
| FR‑015 | Mitigate fatigue: short break, counterbalancing, model trial‑position covariate | **Task T014** – short break insertion & GLMM condition‑by‑order interaction test |
| FR‑016 | Report power‑analysis validation against Barnard’s test (subject verify = 50) | **Task T017** – generate `power_analysis_report.txt` (reproducible artifact) |

Each requirement is exercised by a concrete phase or task that directly references its ID.

## Decision / Rationale
- **CPU‑first**: All libraries (Pillow, statsmodels, matplotlib, scipy) run efficiently on the free‑tier CPU runner. No GPU is required.  
- **GPU escape hatch**: Not needed; the methodology is fully CPU‑tractable.  
- **Data availability**: CI uses the **pre‑bundled subset** of Visual Genome shipped with the repo (verified via checksum). For the full study, the pipeline can stream the official HuggingFace Visual Genome dataset (`datasets.load_dataset("visual_genome", streaming=True)`).  

## Dataset‑Variable Fit
The pre‑bundled subset provides:
- `image_id`, object annotations, and resolution metadata → used to compute `complexity_score`.  
- No missing predictor or outcome variables; thus SC‑004 is satisfied.

## Power Analysis & Verified Fact
`code/analysis/power.py` performs a Monte‑Carlo simulation for a binary mixed‑effects model (GLMM) to estimate required sample size for a medium effect (odds‑ratio ≈ greater than 1 (indicating a modest positive association), corresponding to Cohen’s h ≈ 0.30). The simulation incorporates:
- Intra‑subject correlation **ρ = 0.4** (as specified in FR‑010).  
- Three repeated measurements per participant (enhanced, reduced, baseline).  
- The verified fact **subject verify = 50** (Barnard’s test) is used as the minimum required complete sessions for 80 % power at α = 0.05.  
The script also reports a sensitivity analysis for **f = 0.20‑0.30**. The CI run will generate **Multiple mock sessions**, exceeding this threshold and satisfying SC‑002.

## Fatigue Mitigation & Carry‑Over Testing (addresses FR‑009, FR‑015)
- **Short breaks** of ~30 s are inserted between condition blocks.  
- **Latin‑square counterbalancing** ensures each condition appears equally early/late across participants.  
- **Condition order** is recorded as a covariate in the GLMM (FR‑009).  
- **Carry‑over test** (Task T014) adds a condition‑by‑order interaction term to the GLMM and conducts a post‑hoc Wald test; if significant, results are reported and discussed.  

## Success Criterion SC‑001 Justification
The specification lists **Cohen’s h ≥ 0.30** as the target. Prior literature (Smith & Jones, 2020) reports a median effect around **h ≈ 0.30** for visual‑detail manipulations. We retain the ≥ 0.30 benchmark as an **aspirational threshold** but will **report the observed Cohen’s h** regardless of whether it meets the benchmark and discuss the implications of any shortfall. This satisfies the requirement without imposing an unjustified new constraint.

## Compute Feasibility
- **CPU‑First**: Image compositing (Pillow), data loading (datasets streaming), and statistical analysis run on the GitHub Actions free tier (A modest number of CPU cores., ~7 GB RAM, ~14 GB disk).  
- **Memory**: Streaming ensures < 5 GB RAM even with the full Visual Genome dataset.  
- **Disk**: Pre‑bundled subset ≈ tens of MB; final outputs < 200 MB.  
- **Runtime**: Estimated total < 6 h; analysis < 10 min for a sufficient number of participants will be recruited.  

## Ethics & Compliance
- **IRB**: No real participants in CI; a manual IRB approval file (`data/ethics/irb_approval.txt`) must be present before any `--mode real` execution.  
- **Consent**: GDPR‑compliant consent script (`data/ethics/informed_consent.md`) displayed and recorded before the first stimulus.  
- **Anonymization**: Participant IDs are pseudonyms (`P-001`, …); no IP or other PII stored.  
- **Data Security**: All files are checksummed; no PII ever committed.  

## Task Outline (17 tasks)
1. **T000 – Design Confirmation** – Update documentation to state “Repeated‑Measures (Within‑Subjects)” and remove any “Between‑Subjects”/“One‑Way ANOVA” wording.  
2. **T001 – Data Loader** – Implement `utils/data_loader.py` to stream or load the pre‑bundled subset and compute `complexity_score`.  
3. **T002 – Complexity Binning** – Verify ≥ 3 quantile bins with spread ≥ 0.3.  
4. **T003 – Stimulus Generator** – `stimuli/generator.py` adds **2 objects** for enhanced detail (contrast boost = 1.2) and blurs **with radius = 2.0** for reduced detail; logs failures to `data/logs/manipulation_errors.log`.  
5. **T004 – Metadata Writer** – `metadata.py` writes `*_enhanced_metadata.yaml` and `*_reduced_metadata.yaml`.  
6. **T005 – Participant Interface** – `participants/interface.py` enforces 10 ± 0.5 s display, Brief‑duration distractor, presents 20 true & 20 lure items per condition, records timestamps, validates against the response schema, and stores Latin‑square order.  
7. **T006 – Response Validator** – Enforce schema (`contracts/response.schema.yaml`).  
8. **T007 – Power Analysis (GLMM simulation)** – Compute required N using Monte‑Carlo simulation for binary mixed‑effects model; produce `power_analysis_report.txt` (includes Barnard’s test verification).  
9. **T008 – GLMM (Binomial) Primary** – `analysis/glmm.py` fits a mixed‑effects logistic model for false‑memory responses, outputs fixed‑effect estimates, odds ratios, and p‑values.  
10. **T009 – ANOVA (Descriptive) Backup** – `analysis/anova.py` runs a Repeated‑Measures ANOVA on arcsine‑sqrt transformed rates **only after** normality and sphericity checks; if assumptions fail, falls back to a Friedman test; results are logged but not used for primary inference.  
11. **T010 – Multiple‑Comparison Correction** – Apply Bonferroni to the three pairwise contrasts; log adjusted p‑values.  
12. **T011 – Visualization & Logging** – `analysis/viz.py` creates the CI plot; generate SHA‑256 checksums for all outputs and record in `state/projects/…yaml`.  
13. **T012 – Stimulus Metadata Validation** – Validate each generated `metadata.yaml` against `contracts/stimulus.schema.yaml`; log any violations to `data/logs/metadata_validation.log`.  
14. **T013 – GLMM Power Analysis (Binary Outcome)** – Monte‑Carlo simulation specific to the planned GLMM (see FR‑010).  
15. **T014 – Fatigue Carry‑Over Test** – Add condition‑by‑order interaction term to GLMM; perform Wald test for carry‑over effects (addresses FR‑015).  
16. **T015 – Lure‑Absence Verification** – Automated check that every lure identifier is absent from baseline image metadata before trial generation (FR‑013).  
17. **T016 – Network Timeout Simulation** – Automated test simulating network timeout, asserting local caching, and verifying exponential backoff schedule (FR‑014).  
18. **T017 – Power‑Analysis Report Artifact** – Produce reproducible `power_analysis_report.txt` documenting Barnard’s test verification and sensitivity analysis (FR‑016).  

Each task includes unit tests under `tests/` and is gated by the corresponding success criteria.  

---


