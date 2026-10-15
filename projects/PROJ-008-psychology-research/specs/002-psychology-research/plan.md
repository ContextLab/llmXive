# Implementation Plan: Mindfulness Components and Delivery Formats in ASD Social Skills

**Branch**: `feat/mindfulness-asd-meta-analysis` | **Date**: 2026-10-14  
**Spec**: `specs/001-psychology-research/spec.md`  
**Input**: Feature specification for meta‑analysis of mindfulness interventions for children (6‑12) with ASD.

## Summary
Implement a fully reproducible, CI‑runnable pipeline that (1) programmatically retrieves eligible RCTs from ClinicalTrials.gov and OSF, (2) extracts standardized variables (population, intervention components, delivery format, social‑skill outcomes, sample sizes), (3) computes Hedges’ g with small‑sample correction, (4) conducts random‑effects meta‑analysis with heterogeneity statistics and prespecified subgroup analyses, and (5) generates forest and funnel plots. All artifacts are validated against JSON‑Schema contracts and hashed for integrity.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `requests`, `jsonschema`, `pyyaml`
- **Storage**: CSV/JSON files under `data/` (`raw/`, `processed/`, `results/`)
- **Testing**: `pytest` (unit, integration, contract validation)
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)
- **Project Type**: research‑pipeline (no web or mobile components)
- **Constraints**: CPU‑only; all libraries run on the runner without GPU.

## Constitution Check
| Principle | Requirement | Plan Mapping |
|-----------|-------------|--------------|
| **I. Reproducibility** | Fresh runner execution, pinned seeds, canonical sources | All scripts under `code/` are deterministic; seeds are fixed in `analysis/meta_analysis.py`; data sources are limited to ClinicalTrials.gov and OSF APIs. |
| **II. Verified Accuracy** | Citations must be verified against primary sources | Registry URLs and DOI references are recorded in `data/metadata/registry_log.json`; each extracted field is linked to the registry record ID. |
| **III. Data Hygiene** | Checksums, no in‑place modification | After each pipeline stage a SHA‑256 checksum file (`*.sha256`) is written; raw files are never overwritten. |
| **IV. Single Source of Truth** | Each figure/statistic traces to one data row | Plots use the `study_id` column as the sole identifier; tables are generated directly from `effect_sizes.csv`. |
| **V. Versioning Discipline** | Content hashes for all artifacts | The CI job records hashes in `state/projects/PROJ-008-psychology-research.yaml` after every stage. |
| **VI. Clinical Trial Registry Integrity** | Only ClinicalTrials.gov & OSF (2015‑2024) | `code/data/collector.py` filters by registry and registration date; query strings are logged. |
| **VII. Caregiver‑Mediated Delivery Verification** | Tag `delivery_format`; exclude ambiguous entries | `code/data/cleaner.py` enforces a non‑null `delivery_format` enum; ambiguous records are flagged and omitted from primary subgroup analyses. |
| **SC‑005** | Reproducibility on fresh runner | The entire pipeline is executed via a single `make run` command that can be invoked on a clean GitHub Actions runner. |

## Project Structure
```text
code/
├── data/
│   ├── collector.py      # FR‑001, FR‑002
│   └── cleaner.py        # FR‑003, FR‑008, FR‑009, FR‑010
├── analysis/
│   ├── effect_sizes.py   # FR‑004, FR‑013
│   └── meta_analysis.py  # FR‑005, FR‑011, FR‑012, FR‑014
├── viz/
│   └── plotting.py       # FR‑006
├── utils/
│   └── validation.py     # FR‑007, schema enforcement
├── config/
│   └── constants.py      # seeds, thresholds
└── run_pipeline.py       # orchestrates all steps
tests/
├── unit/
│   ├── test_effect_sizes.py
│   └── test_meta_analysis.py
├── integration/
│   └── test_end_to_end.py
└── contract/
    └── test_schemas.py   # validates CSVs against contracts
data/
├── raw/                  # API downloads (immutable)
├── processed/            # cleaned_studies.csv, effect_sizes.csv
├── results/              # meta_analysis.json, plots/
└── metadata/
    └── registry_log.json # query strings, timestamps, checksums
contracts/
├── cleaned_study.schema.yaml
└── effect_size.schema.yaml
docs/
└── quickstart.md
```

