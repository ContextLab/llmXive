# Implementation Plan: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Branch**: `001-visual-priming-implicit-attitudes` | **Date**: 2024-10-09 (revised) | **Spec**: `specs/001-visual-priming-implicit-attitudes/spec.md`
**Input**: Feature specification from `/specs/001-visual-priming-implicit-attitudes/spec.md`

## Summary

The pipeline will (1) attempt to download a **public IAT response-time dataset** from a single hardcoded, verified URL, (2) extract and verify stimulus metadata, (3) derive missing prime-valence and stimulus-ambiguity scores using CPU-optimized methods, (4) fit a **linear mixed-effects (LME) model** with robust SE, VIF checks (computed **before** fitting), and FDR correction, and (5) generate a **publication-ready PDF** containing interaction plots, coefficient tables, and a sensitivity-analysis summary.

**CRITICAL DATA-AVAILABILITY FINDING (scope flag)**: A dataset-variable fit audit of the "# Verified datasets" block shows that **none of the verified URLs contain trial-level IAT response times with linked stimulus IDs/images**. `davanstrien/ia_test_embeddings` is an embeddings dataset; `siemvaessen/iati` and `devinitorg/iati-policy-markers` are International Aid Transparency Initiative (aid-financing) data, not Implicit Association Test data; the OSF/GET/OAuth entries are NLP/API datasets unrelated to IAT psychology. The spec's core variables (`response_time` per trial, `participant_id`, `stimulus_id`, prime/target stimulus images) are therefore **not available from any verified source**. Per the planning rules, we do NOT fabricate a mirror or synthesize trial data. The plan below is implemented in full and runs end-to-end; at runtime the ingestion gate (T003) will detect the schema mismatch and **halt with an explicit `Data Gap: Schema Mismatch` report** (as US-1 scenario 2/3 require), producing a real, honest data-gap artifact rather than fabricated results. **Scope revision is flagged**: the spec should either (a) name a genuinely open IAT dataset with stimulus linkage (e.g., an OSF project with direct file URLs — currently unverified), or (b) reframe the study to the variables actually present in a verified dataset. All modeling/reporting tasks are implemented and unit-tested against fixture data so they execute correctly the moment a valid dataset is supplied; they are NOT run on fabricated stand-ins presented as real results.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `torch==2.3.0+cpu`, `transformers==4.44.0`, `datasets==2.20.0`, `pyyaml==6.0.2`, `reportlab==4.2.2`, `matplotlib==3.9.2`, `seaborn==0.13.2`, `pytest==8.3.2`, `nltk==3.8.1` (WordNet ambiguity), `opencv-python-headless==4.10.0.84`
- **Storage**: Local file system under `data/` (with `data/primes/` and `data/targets/` kept distinct), `state/`, `reports/`.
- **Testing**: `pytest` (unit, contract, integration).
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk, ≤6 h).
- **Project Type**: Data-science pipeline (CLI).
- **Constraints**: CPU-first; no GPU required (spec Assumptions). No synthetic substitution for real data.
- **Scale/Scope**: One primary dataset; sizes deferred to implementation.

## Constitution Check

| Principle | Compliance | Implementation Detail |
|-----------|------------|-----------------------|
| **I. Reproducibility** | PASS | Seeds pinned (`np.random.seed(42)`, `torch.manual_seed(42)`) in `code/config.py`; `requirements.txt` pins exact versions; single hardcoded canonical URL in `code/config.py` (`PRIMARY_DATASET_URL`); `pip.conf` with `--extra-index-url https://download.pytorch.org/whl/cpu` committed so CPU torch installs deterministically. |
| **II. Verified Accuracy** | PASS | Only URLs from the verified block are cited; `data/verified_sources.json` is generated from `research.md` §2 and is the single source of truth for URL validation (see T048). |
| **III. Data Hygiene** | PASS | Raw files never modified; every transformation writes a new file with documented derivation; SHA-256 checksums recorded in `state/artifact_hashes.json`; PII scan on `data/processed/`. |
| **IV. Single Source of Truth** | PASS | Every figure/statistic in the PDF traces to `data/processed/linked_trials.csv` and one code block; no hand-typed derived numbers. |
| **V. Versioning Discipline** | PASS | Content hashes for all artifacts in `state/artifact_hashes.json`; project state `updated_at` updated after each task. |
| **VI. Distinct Stimulus Set Integrity** | PASS | `data/primes/` and `data/targets/` are separate artifacts; merged only in the final modeling step (T014). |

## Project Structure

