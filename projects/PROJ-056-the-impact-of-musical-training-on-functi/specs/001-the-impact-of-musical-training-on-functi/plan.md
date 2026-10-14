# Implementation Plan: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

**Branch**: `001-musical-training-connectivity` | **Date**: 2026-10-14 | **Spec**: `specs/001-the-impact-of-musical-training-on-functi/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-musical-training-on-functi/spec.md`

## Summary
We deliver a reproducible, CPU-only analysis pipeline that (1) **verifies code correctness using a synthetic dataset** (synthetic verification mode, with controlled missingness/corruption injection so quality audits have a real failure mode, and no injected group effect) and (2) **processes real data when a verified open dataset becomes available** (`--mode real`). No verified open source currently provides both adolescent rs-fMRI and a musical-training variable, so the default run validates the pipeline's statistical machinery (false-positive control, NBS, sensitivity analysis) rather than answering the scientific question. **FR-001's real-data requirement and FR-011's real-data validation clause are both DEFERRED and are NOT satisfied by the synthetic runs** under the explicit re-plan trigger below. This revision also repairs the four failing entry points (`code/run_quickstart_test.py`, `code/data/run_synthetic_generator.py`, `code/main.py`, `code/data/real_ingest.py`) identified by the verifier.

## Re-plan trigger (testable condition for the deferred real-data path)
The deferred real-data mode (FR-001 real clause, FR-011 real-data validation) is activated by re-planning when ALL of the following hold:
1. A **named dataset** passes the verified-dataset gate: a reachable, programmatically downloadable source (direct URL, Hugging Face dataset, or similar open repository) is confirmed by the Reference-Validator Agent.
2. That dataset contains **adolescent resting-state fMRI** (preprocessed to a standard sufficient for ROI extraction) **and a musical-training variable** (years of training or an equivalent documented history).
3. The dataset provides the confounder columns (age, sex, motion, SES) per the Subject schema.
Until then, `--mode real` remains a graceful-stub that reports data-source unavailability, and **FR-011 remains unmet** — the synthetic permutation runs do not count as satisfying it.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `nibabel`, `networkx`, `matplotlib`, `pyyaml`, `tqdm`, `jsonschema` (pinned in `code/requirements.txt`)
- **Storage**: Local filesystem under `data/`; Parquet for subject tables, per-subject JSON for connectivity, CSV/JSON for results.
- **Testing**: `pytest` (unit, integration, contract validation).
- **Target Platform**: Linux (GitHub Actions 2-core runner).
- **Performance Goals**: Peak RAM ≤ 7 GB; total runtime ≤ 6 h; CPU-only (no GPU escape hatch needed — all methods have faithful CPU forms).
- **Constraints**: No open, programmatically downloadable dataset satisfies FR-001's data requirements (see research.md §1.1). Real-data mode is a documented stub that fails gracefully, per the spec's edge case for unavailable data sources.
- **Scale/Scope**: Default synthetic cohort of 100 subjects (50/group, satisfying the ≥50/group halt rule); 200-ROI atlas.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Seeds pinned in `code/`; `requirements.txt` pinned; pipeline runs end-to-end on a fresh CI runner. |
| II. Verified Accuracy | PASS | No dataset URLs cited beyond the verified block; the unverifiable datasets (ABCD/HCP-A) are named without fabricated URLs. |
| III. Data Hygiene | PASS | Checksums recorded under `data/logs/checksums.txt`; no in-place mutation; no PII in synthetic data. |
| IV. Single Source of Truth | PASS | `results_summary.csv` (FR-010) is the sole aggregate for downstream reporting; derived numbers never hand-typed. |
| V. Versioning Discipline | PASS | Content hashes recorded in project state YAML; `updated_at` bumped on artifact change. |
| VI. Neuroimaging Data Integrity | PASS | Synthetic NIfTI files are spec-compliant; real-data mode preserves raw files unchanged with per-subject preprocessing metadata. |
| VII. Behavioral Assessment Standardization | PASS | Synthetic `years_of_training` generated from a documented distribution; real-data mode requires validated questionnaire-derived columns per the Subject schema. |

## Project Structure
```text
specs/001-the-impact-of-musical-training-on-functi/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── subject.schema.yaml
    ├── connectivity.schema.yaml
    ├── network_metric.schema.yaml
    ├── statistical_result.schema.yaml
    └── network_component.schema.yaml

code/
├── requirements.txt
├── main.py                         # CLI entry point (synthetic vs real mode)
├── run_quickstart_test.py          # End-to-end smoke test of quickstart commands
├── data/
│   ├── run_synthetic_generator.py  # Executable wrapper for synthetic_generator
│   ├── synthetic_generator.py
│   ├── preprocess.py
│   └── real_ingest.py              # Real-data ingestion; fails gracefully, exit 0 with clear message
├── analysis/
│   ├── atlas.py                    # Bundled Schaefer-200 CSV
│   ├── connectivity.py
│   ├── network_metrics.py          # Network-level aggregation (NetworkMetric entity)
│   ├── stats.py
│   ├── correlation.py
│   └── sensitivity.py
└── utils/
    ├── logging.py
    └── memory_monitor.py

data/
├── raw/
├── processed/
│   ├── subjects.parquet
│   ├── connectivity/<subject_id>.json
│   ├── network_metrics/<subject_id>.json
│   └── logs/
└── results/
    ├── statistical_results.csv
    ├── nbs_components.json
    ├── sensitivity_analysis.csv
    └── results_summary.csv         # SSoT (FR-010)
```

