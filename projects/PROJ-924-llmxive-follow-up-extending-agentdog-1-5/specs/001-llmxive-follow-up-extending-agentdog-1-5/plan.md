# Implementation Plan: Zero-Shot Drift Detection for AgentDoG 1.5

**Branch**: `PROJ-924-zero-shot-drift` | **Date**: 2026-07-18 | **Spec**: `specs/PROJ-924/spec.md`
**Input**: Feature specification from `specs/PROJ-924/spec.md` (revised to address verifier feedback on T010d and T011a)

## Summary

Extend the AgentDoG 1.5 safety taxonomy with a zero-shot drift detector: embed agent logs with `all-MiniLM-L6-v2` (CPU), compute cosine distance to category centroids built from ≥100 curated examples per category in `agentdog/safety-v1`, flag logs with `drift_score ≥ 0.5`, validate against a three-annotator blinded gold standard, and compare against a `google/flan-t5-small` zero-shot baseline (AUC-ROC, latency). All execution is CPU-only on the GitHub Actions free-tier runner (≤7 GB RAM, ≤6 h).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `sentence-transformers==2.7.0`, `transformers==4.44.2`, `torch==2.4.1` (CPU wheel), `scikit-learn==1.5.1`, `scipy==1.14.0`, `pandas==2.2.2`, `numpy==1.26.4`, `datasets==2.21.0`, `jsonschema==4.23.0`, `pytest==8.3.2`
**Storage**: Local filesystem — `data/raw/` (immutable, checksummed), `data/processed/` (derived artifacts), JSON/Parquet
**Testing**: `pytest` (unit + contract + integration); test execution evidence captured to `data/processed/test_results.log`
**Target Platform**: Linux (GitHub Actions free-tier runner, 2 CPU cores, no GPU)
**Project Type**: Research pipeline (CLI scripts)
**Performance Goals**: Full pipeline ≤ 6 h wall-clock; drift per-log latency ≤ 0.5 × Flan-T5 per-log latency (FR-011)
**Constraints**: ≤ 7 GB RAM; CPU-only (no `cuda` calls); batch size = 64 (verified fact, arXiv:2410.21676); no synthetic stand-in for human annotations
**Scale/Scope**: Centroids from ≥100 examples × 4 categories; novel-log corpus ≥ 500 logs (FR-014); annotation sample ≥ 100 logs across full drift range (FR-017)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Requirement | Compliance Strategy |
|-----------|-------------|---------------------|
| I. Reproducibility | Seeds pinned, canonical dataset sources | `RANDOM_SEED = 42` in `code/config.py`; datasets fetched via `datasets.load_dataset("agentdog/safety-v1")` (canonical HF id, per spec assumption of public accessibility); all sampling seeded |
| II. Verified Accuracy | Citations verified against primary sources | research.md cites only the verified sources named in the spec; no invented URLs |
| III. Data Hygiene | Checksums, no in-place modification, PII scan | `data/raw/` immutable; every derivation writes new files under `data/processed/`; SHA-256 checksums recorded in `data/raw/checksums.json`; GitHub-issue-derived logs pass a PII scrubber (emails/keys redacted) before storage |
| IV. Single Source of Truth | Every reported number traces to code output | All metrics in the final report are read programmatically from `data/processed/metrics.json`; no hand-typed statistics |
| V. Versioning | Content hashes on artifacts | Artifact hashes recorded in the project `state/.../PROJ-924-....yaml` `artifact_hashes` map |
| VI. Zero-Shot Drift Validity | Human gold standard, κ ≥ 0.6, before drift score is reported as reliable | Final validation metrics (FR-007–FR-009, FR-015, FR-016) computed ONLY from real three-annotator data in `data/human_annotations.json`. If that file is absent, the pipeline emits a partial report with status `Incomplete` and exits non-zero; no simulated annotations are ever generated |
| VII. Resource-Constrained Computational Integrity | CPU, 7 GB RAM, 6 h | No GPU code paths; MiniLM (~80 MB) and flan-t5-small (~300 MB) both CPU-resident; streaming/batched processing; runtime and peak RAM measured and recorded (FR-012) |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-924/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agent_log.schema.yaml
│   ├── drift_output.schema.yaml
│   ├── human_annotation.schema.yaml
│   └── taxonomy_centroid.schema.yaml
└── tasks.md            # produced by /speckit-tasks
```

### Source Code (repository root)

```text
projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/
├── code/
│   ├── requirements.txt        # pinned dependencies (Reproducibility Requirement)
│   ├── pyproject.toml          # tool config incl. [tool.ruff]
│   ├── config.py               # RANDOM_SEED=42, MAX_RAM_GB=7, BATCH_SIZE=64, DRIFT_THRESHOLD=0.5
│   ├── data_loader.py          # agentdog/safety-v1 load; novel-corpus acquisition; checksums; PII scrub
│   ├── embeddings.py           # centroid construction + drift scoring
│   ├── baseline_llm.py         # flan-t5-small zero-shot classifier + latency measurement
│   ├── validation.py           # kappa, Mann-Whitney U, logistic regression, chi-squared, AUC-ROC
│   ├── report.py               # final report from metrics.json
│   └── main.py                 # orchestration
├── data/
│   ├── raw/                    # immutable inputs + checksums.json
│   ├── human_annotations.json  # external human input (not generated by code)
│   └── processed/              # centroids, scores, bins, batches, metrics.json, report.md
└── tests/
    ├── unit/
    │   ├── test_config.py      # asserts constants incl. RANDOM_SEED==42, MAX_RAM_GB==7, BATCH_SIZE==64, DRIFT_THRESHOLD==0.5
    │   └── test_tooling.py     # asserts pyproject.toml exists with [tool.ruff] section
    ├── contract/               # schema validation of all data/processed outputs
    └── integration/
        └── test_pipeline.py    # end-to-end on a small real slice
