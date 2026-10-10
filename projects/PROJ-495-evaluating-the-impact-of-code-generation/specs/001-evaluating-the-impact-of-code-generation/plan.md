# Implementation Plan: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2026-09-03 | **Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary

Build a CPU-only research pipeline that (1) ingests LLM-generated and human-written code corpora, (2) runs static analysis (Bandit for Python, Semgrep multi-language) to extract per-file vulnerability counts and CWE classifications, (3) computes vulnerability density per file and aggregates by code source, (4) runs a Negative Binomial regression (primary) and Mann-Whitney U (robustness) with multiple-comparison correction, (5) produces figures and tables, and (6) supports a stratified manual-audit workflow for precision/recall/FPR estimation.

**Scope inconsistency surfaced for correction (blocking data feasibility):** the spec's required datasets — CodeVulnBench and a human-written code subset (e.g., Juliet Test Suite) — have **NO verified public download source** at planning time (see research.md, Dataset Strategy). No URL may be fabricated. The plan therefore builds the pipeline with a manifest-driven ingestion step that (a) first attempts programmatic acquisition via well-known loaders (`datasets.load_dataset("Intel/code-vulnerability...")`-style IDs are NOT assumed — only attempts that are verifiable at runtime are made), and (b) fails loudly with a documented manifest of what was obtainable. If, at execution time, no open mirror is reachable, the run halts with an explicit data-availability error rather than fabricating or synthesizing data. **The spec should be amended to name a verified open dataset pair before execution can produce real results.** Similarly, SonarQube Community Edition requires a Java server process that cannot run unattended within the free-tier runner constraints (Constitution Principle VI mandates it); the plan runs Bandit + Semgrep and flags the SonarQube mandate for constitution amendment (see Complexity Tracking).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `bandit==1.7.9`, `semgrep==1.78.0`, `statsmodels==0.14.1`, `scipy==1.13.1`, `pandas==2.2.2`, `matplotlib==3.9.0`, `pyyaml==6.0.1`, `pytest==8.2.2` (all pinned in `code/requirements.txt`)
**Storage**: Files only — `data/raw/`, `data/derived/`, `results/`; no database
**Testing**: pytest (unit + contract tests against `specs/.../contracts/*.schema.yaml`)
**Target Platform**: GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, ~14 GB disk, no GPU, ≤6 h/job) — all methods CPU-only; no GPU escape hatch needed
**Project Type**: Research pipeline (CLI scripts)
**Performance Goals**: Full pipeline completes within the ≤6 h job limit; memory stays under ~7 GB (SC-003, SC-004)
**Constraints**: CPU-only; per-file streaming (one file in memory at a time); files >50k LOC skipped and logged (spec edge case); no network access assumed after data-ingest phase
**Scale/Scope**: Dataset sizes deferred to research phase; n ≥ 30 per group assumed per spec (if not met, descriptive statistics only — spec assumption honored)

## Constitution Check

| Principle | Status | How satisfied |
|---|---|---|
| I. Reproducibility | PASS | Random seeds pinned in `code/src/config.py`; datasets fetched from canonical manifest with SHA-256 checksums recorded under `data/checksums.json`; pipeline is one deterministic CLI entry point |
| II. Verified Accuracy | PASS (with flag) | No citations carry fabricated URLs; datasets without verified sources are named without URLs (research.md); citation overlap gate applied to all references |
| III. Data Hygiene | PASS | All raw files checksummed on ingest; every transformation writes to `data/derived/` with a derivation record in `data/derived/provenance.json`; no in-place modification; PII scan N/A (public code corpora) but no PII committed |
| IV. Single Source of Truth | PASS | Every figure/statistic emitted by `code/src/` into `results/tables/*.csv` and `results/figures/*`; paper stage must read from these files only |
| V. Versioning Discipline | PASS | Artifact hashes recorded in `state/projects/PROJ-495-...yaml` `artifact_hashes`; `updated_at` bumped on each artifact change |
| VI. Static Analysis Fidelity | **FLAG** | Bandit + Semgrep fully compliant; SonarQube cannot run unattended on the runner (requires Java server + Docker, unavailable). Flagged for constitution amendment; interim: Bandit + Semgrep only, documented in `results/limitations.md`. See Complexity Tracking |
| VII. Vulnerability Taxonomy Compliance | PASS | Every finding carries a CWE ID (Bandit and Semgrep both emit CWE tags); density-by-CWE-class table produced (`results/tables/cwe_density_by_group.csv`) |

## Project Structure