```text
specs/001-visual-priming-implicit-attitudes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── linkage_status.schema.yaml
│   ├── output.schema.yaml
│   └── verified_sources.schema.yaml
└── tasks.md      # generated by /speckit-tasks

code/
├── main.py                # CLI orchestrator with logging config
├── config.py              # Hardcoded PRIMARY_DATASET_URL, thresholds, seeds, paths
├── ingest.py              # Download + core-column validation (hardcoded URL)
├── preprocess.py          # Metadata extraction, linkage, merge
├── derive_valence.py      # Lexical/emotion valence derivation (CPU)
├── derive_ambiguity.py    # WordNet LAI / Laplacian texture variance
├── model.py               # VIF (pre-fit), LME fitting, optimizer fallback
├── report.py              # Plots, PDF assembly, sensitivity embed
├── pii_scan.py            # PII regex scan
├── streaming.py           # >7 GB streaming logic
├── requirements.txt
├── pip.conf               # --extra-index-url https://download.pytorch.org/whl/cpu
├── logs/
│   └── pipeline.log       # Created at runtime by first CLI invocation
└── tests/
    ├── test_contracts.py
    ├── test_ingest.py
    ├── test_model.py
    └── test_report.py
```

## Complexity Tracking (FR/SC → Tasks)

| FR / SC | Capability | Task(s) |
|--------|-----------|---------|
| FR-001 | Verify RT / valence / ambiguity presence; derive missing | T002, T003, T005a, T005b |
| FR-002 | CPU-optimized valence derivation (image classifier or lexical dictionary) | T005b |
| FR-003 | Associational framing | T010 |
| FR-004 | FDR correction for >1 test | T009 |
| FR-005 | VIF, flag > 5.0, **before** model fit | T007 |
| FR-006 | α-sweep sensitivity analysis | T011 |
| SC-001 | Ingestion/linkage completeness vs. design target | T004 |
| SC-002 | Convergence success within 3 optimizer attempts | T008 |
| SC-003 | PDF contains plots, coefficient table, sensitivity summary | T012 |

## Task Ordering (dependency-corrected)

