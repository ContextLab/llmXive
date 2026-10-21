# Implementation Plan: Mindfulness Components and Delivery Formats in ASD Social Skills

**Branch**: `feat/mindfulness-asd-meta-analysis` | **Date**: 2026-10-20  
**Spec**: `specs/001-psychology-research/spec.md`  
**Input**: Feature specification for meta‑analysis of mindfulness interventions for children (6‑12) with ASD.

## Summary
Develop a fully reproducible, CI‑runnable pipeline that:

1. Retrieves eligible RCTs from ClinicalTrials.gov and OSF (FR‑001, FR‑002, Constitution VI).  
2. Supplements registry entries with **open‑access** PubMed Central articles to obtain missing means/SDs; if no open‑access full‑text is available, fall back to abstract extraction (FR‑023, FR‑031, updated for open‑access constraint).  
3. Cleans and standardizes records, extracting intervention components, delivery format, social‑skill domain, **intervention dosage**, **therapist training level**, **baseline severity**, and **risk‑of‑bias rating** (`rob_rating`) (FR‑003, FR‑010, FR‑016, FR‑021, FR‑027, new moderators).  
4. Computes Hedges’ g with small‑sample correction; when baseline means/SDs are available, compute change‑score g; otherwise compute post‑score g using a **sensitivity analysis** over assumed pre‑post correlations r = 0.3, 0.5, 0.7 and report the range (FR‑004, FR‑026, FR‑033, scientific_soundness‑cb3b5961).  
5. Combines multi‑arm studies using Cochrane’s inverse‑variance weighting (FR‑008, FR‑018).  
6. Performs **pre‑specified random‑effects meta‑analysis** using REML estimator and Hartung–Knapp adjustment for **all** analyses, regardless of I² (methodology‑80dd5ee8).  
7. Conducts subgroup analyses for mindfulness components, delivery formats, social‑skill domains, follow‑up duration, and the newly extracted moderators (dosage, therapist training, baseline severity) (FR‑016, FR‑010, FR‑011, FR‑012, methodology‑f767a413).  
8. Executes **power calculations** for each subgroup using a range of plausible effect sizes (g = 0.3, 0.5, 0.6) and reports the required number of studies for each scenario (methodology‑f1ea8fca, scientific_soundness‑d8a28d8d).  
9. Generates forest and funnel plots, running Egger’s test **only if N ≥ 10** (FR‑006).  
10. Validates all intermediate files against JSON‑Schema contracts (FR‑007) and records SHA‑256 checksums for reproducibility (Constitution III, V).  

All steps run on the CPU‑only GitHub Actions free tier; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `requests`, `jsonschema`, `pyyaml`, `biopython` (Entrez)  
- **Storage**: CSV/JSON files under `data/` (`raw/`, `processed/`, `results/`)  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Constraints**: CPU‑first; all libraries have pure‑Python wheels and run within the resource limits.  

## Constitution Check
| Principle | Requirement | Plan Mapping |
|-----------|-------------|--------------|
| **I. Reproducibility** | Deterministic scripts, fixed seeds, identical hashes on fresh runs | All scripts use a central `constants.py` with seeded RNG; `run_pipeline.py` writes SHA‑256 files after each stage. |
| **II. Verified Accuracy** | Registry URLs and DOIs must be verified | `collector.py` validates DOIs via Crossref API and registry URLs via HTTP HEAD; results stored in `metadata/registry_log.json`. |
| **III. Data Hygiene** | Checksums, no in‑place mutation | `utils/checksum.py` creates `*.sha256`; raw files are never overwritten. |
| **IV. Single Source of Truth** | One data row per figure/statistic | Plots and tables are generated directly from `effect_sizes.csv` and `meta_analysis.json`; each figure/table includes the originating `study_id` reference (added for Constitution I). |
| **V. Versioning Discipline** | Content hashes recorded | CI job updates `state/projects/PROJ-008-psychology-research.yaml` with artifact hashes after each step. |
| **VI. Clinical Trial Registry Integrity** | Only ClinicalTrials.gov & OSF (2015‑2024) | `collector.py` filters by registry and registration date; query strings logged. |
| **VII. Caregiver‑Mediated Delivery Verification** | Tag `delivery_format`; exclude ambiguous | `cleaner.py` enforces non‑null `delivery_format`; ambiguous records flagged `abstract_only=True` and handled via sensitivity analysis (methodology‑abf95ff3). |
| **SC‑001** | Identical SHA‑256 hashes for `cleaned_studies.csv` & `excluded_studies.log` | Checksums generated and compared across two independent CI runs. |
| **SC‑002** | Hedges’ g matches metafor R benchmark | Unit test compares a five‑study benchmark against metafor‑generated values within tolerance. |
| **SC‑003** | Forest & funnel plot PNG checksums match synthetic dataset | Synthetic fixture with ≥10 studies is used in CI; generated PNG SHA‑256 compared to stored reference. |
| **SC‑004** | `rob_rating` column present with valid categories | `cleaner.py` extracts RoB2 rating; schema enforces enum `low`, `some concerns`, `high`. |
| **SC‑005** | Full pipeline reproducible on fresh runner | Single `make run` (or `python run_pipeline.py`) executes end‑to‑end on a clean runner. |
| **SC‑006** | Power analysis report includes required number of studies per subgroup | `meta_analysis.py` outputs `power_report.json` with required study counts for g = 0.3, 0.5, 0.6 per subgroup. |