```text
specs/001-evaluating-the-impact-of-code-generation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── file-manifest.schema.yaml
│   ├── per-file-analysis.schema.yaml
│   └── aggregate-results.schema.yaml
└── tasks.md            # (Phase 2, /speckit-tasks)

code/
├── requirements.txt
├── src/
│   ├── config.py           # seeds, thresholds, tool pins
│   ├── ingest.py           # FR-001: dataset download + manifest + checksums
│   ├── static_analysis.py  # FR-002: Bandit + Semgrep runners, CWE extraction
│   ├── density.py          # FR-003: density calc + aggregation
│   ├── stats.py            # FR-004, FR-006: NB regression, MW-U, correction
│   ├── audit.py            # FR-007, FR-008: stratified sample, FPR
│   ├── figures.py          # FR-005: boxplot, CWE bar chart
│   └── pipeline.py         # orchestrator CLI
└── tests/
    ├── test_density.py
    ├── test_stats.py
    ├── test_ingest.py
    └── contract/
        └── test_schemas.py

data/
├── raw/                    # immutable downloads
├── derived/                # transformed outputs + provenance.json
└── checksums.json

results/
├── tables/
└── figures/
```

**Structure Decision**: Single-project layout (Option 1) — a pure research pipeline with no UI/service components.

## Implementation Phases

### Phase 1 — Data ingestion (FR-001, SC-005)
- **Task 1**: `ingest.py` — manifest-driven acquisition of the LLM-generated corpus and human-written corpus. Attempts programmatic download of CodeVulnBench and the human-code subset; records SHA-256 checksums (`data/checksums.json`, Constitution III); writes `data/derived/file_manifest.csv` (one row per file: path, source group, language). Fails loudly if no corpus is obtainable — no synthetic fallback. Files >50k LOC are marked `skipped_size` at this stage.
- **Task 2**: Contract test validating the manifest against `contracts/file-manifest.schema.yaml`; proportion of successfully ingested files reported (SC-005).

### Phase 2 — Static analysis (FR-002, SC-003, SC-004, SC-005)
- **Task 3**: `static_analysis.py` — run Bandit (Python files) and Semgrep (`p/python` + `p/javascript` + `p/java` registries, CPU mode) file-by-file (streaming, one file in memory); parse findings into `VulnerabilityRecord` rows (CWE ID, severity, tool); per-file counts into `data/derived/per_file_analysis.csv` validated against `contracts/per-file-analysis.schema.yaml`. Parse failures logged and file excluded (spec edge case); zero-finding files recorded with count 0 (US-1 scenario 2). SonarQube omitted per flagged amendment; limitation documented in `results/limitations.md`.
- **Task 4**: Timing and peak-memory instrumentation around the analysis loop (SC-003, SC-004), written to `results/tables/resource_usage.csv`.

### Phase 3 — Density and aggregation (FR-003, US-2)
- **Task 5**: `density.py` — LOC counting (non-comment, non-blank, language-aware via per-language comment regexes, documented in assumptions); density = count / LOC with zero-LOC → `undefined` (recorded, excluded from means); per-file density CSV + group summary stats (mean, median, SD) to `results/tables/group_summary.csv`, validated against `contracts/aggregate-results.schema.yaml`.

### Phase 4 — Statistical comparison (FR-004, FR-006, SC-001, SC-002)
- **Task 6**: `stats.py` — Negative Binomial regression (`statsmodels` GLM NegativeBinomial, response = vulnerability count, exposure = LOC offset, predictor = group) as primary test; Mann-Whitney U on per-file densities as secondary; Benjamini-Hochberg correction across the two tests (FR-006); adjusted p-values and effect sizes to `results/tables/statistical_tests.csv`. Claims framed as associational (spec assumption: observational). Power limitation acknowledged explicitly (no a-priori power analysis possible with deferred dataset sizes — noted in limitations).
- **Task 7**: Unit tests with synthetic two-group data of known p-value (US-3 independent test: p within 0.001) and known density values (US-2 independent test).

### Phase 5 — Audit workflow (FR-007, FR-008, SC-006, SC-007)
- **Task 8**: `audit.py` — stratified random sample (seeded) of findings: min(5% of findings, 100), stratified by tool × CWE class × code group; emits `data/derived/audit_sample.csv` with blank verdict column. Precision/recall and per-group FPR computed from a filled `data/derived/audit_verdicts.csv` (human input; if no auditor verdicts are available at run time, the module reports precision/recall/FPR as `not_available` and the limitation is documented — spec assumption of auditor availability flagged).

### Phase 6 — Figures and reporting (FR-005)
- **Task 9**: `figures.py` — boxplot of density by group; bar chart of CWE-class distribution by group; saved as PNG + SVG under `results/figures/`. Generated after all consuming analyses (ordering: data → analysis → stats → figures).
- **Task 10**: `pipeline.py` orchestrator + `quickstart.md` end-to-end run on a 50-file smoke subset (US-1 independent test), then full run; final results summary table.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| SonarQube omitted (Constitution VI partial) | SonarQube Community requires a Java server/Docker process that cannot run unattended on the free-tier runner | Running Bandit + Semgrep only leaves a two-tool pipeline; rejected as constitution-noncompliant without an explicit amendment — hence surfaced as a blocking flag rather than silently dropped |
| Dataset source unverified (FR-001) | CodeVulnBench and Juliet have no verified public URL at plan time | No alternative open dataset with verified URL supporting the same LLM-vs-human comparison exists in the verified block; fabricating a mirror or synthesizing data is prohibited — spec must be amended to name a verifiable source pair |