**Structure Decision**: Single-project layout; analysis modules grouped by pipeline stage; all entry points directly executable (`python code/<script>.py`) so the quickstart smoke test and CI can invoke them without argument errors.

## Complexity Tracking (FR / SC → Phase / Task)

| FR / SC | Phase / Task | Reason for Inclusion |
|--------|--------------|----------------------|
| FR-001 | Phase 1 — `run_synthetic_generator.py` + `preprocess.py`; `real_ingest.py` stub | Generates/loads data, applies ≥1 yr threshold, matches confounders, caps at 75/group, halts <50/group. **Real-data clause DEFERRED** (no verified open dataset; see Re-plan trigger). |
| FR-002 | Phase 2 — `connectivity.py` | ROI-wise Pearson + Fisher-z, per-subject JSON. |
| FR-003 | Phase 2 — `stats.py` | Welch's t per edge within auditory/motor/executive networks, BH FDR. |
| FR-004 | Phase 2 — `correlation.py` | Pearson/Spearman vs years of training, musicians only. |
| FR-005 | Phase 2 — `sensitivity.py` | Threshold sweep {0.01, 0.05, 0.10}. |
| FR-006 | Phase 1 — `memory_monitor.py` | ≤7 GB enforcement with adaptive fallback: per-subject streaming first, then deterministic seeded subsetting; hard abort only as last resort. |
| FR-007 | Phase 2 — `stats.py` / `correlation.py` | Cohen's d and 95% CIs for all tests. |
| FR-008 | Phase 2 — `stats.py` (NBS) | Largest connected component, FWER-corrected p. |
| FR-009 | Phase 1 — `preprocess.py` | Matching defines the analysis sample; residualization then adjusts the matched sample on age/sex/motion/SES. |
| FR-010 | Phase 3 — `results_summary.csv` builder | Aggregates all primary outcomes. |
| FR-011 | **UNMET / DEFERRED (real-data clause)** — no plan element satisfies FR-011 today | FR-011 requires validation **on real data**; no verified real dataset exists, so **no real-input validation is delivered and FR-011 is explicitly not satisfied**. The Phase 3 synthetic-null permutation runs validate only the statistical machinery's false-positive control (FDR/NBS) on synthetic data — they are machinery verification, not FR-011 validation. The real-data validation clause activates solely under the Re-plan trigger above, together with FR-001's real-data clause. No synthetic effect injection is used in these runs. |
| NetworkMetric entity (spec Key Entities) | Phase 2 — `network_metrics.py` | Per-subject network-level mean connectivity for auditory/motor/executive networks, validated against `contracts/network_metric.schema.yaml`. |
| SC-001 | Phase 2 — `nbs_components.json` | Component size vs null. |
| SC-002 | Phase 2 — `statistical_results.csv` | r vs zero-correlation null. |
| SC-003 | Phase 2 — `sensitivity_analysis.csv` | Counts across thresholds. |
| SC-004 | Phase 3 — memory/runtime log | Peak RAM and total runtime recorded. |
| SC-005 | Phase 1 — inclusion-criteria audit | Fraction of final subjects with valid labels + complete data reported; must be ≥90%. Meaningful because the generator injects controlled missingness/corruption; the clean-fraction assertion is additionally only scientifically meaningful in real-data mode. |

## Phase 0 — Repair Failing Entry Points (verifier feedback T001–T003, T111)
1. **Fix `code/main.py` (exit=2)** — correct argparse definition so `--mode synthetic --n-subjects N` runs end-to-end; add `--n-permutations` and `--seed` flags.
2. **Fix `code/data/run_synthetic_generator.py` (exit=1)** — make it a standalone executable with `if __name__ == "__main__"` and correct relative imports (run as `python code/data/run_synthetic_generator.py` from repo root).
3. **Fix `code/data/real_ingest.py` (exit=1)** — it must fail *gracefully* per the spec's edge case: when no verified dataset path is supplied, print a clear "data source unavailable" message and exit 0 with a JSON status file, not an unhandled exception.
4. **Fix `code/run_quickstart_test.py` (exit=5)** — subprocess-invokes the exact quickstart commands; asserts exit 0 and schema-valid outputs.