## Implementation Phases & Tasks
| Phase | Tasks (covers FR / SC) |
|-------|------------------------|
| **Phase 0 – Foundations** | • Create `contracts/cleaned_study.schema.yaml` and `contracts/effect_size.schema.yaml` (FR‑007).<br>• Implement `utils/validation.py` to apply `jsonschema` checks.<br>• Add checksum utilities (`utils/checksum.py`). |
| **Phase 1 – Data Collection (US1)** | • `collector.py`: query ClinicalTrials.gov API (v2) and OSF API, respecting rate limits with exponential backoff (FR‑001, FR‑002).<br>• Save raw JSON to `data/raw/registry_snapshot_YYYYMMDD.json` and log query strings/timestamps (`metadata/registry_log.json`). |
| **Phase 2 – Cleaning & Tagging** | • `cleaner.py`:<br> – Filter by age (6‑12) and ASD diagnosis.<br> – Extract intervention components via regex patterns (FR‑003).<br> – Tag `delivery_format` (caregiver‑mediated, child‑led, hybrid, unknown) (FR‑008, VII).<br> – Tag `social_skill_domain` (communication, peer_interaction, etc.) (FR‑010).<br> – Implement proportional control splitting for multi‑arm studies (FR‑008).<br> – Fallback to abstract‑only extraction when full text unavailable (FR‑009).<br>• Output `data/processed/cleaned_studies.csv` and `data/raw/excluded_studies.log`. |
| **Phase 3 – Effect‑Size Computation** | • `effect_sizes.py`: compute Hedges’ g with small‑sample correction from means, SDs, Ns (FR‑004, FR‑013).<br>• Validate against `effect_size.schema.yaml`.<br>• Output `data/processed/effect_sizes.csv`. |
| **Phase 4 – Meta‑Analysis & Subgroups** | • `meta_analysis.py`:<br> – Compute heterogeneity (Q, I²).<br> – Choose fixed‑effects if I² ≤ 50 % else random‑effects (FR‑005).<br> – Perform subgroup analyses for (a) mindfulness component, (b) delivery format, (c) social‑skill domain, (d) follow‑up duration (FR‑011, FR‑012).<br> – Suppress meta‑regression, funnel plot, and Egger’s test when N < 10 (FR‑014).<br> – Apply Bonferroni correction for multiple subgroup tests.<br>• Save `data/results/meta_analysis.json`. |
| **Phase 5 – Visualization** | • `plotting.py`: generate forest plot with study CIs and pooled diamond (FR‑006).<br>• Generate funnel plot only if N ≥ 10; compute Egger’s test (FR‑006).<br>• Save PNGs to `data/results/plots/`. |
| **Phase 6 – Reporting & Integrity** | • `run_pipeline.py` orchestrates all steps, writes SHA‑256 checksums for each artifact, and logs success/failure.<br>• Update `state/projects/PROJ-008-psychology-research.yaml` with artifact hashes (Principle III, V). |
| **Phase 7 – Testing** | • Unit tests for each module.<br>• Integration test that runs the full pipeline on a tiny sampled subset (first 5 studies) to verify end‑to‑end reproducibility.<br>• Contract tests that validate CSVs against schemas. |

## Rigor & Risk Mitigation
- **Power / Sample‑Size**: If the final eligible study count `N` < 10, the pipeline automatically switches to a descriptive synthesis and notes the limited power in the final report (SC‑005 compliance).  
- **Multiple Comparisons**: Bonferroni adjustment applied to all subgroup p‑values.  
- **Publication Bias**: Funnel plot & Egger’s test only when `N ≥ 10`; otherwise, report “insufficient studies to assess bias”.  
- **Collinearity**: Delivery format and component tags are mutually exclusive by design; no regression claims of independent effects beyond subgroup means.  
- **Measurement Validity**: Only studies reporting validated social‑skill instruments (e.g., SRS‑2, VABS) are included; instrument name is recorded in `cleaned_studies.csv`.  

---
