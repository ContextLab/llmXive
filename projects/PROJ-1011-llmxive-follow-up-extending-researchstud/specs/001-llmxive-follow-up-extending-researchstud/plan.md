# Implementation Plan: llmXive follow-up: extending "ResearchStudio-Idea"

**Branch**: `001-llmxive-extension` | **Date**: 2026-07-23 (revised) | **Spec**: `specs/001-llmxive-extension/spec.md`
**Input**: Feature specification from `specs/001-llmxive-extension/spec.md`

## Summary

This feature extends the "ResearchStudio-Idea" system to test whether 15 ML-derived ideation patterns transfer to non-ML domains. The system ingests abstracts from ML and non-ML domains (public health, climate adaptation), maps non-ML problem statements to ML patterns using a CPU-quantized embedding model (`all-MiniLM-L6-v2`), generates paired research proposals (pattern-guided vs. generic-prompt baseline), and subjects them to blind expert evaluation. Statistical analysis (paired t-test / Wilcoxon with Benjamini-Hochberg correction) evaluates whether pattern-guided proposals differ from baseline — **with claims scoped to "structured (ML-pattern) prompting vs. unstructured prompting"** (see Limitations; a third non-ML-structure arm is flagged as a spec gap, not silently added).

**Feasibility / answering status (stated up front)**: no verified, openly-downloadable abstract corpus with acceptance labels currently exists for this project, and real expert ratings are not yet collected. **The research question is therefore UNANSWERABLE until (a) a verified labeled corpus is added to the dataset list and (b) real expert ratings are ingested.** Current deliverables are **pipeline validation only**: the full code path (acquisition, embedding, generation, blinding, statistics, reporting) is implemented, tested end-to-end on a clearly-labeled deterministic fixture, and refuses to present dry-run results as answering the research question. Real-data acquisition (FR-001) is contingent on a verified source being added; the fixture is the dry-run path, not a substitute.

**Corpus role (clarified)**: the balanced ML / non-ML accepted / non-ML rejected corpus serves as (i) the source of the 50 non-ML problem statements and (ii) the ML reference context for the pattern cards. **No corpus-level statistical analysis is performed**; `acceptance_status` is recorded for provenance and ingestion hygiene (FR-001 balancing) but is not a variable in any hypothesis test.

This is an **in-place revision** addressing verifier-rejected tasks (T011, T024b, T059a, T059b, T036, T037) and panel concerns; all unaffected structure, paths, and methods are preserved.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `sentence-transformers`, `transformers`, `scikit-learn`, `pandas`, `numpy`, `requests`, `pyyaml`, `statsmodels`, `scipy`, `krippendorff`
**Storage**: Local file system (`data/raw/`, `data/processed/`, `data/results/`), GitHub Actions ephemeral storage
**Testing**: `pytest` (unit tests for data parsing, statistical logic; integration tests for pipeline flow)
**Target Platform**: Linux (GitHub Actions free runner: 2 CPU cores, 7 GB RAM, ~14 GB disk, no GPU)
**Project Type**: Computational research pipeline / CLI
**Performance Goals**: Complete end-to-end pipeline within ≤6 hours (generation of 100 proposals within 4 hours per FR-003); peak memory < 7 GB.
**Constraints**: CPU-only; data openly downloadable (contingent on a verified source being added — see Summary); statistical rigor (FDR correction, power acknowledgement vs. the 0.8 convention, IRR gate); expert ratings are human-derived only (Principle VII).
**Scale/Scope**: ~600 abstracts (ML, non-ML accepted, non-ML rejected in approximately equal proportions per FR-001; ingestion hygiene only — no corpus-level analysis); 50 problem statements; 100 generated proposals (50 pairs); ≥3 expert ratings per proposal.

## Constitution Check

*Gates per `projects/PROJ-1011-llmxive-follow-up-extending-researchstud/.specify/memory/constitution.md`*