```

**Structure Decision**: Single research-pipeline project. `code/` holds all logic, `data/` strictly inputs/derived outputs, `tests/` validates config, tooling, contracts, and end-to-end behavior. Test runs tee output to `data/processed/test_results.log` so passing-test evidence is a persisted artifact (fixes T010d).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Human-annotation hard gate | Constitution Principle VI requires κ ≥ 0.6 on real human data before the drift score is reported as reliable | Simulation/synthetic annotators rejected: a proxy cannot validate novel-threat detection and would violate the fabrication gate |
| External GitHub-issue scraping (FR-014) | Spec requires ≥500 post-2025 public GitHub issue logs; no HF dataset provides this | A bundled toy corpus rejected: spec mandates real emergent-pattern exposure |

## Phase Plan (ordered: data before consumers, models before evaluation, figures before report)

### Phase 0: Research & Feasibility
- Verify `agentdog/safety-v1` loads via `datasets.load_dataset` and contains ≥100 labeled examples for each of Safety, Privacy, Bias, Jailbreak (FR-004). Verify MiniLM and flan-t5-small run on CPU within RAM. → `research.md`.

### Phase 1: Data Model & Contracts
- Define schemas for logs, centroids, drift outputs, and three-category human annotations. → `data-model.md`, `contracts/*.schema.yaml`.

### Phase 2: Setup & Tooling (fixes T011a, T010d)
- **T011a (redo)**: Write `code/config.py` with the exact constants `RANDOM_SEED = 42`, `MAX_RAM_GB = 7`, `BATCH_SIZE = 64`, `DRIFT_THRESHOLD = 0.5` (spec pre-registered operating point), plus `HIGH_DRIFT_QUANTILE = [deferred]`, `LOW_DRIFT_QUANTILE = [deferred]`. Write `code/requirements.txt` and `code/pyproject.toml` (with `[tool.ruff]`).
- **T010d (redo)**: Write `tests/unit/test_config.py` (asserts each constant's exact value) and `tests/unit/test_tooling.py` (`test_ruff_config_exists`, `test_pyproject_config_exists`). Execute `pytest tests/unit/ -v | tee data/processed/test_results.log` and commit the log as evidence of passing tests.

### Phase 3: Data Acquisition (FR-004, FR-014, FR-012)
- Load `agentdog/safety-v1` via `datasets.load_dataset`; checksum to `data/raw/checksums.json`.
- Acquire ≥500 post-2025 agent-interaction logs from public GitHub issue threads via the GitHub REST API (`GET /repos/{owner}/{repo}/issues`, unauthenticated, rate-limited, seeded repository list); scrub PII; store as `data/raw/novel_corpus.jsonl` validated against `agent_log.schema.yaml`.

### Phase 4: Taxonomy & Drift Scoring — US-01 (FR-001, FR-002, FR-003, FR-004)
- Embed ≥100 curated examples per category with `all-MiniLM-L6-v2` (batch size 64); compute category centroids (`taxonomy_centroid.schema.yaml`).
- Embed all logs; compute cosine distance to each centroid; `drift_score` = min distance; `review_flag = drift_score >= 0.5`; write `data/processed/drift_scores.parquet` validated against `drift_output.schema.yaml`.

### Phase 5: Stratification & Annotation Batches — US-02 part 1 (FR-005, FR-006, FR-017)
- Bin logs: high-drift = top [deferred] quantile, low-drift = bottom [deferred] quantile.
- Draw a seeded random sample of ≥100 logs across the full drift range (FR-017).
- Emit blinded annotation batches (`data/processed/annotation_batches/`) containing only `log_id` + text — no drift scores, no bin labels.

### Phase 6: Human Annotation (external, FR-006)
- Three independent annotators label each batched log as "novel attack" / "known attack" / "benign". Results ingested as `data/human_annotations.json` (schema-validated). Majority vote → binary "novel" gold standard. **This is a manual external step; code never generates it.**

### Phase 7: Statistical Validation — US-01/US-02 (FR-007, FR-008, FR-009, FR-015, FR-017)
- Mean pairwise Cohen's Kappa (3 pairs); gate κ ≥ 0.6.
- Mann-Whitney U on drift scores, human-novel vs human-benign (p < 0.05, rank-biserial ≥ 0.5) — computed on the FR-017 full-range random sample to avoid range restriction.
- Logistic regression (novel ~ drift_score): coefficient p-value, AUC-ROC — same random sample.
- Chi-squared test of "novel" proportion across high/low-drift bins (α = 0.05).
- Multiple comparisons: report Holm correction across the family of hypothesis tests (Mann-Whitney, logistic coefficient, chi-squared); note that thresholds are pre-registered per spec.
- Power: acknowledge as a limitation — annotation sample size (≥100) is fixed by FR-017, not by a power calculation; report achieved power/CI descriptively.

### Phase 8: Baseline Comparison — US-03 (FR-010, FR-011, FR-016)
- Run zero-shot `google/flan-t5-small` classification on the annotated log set (CPU); compute AUC-ROC against the human gold standard; verify baseline AUC ≥ 0.70 before using it as reference (FR-016).
- Measure per-log inference latency of both methods on the same CPU; check drift ≤ 0.5 × Flan-T5.
- Compute drift-method AUC; flag "computationally efficient alternative" if within 0.10 of baseline AUC.

### Phase 9: Final Report (FR-012, FR-013)
- Record peak RAM and wall-clock runtime; assert FR-012 limits.
- Generate `data/processed/report.md` + `metrics.json` from code only (Principle IV). Figures (drift-score distribution by human label; ROC curves) generated before report inclusion.
- If `data/human_annotations.json` is absent, emit partial report with status `Incomplete` and exit non-zero (Principle VI hard gate).

## FR / SC Coverage Map

| Req | Phase | Req | Phase | Req | Phase |
|-----|-------|-----|-------|-----|-------|
| FR-001 | 4 | FR-007 | 7 | FR-013 | 9 |
| FR-002 | 4 | FR-008 | 7 | FR-014 | 3 |
| FR-003 | 4 | FR-009 | 7 | FR-015 | 7 |
| FR-004 | 3–4 | FR-010 | 8 | FR-016 | 8 |
| FR-005 | 5 | FR-011 | 8 | FR-017 | 5, 7 |
| FR-006 | 5–6 | FR-012 | 9 | | |

SC-001 = FR-001–004, FR-008 (Phases 3–4, 7); SC-002 = FR-006–009, 015, 017 (Phases 5–7); SC-003 = FR-010–011, 016 (Phase 8); SC-004 = FR-012 (Phase 9). All covered.

## Unresolved Concerns Resolution

1. **T011a fix**: `code/config.py` is now an explicit Phase-2 deliverable with exact constants; the prior draft's `DRIFT_THRESHOLD = 1.5` was wrong and is corrected to `0.5` per FR-002.
2. **T010d fix**: test runs are piped to a committed evidence log (`data/processed/test_results.log`), so passing-test proof is a persisted artifact.
3. **Dataset fidelity**: the prior draft's proxy datasets (the-stack, humaneval) contradicted the spec's mandated `agentdog/safety-v1`; removed. The spec asserts `agentdog/safety-v1` is publicly accessible and verified; it is loaded via its canonical HF id. If load fails at execution time, that is a blocking data-availability gap to be surfaced, not worked around with a substitute.
4. **Human validation gate**: no simulation fallback anywhere; `Incomplete` status on missing human data.
5. **Statistical rigor**: Holm correction, power limitation acknowledgement, and associational framing (no causal claims) added in Phase 7.
6. **Duplicate contracts**: the prior draft's redundant `drift_result.schema.yaml`, `log.schema.yaml`, `taxonomy.schema.yaml` are consolidated into four schemas.