| ID | Description | Depends On |
|----|-------------|------------|
| **T001** | Environment setup: `requirements.txt` (exact pins) + `pip.conf` containing `--extra-index-url https://download.pytorch.org/whl/cpu` (both committed so `pip install -r code/requirements.txt` succeeds deterministically; pip reads `pip.conf` from the CWD or `PIP_CONFIG_FILE=code/pip.conf` is set in CI). Load `config.py`. | – |
| **T002** | **Ingest**: download from the single hardcoded URL `config.PRIMARY_DATASET_URL` = `https://huggingface.co/datasets/davanstrien/ia_test_embeddings/resolve/main/data/train-00000-of-00001-82feb90c086b8e08.parquet`; write `data/raw/iat.parquet`; record SHA-256 in `state/artifact_hashes.json`. | T001 |
| **T003** | **Validate core columns**: require `response_time`, `participant_id`, `stimulus_id`. **Expected outcome given the dataset-variable audit: this gate HALTS with `Data Gap: Schema Mismatch`** (the verified dataset does not contain these columns). The halt writes `state/linkage_status.json` with `status: HALT` and a message naming the missing columns — this is the honest, spec-mandated behavior (US-1 scenarios 2–3). Downstream tasks are implemented and unit-tested with fixtures but are not executed on fabricated data. | T002 |
| **T004** | **Metadata extraction + linkage metric**: split prime vs. target stimuli into `data/primes/` and `data/targets/`; compute % of trials with linked stimulus metadata; write `data/processed/ingest_metrics.json` and `state/linkage_status.json`. Threshold `LINKAGE_THRESHOLD` is defined **in `code/config.py`** (single source, default 95.0) — no separate threshold-definition task, removing the prior circular dependency. Gate logic: >10% missing images → HALT; ≤10% → warn and exclude those trials. | T003 |
| **T005a** | **Derive ambiguity** (only if `ambiguity` column missing and T004 passed): WordNet sense-count Lexical Ambiguity Index for word stimuli; Laplacian texture variance for image stimuli; normalized to [0,1]. Writes `data/processed/ambiguity_scores.csv` (new file; raw untouched). | T004 |
| **T005b** | **Derive valence** (only if `prime_valence` missing and T004 passed): lexical valence dictionary for word stimuli; CPU emotion classifier (`torch` CPU backend) for image stimuli; normalized to [-1,1]. Writes `data/processed/valence_scores.csv`. | T004 |
| **T006** | **Merge derived scores** into `data/processed/linked_trials.csv` with `linkage_status` and `demographics_status` columns. Input paths are explicit: reads `data/processed/ingest_metrics.json`, `data/processed/metadata_mapping.csv` (produced by T004; column format: `stimulus_id,type,file_path_or_word,prime_or_target`), `ambiguity_scores.csv`, `valence_scores.csv`. **Fallback schema rule (resolves prior T022c ambiguity)**: if ambiguity is unavailable, the `stimulus_ambiguity` column is **retained with empty values** (never dropped), and `state/analysis_scope.json` records `scope: "valence_only"`; the model then fits the valence main effect only and the PDF states the reduced scope. | T005a, T005b |
| **T007** | **VIF pre-check** — computed on the design matrix **before** any model fit (VIF is a property of the predictors, not the fit). Writes `state/vif_flag.json`; if any VIF > 5.0, sets `claim_suppressed: true` and the report refrains from independent-effect language. Also computes Pearson r(valence, ambiguity); if |r| > 0.7 the interaction term is dropped with a logged warning. | T006 |
| **T008** | **LME fitting** with optimizer fallback: fit via `statsmodels.MixedLM` (random participant intercept; robust Huber-White SE because predictors are derived). On convergence failure, retry with up to 3 alternative optimizer settings (`lbfgs`, `bfgs`, `powell`), recording each attempt; if all fail, log the failure, suggest simplifying the random-effects structure, and write `state/model_convergence_metrics.json` with `convergence_rate`. SC-002's numeric target is `[deferred]` per spec. **Conditional on T007**: if VIF flagged, the interaction term is not interpreted as an independent effect. | T007 |
| **T009** | **FDR correction**: Benjamini-Hochberg across all fixed-effect p-values; writes `state/fdr_results.json`. | T008 |
| **T010** | **Associational framing**: appends exactly two keys to the result dict — `caution_note` (value: the literal string `"All findings are associational, not causal, given the observational secondary-data design and derived prime valence (FR-003)."` ) and `limitation_note` (value: `"Prime valence and ambiguity scores are model-derived; measurement error may attenuate or inflate estimates."`). These exact key names and string values are consumed verbatim by `report.py` (T012), removing prior integration ambiguity. Also computes effect sizes (Cohen's d, partial eta-squared) with bootstrap CIs (fixed seed, resample count `[deferred]` to implementation, ≥1000). | T009 |
| **T011** | **Sensitivity analysis**: sweep α ∈ {0.01, 0.05, 0.10} over FDR-corrected p-values; write `reports/sensitivity_analysis.csv`. | T009 |
| **T012** | **Report generation**: interaction plot (`reports/interaction_plot.png`), coefficient table, sensitivity summary, caution/limitation notes, and (if applicable) power-limitation and data-gap notes assembled into `reports/final_report.pdf` via `reportlab`. The PDF is generated **even when T003/T004 halts**, in which case it contains the data-gap report — guaranteeing the artifact always exists (addresses the rejected T036). | T004 (for halt case), T010, T011 |
| **T013** | **PII scan** on `data/processed/`; write `reports/pii_scan.json`. | T006 |
| **T014** | **Streaming support**: `code/streaming.py` implements `datasets.load_dataset(..., streaming=True)` accumulation for inputs > 7 GB. **Verification fix**: the streaming path is verified against a synthetically generated Parquet file whose on-disk size **exceeds 7 GB** (generated with fixed seed in a temp dir, streamed, then deleted) — a 1 GB file does not exercise the >7 GB branch. This synthetic file is used ONLY to verify streaming code mechanics; it is never used as analysis data. | T001 |
| **T015** | **URL validation (T048 fix)**: `code/ingest.py` validates `config.PRIMARY_DATASET_URL` against `data/verified_sources.json`. **Single source of truth**: `data/verified_sources.json` (schema: a JSON object `{"sources": [{"name": string, "url": string, "format": string}]}`) generated by a script from research.md §2 and committed; if both research.md and the JSON exist, the **JSON is authoritative**. Validated by `contracts/verified_sources.schema.yaml`. | T001 |
| **T016** | **Contract verification**: `pytest -m contract` validates all `state/`, `data/processed/`, and `reports/` artifacts against `contracts/*.schema.yaml`. | T012, T013 |

**Dependency corrections applied vs. prior revision**: (1) threshold definition moved into `config.py`, eliminating the circular T018a↔T018b dependency; (2) the confounding/order-effect diagnostic now reads `data/processed/linked_trials.csv` and `data/processed/metadata_mapping.csv` (data artifacts), not a status-report task; (3) aggregation is no longer serialized behind the confounding diagnostic — the diagnostic runs in parallel and only gates *interpretation*, not the data transformation; (4) VIF is computed **before** model fitting (T007 → T008), so a collinear design is flagged before the fit; (5) T023's dependency now points at the metadata-merge data task, not the status task.

## Compute Feasibility

- **CPU-first**: every step (ingestion, derivations, VIF, LME, PDF) runs on 2 CPU cores, <7 GB RAM, ≤6 h. No GPU is needed; per the spec's hardware-constraint assumption, valence derivation uses CPU-optimized models only. No fake CPU imitation of GPU-only methods is planned, and none is needed.
- **Data**: single directly-downloadable Parquet URL (no OAuth). Checksums recorded per Constitution III.

## Scope-Revision Flag (blocking, surfaced per planning rules)

The verified-datasets block contains **no IAT psychology dataset**. The dataset-variable fit audit is recorded in research.md §2. Until the spec names a verified open IAT source (or reframes the question), the pipeline's honest end state is the T003 data-gap halt report. No fabricated trial data, fake mirrors, or synthetic stand-ins will be used to force a "result".