1. **I. Reproducibility**: All random seeds (numpy, torch, python) pinned in `code/utils/config.py`. External datasets fetched via deterministic programmatic loaders. `requirements.txt` pins exact versions. Mock/dry-run data generation is deterministic (fixed seed) so the pipeline runs end-to-end even before real ratings arrive.
2. **II. Verified Accuracy**: `code/utils/validate_citations.py` runs before analysis; title-token-overlap ≥ 0.7 enforced; unreachable/mismatch citations block analysis.
3. **III. Data Hygiene**: Raw data checksums recorded under `data/` (a `data/CHECKSUMS` manifest), mirrored in the project state `artifact_hashes` map; no in-place modification — derivations written to new files (`data/raw/` → `data/processed//` → `data/results/`); PII scan in CI.
4. **IV. Single Source of Truth**: All statistics in the final report generated directly from `code/` output files; no hand-typed numbers in `data/results/analysis_report.md` (the SSoT report artifact, per T037 and the data model).
5. **V. Versioning Discipline**: Content hashes for artifacts in `state/`; `code/utils/update_state.py` updates `updated_at` on every artifact change.
6. **VI. Cross-Domain Pattern Validity**: The constitution's wording names "the quantized BERT-base retrieval system". **This plan substitutes `all-MiniLM-L6-v2` (a distilled BERT-family sentence encoder) per FR-002 of the spec** — the substitution is acknowledged here rather than made silently, and is flagged for a constitution/spec alignment amendment. Otherwise: pattern mapping uses the quantized CPU embedding model as specified; generalization claims tied strictly to the statistical comparison of expert ratings (FR-005), scoped to structured-vs-unstructured prompting (see Summary).
7. **VII. Human-in-the-Loop Evaluation Integrity**: Final analysis uses only human scores; no model metrics as quality proxies; blind evaluation protocol (metadata stripped before distribution; experts rate alignment with the problem statement/domain only, never with pattern cards — rubric text embedded in blinded batch instructions); IRR gate (Krippendorff's alpha ≥ 0.6) on raw ratings before aggregation.

## FR/SC Coverage Map

| Requirement | Covered by |
| :--- | :--- |
| FR-001 | Phase 1 (T011: download, pagination, balancing, fallback logic → `data/raw/corpus_raw.jsonl` → `data/processed/corpus_clean.jsonl`). Real-data acquisition contingent on a verified labeled corpus being added; deterministic fixture is the dry-run path (see Summary) |
| FR-002 | Phase 2 (T020 embedding + top-3 retrieval, cosine ≥ 0.6; embedding-model fallback with logged switch on load failure) |
| FR-003 | Phase 3 (T030 generation of 50 pattern-guided + 50 baseline pairs, ≤4 h, batched) |
| FR-004 | Phase 4 (T059a blind distribution with alignment rubric in instructions, T059b deterministic mock ratings for dry-run, T065 real-rating ingestion, ORCID/experience verification, ≥3 experts/proposal) |
| FR-005 | Phase 5 (T032 normality check + paired test, T033 outlier removal, T036 validity metrics, T055 IRR gate on raw data, BH correction). Claims scoped to pattern-guided (structured) vs. generic-prompt (unstructured) baseline |
| FR-006 | Phase 5 (T037 report generation with enforced "associational, not causal" phrase) |
| SC-001 | T036/T032: alignment-score difference tested against null of no difference |
| SC-002 | T032: BH-corrected p-values reported against α = 0.05 |
| SC-003 | T030: runtime and memory measured against ≤6 h / 7 GB runner limits |
| SC-004 | T036: `calculate_validity_improvement()` uses downstream expert alignment scores (not retrieval scores) and reports the difference and test outcome against the null of no difference — SC-004 is treated as a **testable outcome**, not a guaranteed improvement |

## Task Ordering & Dependency Fixes (verifier-rejected tasks)

The verifier rejected T011, T024b, T059a, T059b, T036, T037 for missing artifacts. The plan now mandates, for each task, **both the complete code path and the output artifact**, with explicit artifact paths the Implementer must produce:

- **T011 (redo)**: `code/01_data_acquisition.py` MUST implement (a) paginated download from the primary source, (b) approximately-equal balancing across ML / non-ML accepted / non-ML rejected, (c) fallback-source switch with logged reason on primary failure, (d) validation of title/abstract fields, and (e) write `data/raw/corpus_raw.jsonl` (raw, checksummed) and `data/processed/corpus_clean.jsonl`. Truncated or non-writing implementations fail the task. On unreachable sources the script logs a per-venue error and exits non-zero (fail-first per the spec edge case); the labeled fixture is produced only via an explicit `--dry-run` flag.
- **T020 (embedding fallback, spec edge case)**: `code/02_pattern_mapping.py` MUST attempt the configured embedding model (`all-MiniLM-L6-v2` quantized); if it fails to load under memory constraints, fall back to a smaller, lighter model (configured in `code/utils/config.py`, e.g. a smaller MiniLM variant) and **log the switch** with reason and model names.
- **T024b (redo)**: `code/05_statistical_analysis.py` MUST contain a power-analysis step that reads `n` (number of proposal pairs) from `data/results/generated_proposals.jsonl` and writes `data/results/power_analysis_config.json` (n, α, target effect size d=0.5, achieved power estimate `[deferred]`). The accompanying limitation text MUST reference the 0.8 power convention so the achieved estimate (expected ≈0.70 for n=50, d=0.5, two-sided paired t) is interpretable against it.
- **T059a (redo)**: `code/04_evaluation_loader.py` MUST be complete (no truncated fields), read `data/results/generated_proposals.jsonl`, strip generation metadata, assign deterministic blinded batch IDs, and write `data/results/blinded_batches.csv` with complete `instructions` text. The instructions MUST include the alignment rubric: experts rate alignment of the proposal with the **problem statement and domain context only**; pattern cards are never shown or described to raters (anti-circularity, Principle VII).
- **T059b (redo)**: A deterministic mock-ratings generator (fixed seed, clearly labeled `mock=true` in a metadata field, used ONLY for dry-run logic verification) MUST write `data/results/ratings_filled.csv` with ≥3 raters × 50 pairs × 3 metrics. Real ratings replace this file when available; the final analysis (T037) MUST refuse to report conclusions from mock data.
- **T036 (redo)**: `calculate_validity_improvement()` MUST be implemented in `code/05_statistical_analysis.py`, computing the alignment-score difference (pattern-guided vs. baseline) from expert mean scores (SC-004 — not retrieval similarity) and write `data/results/validity_metrics.json`. The output reports the observed difference and its test outcome against the null of no difference — no presupposed direction or significance.
- **T037 (redo)**: `code/05_statistical_analysis.py` MUST generate `data/results/analysis_report.md` from result files (single source of truth) and MUST include a parser/assertion that the phrase "associational, not causal" appears in the conclusion section (FR-006); the report fails generation if the phrase is absent. Report language MUST scope conclusions to "pattern-guided (structured) prompting vs. unstructured prompting" and frame SC-004 as a testable outcome evaluated against the null, not a guaranteed improvement.

**Dependency ordering (confirmed, resolving panel concerns)**: T011 → T020 → T030 → T059a → T059b/T065 (mock dry-run and real-rating ingestion are parallel branches merging at T055) → **T055 (IRR gate, on RAW ratings, before any cleaning — i.e., T055 runs BEFORE T033)** → T033 (outlier removal) → T032/T036 (primary tests and validity metrics on cleaned data) → sensitivity re-run (T033b, outliers removed) → T037 (final report). Data is downloaded before any consuming task; proposals are generated before blinding/rating; ratings exist before statistics; results exist before the report.

## Test Traceability Matrix

| User Story | Acceptance Scenario | Test Function | Status |
| :--- | :--- | :--- | :--- |
| US-1 | Download balanced abstracts with fallback | `test_download_and_parse_open_datasets` | Planned |
| US-1 | Pre-processing: non-empty abstract, malformed rejection logged | `test_preprocessing_validation` | Planned |
| US-1 | Memory < 7 GB | `test_memory_usage_constraint` | Planned |
| US-2 | Top-3 pattern retrieval (cosine ≥ 0.6) | `test_pattern_mapping_similarity` | Planned |
| US-2 | Embedding-model fallback with logged switch | `test_embedding_model_fallback` | Planned |
| US-2 | Pattern injection vs. generic baseline logic | `test_proposal_generation_logic` | Planned |
| US-2 | 100 proposals within 4 h, batched | `test_generation_runtime_and_batching` | Planned |
| US-3 | Normality check → paired t / Wilcoxon | `test_statistical_normality_check` | Planned |
| US-3 | BH correction on 3 metrics | `test_multiple_comparison_correction` | Planned |
| US-3 | IRR gate (alpha ≥ 0.6) on raw ratings | `test_inter_rater_reliability_gate` | Planned |
| US-3 | Outlier sensitivity re-run | `test_outlier_sensitivity` | Planned |
| US-3 | "associational, not causal" phrase enforced | `test_report_rhetorical_constraint` | Planned |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/
├── 01_data_acquisition.py       # Downloads, paginates, balances, fallback (FR-001) → data/raw/corpus_raw.jsonl
├── 02_pattern_mapping.py        # Embedding + top-3 retrieval + embedding-model fallback with logged switch (FR-002, spec edge case)
├── 03_proposal_generation.py    # LLM generation, pattern vs. baseline (FR-003) → data/results/generated_proposals.jsonl
├── 04_evaluation_loader.py      # Blind distribution w/ alignment rubric (T059a) + mock ratings (T059b) + real ingestion (FR-004)
├── 05_statistical_analysis.py   # Power config (T024b), IRR gate, tests, validity metrics (T036), report (T037) (FR-005, FR-006)
├── utils/
│   ├── config.py                # Seed pinning, path constants, batch sizes, embedding fallback model
│   ├── validators.py            # Data hygiene checks, schema validation vs. contracts/
│   ├── validate_citations.py    # Citation validation (Principle II)
│   └── update_state.py          # State/hash updates (Principle V)
├── requirements.txt             # Pinned dependencies
└── run_pipeline.sh              # Orchestration script

tests/
├── unit/
│   ├── test_data_parsing.py
│   ├── test_pattern_mapping.py
│   └── test_statistical_logic.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single project structure within `code/`, chosen for simplicity and minimal I/O overhead on the constrained runner. Sequential, batched scripts.

## Complexity Tracking

*No violations detected. The pipeline is linear and fits within the defined constraints.*

## Spec gaps flagged for kickback (not silently worked around)

1. **Third-arm confound**: FR-003's two-arm design (ML-pattern structure vs. generic unstructured prompt) cannot distinguish "ML patterns generalize" from "any structured prompt beats an unstructured one". A third arm (non-ML structural scaffolding, e.g., IMRaD sections) would resolve this but is a new requirement; the plan narrows claims instead and flags the gap.
2. **Verified labeled corpus**: no verified open abstract corpus with acceptance labels exists in the verified-datasets block; real-data conclusions are blocked until one is added (see Summary).