## Project Structure
```text
code/
├── data/
│   ├── collector.py          # FR‑001, FR‑002, DOI/URL validation, open‑access PubMed Central handling
│   ├── pubmed_fetcher.py     # Retrieves missing outcome stats from PubMed Central; abstracts as fallback
│   └── cleaner.py            # FR‑003, FR‑008, FR‑009, FR‑010, FR‑016, FR‑021, FR‑027, FR‑028, new moderators, abstract‑only flag handling
├── analysis/
│   ├── effect_sizes.py       # FR‑004, FR‑013, FR‑024, r‑sensitivity analysis
│   └── meta_analysis.py      # FR‑005, FR‑011, FR‑012, FR‑014, FR‑019, FR‑022, FR‑030, pre‑specified random‑effects model
├── viz/
│   └── plotting.py           # FR‑006, conditional funnel/Egger
├── utils/
│   ├── validation.py         # FR‑007 (jsonschema)
│   └── checksum.py           # Constitution III
├── config/
│   └── constants.py          # seeds, thresholds, correlation values for sensitivity
└── run_pipeline.py           # orchestrates all phases, writes checksums
tests/
├── unit/
│   ├── test_effect_sizes.py
│   └── test_meta_analysis.py
├── integration/
│   └── test_end_to_end.py    # runs pipeline on a deterministic tiny sample
└── contract/
    └── test_schemas.py       # validates CSV/JSON against contracts
data/
├── raw/                       # immutable API downloads, PubMed Central XML
├── processed/
│   ├── cleaned_studies.csv
│   └── effect_sizes.csv
├── results/
│   ├── meta_analysis.json
│   └── plots/
│       ├── forest.png
│       └── funnel.png   # only if N ≥ 10
└── metadata/
    ├── registry_log.json
    ├── pubmed_log.json
    └── rob_log.json
contracts/
├── cleaned_study.schema.yaml
├── effect_size.schema.yaml
└── study.schema.yaml
docs/
└── quickstart.md
```

## Implementation Phases & Tasks (FR/SC Coverage)