## Phase 1 — Data Model, Contracts & Synthetic Generation
- Contracts under `contracts/` (subject, connectivity, network_metric, statistical_result, network_component) — drafted; validated in tests via `jsonschema`.
- **Synthetic generator**: `--n-subjects` (default 100, capped 75/group per FR-001); `years_of_training ~ Uniform(1,10)` for musicians, 0 otherwise; age ~ N(15,1); sex 50/50; motion ~ N(0.15,0.05); SES ~ N(0,1); mock 64³ Gaussian-noise NIfTI per subject. **No systematic group effect by default** (false-positive verification). Optional `--inject-effect` (d≈0.4) exists only for the power simulation, never for primary output.
- **Controlled quality defects**: the generator injects a small, seeded rate of missing training-history values and corrupted NIfTI files (logged), so the preprocessing exclusions and the SC-005 inclusion audit have a genuine failure mode to detect rather than passing vacuously.
- **Preprocess**: ≥1 yr threshold (edge case: 0 years + "some experience" → non-musician); drop missing training history with logged exclusion count; skip+log corrupted NIfTI files; propensity matching (nearest-neighbor, caliper 0.2 SD) on age/sex/motion/SES, then edge-wise linear residualization of the matched sample on the same covariates — matching defines the analysis sample (the estimand is the matched-sample group difference), residualization provides additional covariate adjustment within it; halt with "Sample Size Insufficient" (the spec's edge-case-3 string; the log also records the US-1 phrasing "Insufficient Data for Power" for traceability, since the spec itself uses both) if either group <50.
- **Inclusion audit (SC-005)**: report fraction of subjects with valid labels + complete data after the injected defects are handled; assert ≥90%. The clean-fraction assertion is only scientifically meaningful in real-data mode; on synthetic data it verifies the audit logic against the known injected defect rate.
- **Memory guard (FR-006)**: `memory_monitor.py` implements the adaptive fallback the FR mandates — per-subject streaming keeps baseline usage low; if a step still approaches 7 GB, the monitor first applies deterministic seeded subsetting (recording the subsetting decision in the log); a hard abort is a last resort only when subsetting cannot reduce usage below the limit.

## Phase 2 — Core Analysis (CPU-only)
1. Atlas loading from bundled CSV (no download).
2. Connectivity: Pearson + Fisher-z per subject → per-subject JSON.
3. **Network metrics (NetworkMetric entity)**: per-subject mean within-network connectivity for auditory, motor, and executive networks → `data/processed/network_metrics/<subject_id>.json`, validated against `contracts/network_metric.schema.yaml`.
4. Group comparison: Welch's t per edge (auditory/motor/executive), BH FDR (per FR-003), Cohen's d, 95% CI (bootstrap).
5. NBS: permutation-based (default 1000 permutations), thresholds t ∈ {1.8, 2.0, 2.5}; largest component size + FWER p.
6. Correlation (musicians only): Pearson (Spearman on non-normality), BH FDR, r, p, q, effect size, 95% CI.
7. Sensitivity: sweep q ∈ {0.01, 0.05, 0.10}; counts table; "low stability" flag per spec.

## Phase 3 — Validation, Testing & Aggregation
- Unit tests on tiny subsets (N=4); integration test runs full synthetic pipeline; contract validation of every output.
- **Machinery verification on synthetic-null data (NOT FR-011 validation)**: null synthetic data must yield FDR/NBS false-positive rates at nominal levels; no effect injection. These runs verify the statistical machinery's false-positive control only — they use no real inputs and therefore do **not** satisfy FR-011's real-data validation requirement. **FR-011's real-data validation clause is UNMET/DEFERRED** — no verified real dataset exists today, so no real-data validation is delivered; the clause activates under the Re-plan trigger above, together with FR-001's real-data clause.
- Power simulation (separate, effect-injected synthetic datasets) → detection-rate estimate logged as a power limitation acknowledgment.
- `results_summary.csv` (FR-010) aggregates group stats, network metrics, correlations, sensitivity table, NBS summary.
- Runtime + peak-RAM recorded (SC-004).

## Phase 4 — Documentation & Handoff
- `quickstart.md` updated with the exact working commands verified by `run_quickstart_test.py`.
- `research.md` records dataset limitation, deferred FR-001/FR-011 real-data status, and power-simulation result.
- All artifacts hashed in project state YAML.

## Scope notes and flagged gaps (not silently resolved)
- **Reviewer concern (≥1 yr musician cutoff)**: the cutoff is fixed by the spec (FR-001, edge case). The plan does not change it; however, the literature typically uses multi-year, currently-practicing musicians, and a relatively brief cutoff period may dilute effects toward the null. This is flagged as a spec-level gap for future revision; the plan additionally reports the distribution of `years_of_training` within the musician group so any dilution is visible.
- **Real-data feasibility (FR-001 and FR-011 real-data clauses)**: neither can be met with any verified open dataset today (research.md). The plan delivers the compliant pipeline and a graceful real-data stub; the scientific question and FR-011's real-data validation remain open until the Re-plan trigger fires — this mismatch is stated, not papered over. The spec would ideally add an explicit conditional/deferred clause for FR-011 mirroring the FR-001 treatment; this is flagged for spec kickback.
- **Halt-message inconsistency in the spec**: US-1 scenario 1 mandates "Insufficient Data for Power" while edge case 3 mandates "Sample Size Insufficient". The plan aligns on the edge-case string "Sample Size Insufficient" and logs both phrasings; the spec should unify the string.