| Phase | Tasks | FR / SC IDs addressed |
|-------|-------|------------------------|
| **Phase 0 – Foundations** | • Create `contracts/cleaned_study.schema.yaml` & `contracts/effect_size.schema.yaml`.<br>• Implement `utils/validation.py` (jsonschema).<br>• Implement `utils/checksum.py`. | FR‑007, SC‑001, SC‑005 |
| **Phase 1 – Data Collection (US1)** | • `collector.py` queries ClinicalTrials.gov & OSF with exponential backoff (FR‑001, FR‑002).<br>• Extracts DOI & validates via Crossref (FR‑015, Constitution II).<br>• Stores raw JSON snapshots in `data/raw/`.<br>• Calls `pubmed_fetcher.py` to retrieve **open‑access** full‑text outcome stats via PubMed Central; if unavailable, extracts statistics from abstracts (FR‑023, FR‑031, open‑access constraint).<br>• Logs query strings, timestamps, DOI/URL status in `metadata/registry_log.json`. | FR‑001, FR‑002, FR‑015, FR‑023, FR‑031, SC‑001 |
| **Phase 2 – Cleaning & Tagging** | • `cleaner.py` loads raw data, filters by age (6‑12) and ASD diagnosis.<br>• Keeps only RCTs (`design == 'rct'`); logs quasi‑experimental records for sensitivity analysis (FR‑017, FR‑028).<br>• Extracts intervention components via regex (FR‑003).<br>• Tags `delivery_format` (FR‑016, Constitution VII).<br>• Tags `social_skill_domain` (FR‑010).<br>• Extracts **dosage**, **therapist training level**, **baseline severity** (new moderators).<br>• Extracts RoB2 rating into `rob_rating` (FR‑021).<br>• Handles multi‑arm studies using Cochrane inverse‑variance weighting (FR‑008, FR‑018).<br>• Flags records where component/delivery extraction relied on abstract only (`abstract_only=True`) and **includes** them in primary analyses; a separate sensitivity analysis will compare results with and without these flagged records (methodology‑abf95ff3).<br>• Writes `cleaned_studies.csv` and `excluded_studies.log`. | FR‑003, FR‑008, FR‑009, FR‑010, FR‑016, FR‑017, FR‑018, FR‑020, FR‑021, FR‑027, FR‑028, SC‑004 |
| **Phase 3 – Effect‑Size Computation** | • `effect_sizes.py` computes Hedges’ g with small‑sample correction (FR‑004).<br>• Uses change‑score data when pre‑ and post‑means/SDs are present; otherwise computes post‑score g **for each assumed correlation (r = 0.3, 0.5, 0.7)** and records the range; reports sensitivity (methodology‑dc72a3a8, scientific_soundness‑cb3b5961).<br>• Retains `n_treatment`, `n_control` (FR‑024).<br>• Validates rows against `effect_size.schema.yaml` (FR‑007).<br>• Outputs `effect_sizes.csv`. | FR‑004, FR‑013, FR‑024, FR‑026, FR‑033, FR‑007, SC‑002 |
| **Phase 4 – Meta‑Analysis & Subgroups** | • `meta_analysis.py` **always** uses random‑effects REML with Hartung‑Knapp (pre‑specified; methodology‑80dd5ee8).<br>• Computes Q, I², τ².<br>• Performs subgroup analyses for (a) mindfulness component, (b) delivery format, (c) social‑skill domain, (d) follow‑up duration, and (e) additional moderators (dosage, therapist training, baseline severity) (FR‑011, FR‑012, FR‑016, methodology‑f767a413).<br>• Applies Bonferroni correction across the four subgroup families (multiple‑comparison control).<br>• Executes **power analysis** for each subgroup using **g = 0.3, 0.5, 0.6**; reports required number of studies for each scenario (methodology‑f1ea8fca, scientific_soundness‑d8a28d8d).<br>• Incorporates `rob_rating` as a weighting factor and provides sensitivity analyses stratified by RoB2 categories (FR‑030).<br>• If total N < 10, skips meta‑regression and notes descriptive synthesis (FR‑014).<br>• Saves results to `meta_analysis.json` and `power_report.json`. | FR‑005, FR‑011, FR‑012, FR‑014, FR‑019, FR‑022, FR‑030, SC‑006 |
| **Phase 5 – Visualization** | • `plotting.py` creates forest plot with study‑specific CIs and pooled diamond (FR‑006).<br>• Generates funnel plot and runs Egger’s test only when N ≥ 10 (FR‑006).<br>• Saves PNGs to `results/plots/`. | FR‑006, SC‑003 |
| **Phase 6 – Reporting & Integrity** | • `run_pipeline.py` orchestrates Phases 1‑5, writes SHA‑256 checksums for every artifact, updates `state/projects/PROJ-008-psychology-research.yaml` (Constitution III, V).<br>• Generates a concise `report.md` summarizing results, power calculations, and any conditional branches taken; each figure/table includes the originating `study_id` reference (Constitution I). | Constitution III, V, SC‑001, SC‑005 |
| **Phase 7 – Testing** | • Unit tests for each module.<br>• Integration test runs full pipeline on a deterministic subset (first 5 studies) to verify reproducibility.<br>• Contract tests validate CSV/JSON against schemas.<br>• Synthetic fixture `tests/fixtures/multi_arm_split.yaml` verifies multi‑arm combination logic (FR‑008). | FR‑007, SC‑001, SC‑002, SC‑003, SC‑004 |

## Rigor & Risk Mitigation
- **Multiple Comparisons**: Bonferroni correction across four subgroup families.  
- **Power / Sample‑Size**: Subgroup‑specific power analysis for g = 0.3, 0.5, 0.6 (FR‑019) reported; if N < 10, descriptive synthesis replaces meta‑regression (SC‑006).  
- **Publication Bias**: Funnel plot & Egger’s test conditioned on N ≥ 10 (FR‑006).  
- **Collinearity**: Delivery format and component tags are orthogonal by definition; no regression claims of independent effects beyond subgroup means.  
- **Measurement Validity**: Only studies reporting validated social‑skill instruments (e.g., SRS‑2, VABS) are retained; instrument name stored for traceability.  
- **Risk‑of‑Bias**: RoB2 rating extracted into `rob_rating` and used as a moderator; low‑quality studies can be down‑weighted in sensitivity checks (FR‑030).  
- **Open‑Access Data**: All PubMed retrievals are limited to PubMed Central open‑access articles; otherwise abstract extraction is used, ensuring CI can download all required content.  

---

