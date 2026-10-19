# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

**Inputs**: active `spec.md`, `plan.md` (revision 2), data-model and contracts in `specs/001-investigating-the-relationship-between-b/`, and the rejected-execution feedback on the prior T001 (guessed OpenNeuro dataset IDs failed; only the `clane9/openneuro-fslr64k` parquet mirror is a verified real source).

**Re-scope note (from plan.md, must be honored):** the originally named OpenNeuro datasets ds000246/ds001600 have no verified downloadable source. The single verified real fMRI source is the `clane9/openneuro-fslr64k` parquet mirror (real, pre-normalized fsLR-64k CIFTI-format BOLD timeseries). The primary deliverable is a reproducible descriptive characterization of time-varying **vertex-block connectivity descriptors**; the skill-association stage is conditional and its halt-with-explicit-message path is the EXPECTED outcome. No synthetic behavioral scores, no fabricated data, no fallback to invented mirrors. All descriptors are labeled vertex-block descriptors, never brain-network properties.

## Spec-revision kickbacks (spec/plan-rooted; NOT resolvable in this artifact)

The following contradictions are rooted in `spec.md` (and one path in `plan.md`), which this tasks revision cannot edit. They are recorded here verbatim-in-substance so the spec stage resolves them; the tasks below implement the honest, verified-data forms without weakening any FR beyond what plan.md already routed through the constitution amendment procedure:

1. **FR-001** still names ds000246/ds001600, which have no verified source; the spec must name the `clane9/openneuro-fslr64k` parquet mirror (plan scope-gap #1).
2. **FR-002 / Constitution VI** mandate FSL/AFNI and AAL/Schaefer, neither installable/downloadable from any verified source; the Python bandpass + deterministic 100-block scheme is the routed amendment (plan scope-gaps #2, #4).
3. **FR-004/FR-009/SC-001** primary outcome (expert blind ratings) has no verified data source; SC-001 is unmeasurable on the expected path (plan scope-gap #3).
4. **SC-002** needs a conditional/fallback form (`not_computable_no_skill_proxy` on the expected path; plan scope-gap #5).
5. **FR-007** requires a task-condition comparison figure; the conditional single-group fallback must be defined in the spec (plan scope-gap #5).
6. **FR-010/SC-005** abort scope must be revised to the association-stage-only abort this plan implements; the "[deferred]" power target must be filled in (tasks pin 0.80).
7. **FR-005**'s "substantial number of permutations" should state 1000 explicitly (SC-001 and the plan already pin 1000).
8. **Edge case (motion)**: the spec's FD > 0.5 mm rule needs an amplitude-based fallback definition for data without an FD column; the tasks pin a DVARS-like MAD threshold (below).
9. **Spec directory path**: plan.md's Project Structure says `specs/001-gene-regulation/` and spec.md's header carries a leftover `001-gene-regulation` branch name, while the authoritative directory (and all contracts) is `specs/001-investigating-the-relationship-between-b/`; plan.md/spec.md headers must be corrected. All task paths below use the authoritative directory.

---

## Phase 1: Setup and first end-to-end analysis

- [X] **T001 [P1] [US1]** Download the verified real fMRI parquet shard directly via `huggingface_hub.hf_hub_download` from the `clane9/openneuro-fslr64k` repository (test split, shard `test-00000-of-00016.parquet`), and record its SHA-256 checksum. This redoes the rejected prior T001 — the guessed `openneuro/ds000246` / `openneuro/ds001600` fetch MUST NOT be retried; the verified parquet source is the sole input. The loader must FAIL LOUDLY on any fetch error (raise, never fall back to synthetic or bundled data).
  *Artifact paths*: `data/raw/test-00000-of-00016.parquet`, `data/checksums.json` (SHA-256 of the raw file), `data/raw/column_inventory.json` (real column names plus which of `subject_id`, task labels, skill proxies, and FR-011 covariates — age, FD, years of training, instrument, genre, practice intensity, education — actually exist, AND `available_subject_count`: the number of distinct subject IDs in the shard — this anchors the SC-005 power comparison and the Constitution VII N≥20 floor check).
  *Verification*:
  &nbsp;&nbsp;• `python code/download_openneuro.py` exits 0 and the parquet file exists and is non-empty.
  &nbsp;&nbsp;• `data/checksums.json` contains the SHA-256 of the downloaded file.
  &nbsp;&nbsp;• `data/raw/column_inventory.json` lists the real parquet schema, explicitly marks each expected behavioral field as present or absent, and records `available_subject_count` as a positive integer equal to the distinct subject IDs actually present in the parquet (no fabricated columns, no guessed count).
  &nbsp;&nbsp;• `pytest tests/test_download.py` asserts the file loads with pyarrow, that the inventory reflects the actual schema, and that `available_subject_count` matches a pyarrow-computed distinct-subject count.

- [X] **T002 [P1] [US1]** Establish the code layout and runnable entry point per the plan (`code/config.py` with pinned seeds, window/step parameters, and the QC threshold constants defined in T003; `code/requirements.txt`; `code/run_all.py` CLI orchestrator) and document the exact end-to-end command in the active feature's `quickstart.md`.
  *Artifact paths*: `code/config.py`, `code/requirements.txt`, `code/run_all.py`, `specs/001-investigating-the-relationship-between-b/quickstart.md`.
  *Verification*:
  &nbsp;&nbsp;• `python code/run_all.py --help` exits 0.
  &nbsp;&nbsp;• `quickstart.md` contains the exact CLI invocation runnable on a fresh CPU-only runner with the pinned dependencies.

- [ ] **T003 [P1] [US1]** Implement vertex-block extraction and cleaning in `code/extract_rois.py`: stream the parquet in row-group batches (never loading the full shard into RAM), map fsLR vertices to the deterministic 100-block contiguous-vertex scheme (documented in the code; NOT a neuroanatomical parcellation), compute the mean signal per block per timepoint, bandpass filter 0.01–0.1 Hz, and write per-subject QC records. This is the honest Python adaptation of FR-002 preprocessing (the verified data are already spatially normalized; FSL/AFNI cannot be installed from any verified source — deviation routed through the constitution amendment procedure per plan.md). <!-- FAILED-IN-EXECUTION: tests/test_extract.py exit=1 -->
  *QC bad-volume rule (fully specified so the edge case is testable)*: if a real FD column exists, a volume is bad when FD > 0.5 mm (spec edge case). If no FD column exists (expected path), a volume is bad when its DVARS-like statistic — the root-mean-square frame-to-frame change in the 100 block-mean signals, standardized against the run median and MAD-based robust SD — exceeds run_median + 3 × (1.4826 × MAD). A subject is excluded when >20% of volumes are bad. All threshold constants are pinned in `code/config.py`.
  *Artifact paths*: `data/derived/roi_timeseries_<subject>.csv` (long format conforming to `specs/.../contracts/roi_timeseries.schema.yaml`), `data/derived/qc_<subject>.json` (fraction of bad volumes, exclusion flag and reason, motion-proxy description — FD column if present, else the DVARS-like rule above with its thresholds).
  *Verification*:
  &nbsp;&nbsp;• Each subject's timeseries has exactly 100 distinct `roi_id` values (`roi_1`…`roi_100`) and rows pass `roi_timeseries.schema.yaml` (`pytest tests/test_extract.py`).
  &nbsp;&nbsp;• Edge case: subjects with >20% bad volumes (by the FD rule if an FD column exists, else by the DVARS-like MAD rule above) are flagged `excluded=true` with a logged reason in their QC record and appear in the exclusion log consumed by downstream tasks; a unit test injects a series with known bad volumes and asserts the exclusion fires.
  &nbsp;&nbsp;• Edge case: missing task labels are detected from `column_inventory.json` and recorded — the conditional association stage (T006) uses this, per the spec's edge-case rule; the descriptive pipeline proceeds.
  &nbsp;&nbsp;• Peak memory stays under 7 GB (row-group streaming; measured and recorded in T010's `results/performance_metrics.txt`).

- [ ] **T004 [P2] [US2]** Implement sliding-window dynamic connectivity and vertex-block descriptors in `code/connectivity.py` and `code/graph_metrics.py`: rectangular-window Pearson correlation with Ledoit-Wolf shrinkage (default window 45 s, step 10 s, minimum 30 timepoints per window, windows below the minimum skipped and logged), then weighted undirected graph descriptors per window — global efficiency, seeded Louvain modularity, participation coefficient — labeled throughout as **vertex-block connectivity descriptors**, not brain-network properties. Run it end-to-end on all real subjects in the shard. <!-- FAILED-IN-EXECUTION: code/connectivity.py exit=1 -->
  *Artifact paths*: `data/derived/metrics_<subject>.csv` (one row per window, conforming to `specs/.../contracts/network_metrics.schema.yaml`).
  *Verification*:
  &nbsp;&nbsp;• `pytest tests/test_connectivity.py` validates schema compliance, metric ranges, window indexing starting at 0, and the ≥30-timepoint rule.
  &nbsp;&nbsp;• A focused unit test recovers a known correlation from a constructed input through the Ledoit-Wolf + Pearson path.
  &nbsp;&nbsp;• Descriptors are computed for every non-excluded subject in the shard, producing real result rows (first end-to-end analysis on real inputs).

**Checkpoint**: `python code/run_all.py --stage download --stage extract --stage metrics` executes on the real verified shard and its numerical outputs can be checked. No report writing from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] **T005 [P2] [US2]** Implement PCA dimensionality reduction in `code/dimensionality.py`: stack window-descriptor vectors across subjects, retain components explaining ≥80% cumulative variance, and write per-subject PC scores.
  *Artifact path*: `data/derived/pca_scores.csv` (conforms to `specs/.../contracts/pca_scores.schema.yaml`).
  *Verification*:
  &nbsp;&nbsp;• `pytest tests/test_pca.py` checks orthogonality of components, the ≥80% variance threshold, and schema compliance (per-subject `n_components_retained`, `variance_explained_total`, dynamic `pc_scores` mapping).

- [ ] **T006 [P2] [US2]** Implement the a priori power analysis and the conditional association stage in `code/analysis.py`. **Power analysis (reporting-only, never aborts the pipeline; satisfies FR-010 as AMENDED pending the spec revision routed in plan.md's scope-gap list — the spec's original whole-pipeline abort is NOT claimed as satisfied):** target power = 0.80 (the value FR-010 left "[deferred]"; pinned here so the computation is deterministic), Cohen's d = 0.5 converted to r ≈ 0.243, required N for the partial-correlation/F-test at α = 0.05 computed via `statsmodels.stats.power`, written to `results/power_analysis.json` with required N vs. available N (available N taken from T001's `available_subject_count` in `column_inventory.json`), a `power_status` field, and an explicit `n_ge_20_floor_check` field recording whether available N meets the Constitution VII N≥20 presupposition (reported honestly if below). **Ordering (two-form, mirroring T009):** in the ratified-amendment path the power analysis runs after T005; in the amendment-rejection path the power-analysis portion of T006 runs after T001 ONLY — it consumes no PC scores — so the rejection-path manifest's `power_status` always has a producer. **Association stage (ratified path only):** executes ONLY if a real skill-proxy column exists in the column inventory (priority: expert rating > task condition > years of training, per FR-004); OLS regression of PC scores on the proxy with age, FD, and all present FR-011 covariates; Freedman–Lane residual permutation (1000 permutations, seeded, per FR-005 as pinned by SC-001) for raw p-values; Benjamini–Hochberg FDR across PCs; null results reported and flagged as valid, never treated as failure. If no skill proxy exists — the EXPECTED path — the stage halts with an explicit logged data-mismatch message and records the scope gap; downstream stages proceed. If available N is below required N, the association stage is skipped with an `underpowered_association_skipped` marker (SC-005 scope as amended: abort applies to this stage only).
  *Artifact paths*: `results/power_analysis.json` (always produced, both paths); `results/regression_results.csv` (only if the association stage ran, conforming to `specs/.../contracts/regression_results.schema.yaml`).
  *Verification*:
  &nbsp;&nbsp;• `pytest tests/test_analysis.py` validates the power computation against a deterministic reference: required N for r = 0.243, α = 0.05, power = 0.80 via statsmodels, cross-checked against the Fisher-z closed-form approximation; and, on a constructed dataset with a known effect, that the Freedman–Lane permutation recovers it and the FDR procedure is Benjamini–Hochberg.
  &nbsp;&nbsp;• On the expected no-proxy path, the run exits 0 with the halt message logged and no fabricated `regression_results.csv`.
  &nbsp;&nbsp;• No synthetic behavioral scores are ever generated (grep-level check: no `random`/mock skill columns in the code path).

- [ ] **T007 [P3] [US3]** Implement the sensitivity analysis in `code/sensitivity.py`: re-run descriptor computation (and the association stage if it ran) for window ∈ {30, 45, 60} s × step ∈ {5, 10} s and report mean, SD, and range of descriptor values (and correlation coefficients if T006 ran) across the 6 combinations. <!-- FAILED-IN-EXECUTION: code/sensitivity.py exit=1 -->
  *Artifact path*: `results/sensitivity_summary.csv` (exactly 6 rows for the parameter grid).
  *Verification*:
  &nbsp;&nbsp;• `pytest tests/test_sensitivity.py` asserts the 6 combinations completed without error and the summary contains the required statistics.
  &nbsp;&nbsp;• If T006 did not run, the correlation-SD field is written as `not_computable_no_skill_proxy` (SC-002 as amended pending spec revision: explicitly unmeasurable on the expected path — stated honestly, not faked; see kickback #4).

- [ ] **T008 [P3] [US3]** Implement visualization in `code/visualization.py`: if real task-condition labels exist, mean adjacency per condition with NetworkX graph construction and Matplotlib rendering (edge width ∝ weight, node color ∝ Louvain community) — this path satisfies FR-007 as written. If no labels exist (expected path), a single-group descriptive topology figure of the mean vertex-block descriptor graph — no group comparison and no PC-1 median split; this path satisfies FR-007 only as AMENDED (conditional fallback, plan scope-gap #5, kickback #5).
  *Artifact path*: `results/fig_network_topology.png`.
  *Verification*:
  &nbsp;&nbsp;• The PNG loads without error; `pytest tests/test_visualization.py` checks the mean adjacency has shape (100, 100) and node labels are the deterministic block IDs (labeled vertex blocks, not atlas regions).
  &nbsp;&nbsp;• The figure caption/legend carries the vertex-block-descriptor caveat.

- [ ] **T009 [P2] [US2]** Write the master manifest as the Single Source of Truth, in TWO explicitly defined forms so the unconditional-execution claim is coherent:
  **(a) Full manifest (ratified-amendment path; ordered after T004–T008):** one row per processed subject with all derived descriptors (default 45 s/10 s setting), available covariates, skill-proxy status (`skill_proxy_used` = real column name or `none`), PC scores, statistical outcomes or the halt marker, exclusion flags and reasons, and `power_status` from T006's power report.
  **(b) Rejection-path manifest (amendment-rejection path; produced after T001 and T006's power portion ONLY — both unconditional):** one row per subject in the shard with `subject_id`, `excluded=true`, `exclusion_reason='amendment_rejected_descriptive_pipeline_not_run'`, `power_status` from the power report, and no descriptor/PC fields (they have no producers in this path).
  **CSV encoding of nested fields (both forms):** the schema's object-typed fields (`pc_scores`, `fdr_p_values`) are encoded as JSON-string cells — one compact JSON object per CSV cell (e.g. `"{""pc_1"": 0.42}"` with CSV quoting); `tests/test_manifest.py` parses each such cell with `json.loads` before validating the row against `specs/.../contracts/manifest.schema.yaml`, making "syntactically valid" deterministic.
  *Artifact path*: `results/manifest.csv`, validated against `specs/.../contracts/manifest.schema.yaml` (after JSON-cell decoding).
  *Verification*:
  &nbsp;&nbsp;• `pytest tests/test_manifest.py` asserts the manifest is syntactically valid (consistent columns, no missing mandatory fields, JSON-string cells parse), contains a row for EVERY processed subject including excluded ones (SC-006), and that every figure/table in `results/` traces to manifest rows.
  &nbsp;&nbsp;• Excluded subjects appear with `excluded=true` and a non-empty `exclusion_reason`.
  &nbsp;&nbsp;• In the rejection path, form (b) is produced with the reduced column set and the test validates it accordingly.

- [ ] **T010 [P2] [validation]** Add the independent correctness and runtime checks: run the full pipeline on a representative subset and on the full shard, record total wall-clock time and peak RAM, and confirm the ≤6 h / ≤7 GB free-tier budget (SC-004). Strictly sequential with respect to T004–T009 (requires the full pipeline); must complete before T011.
  *Artifact paths*: `results/performance_metrics.txt` (`runtime_seconds`, `peak_ram_gb`), focused pytest modules under `tests/`.
  *Verification*:
  &nbsp;&nbsp;• `pytest tests/` passes with 0 failures across download, extraction, connectivity, PCA, analysis, sensitivity, visualization, and manifest contract tests.
  &nbsp;&nbsp;• Recorded `runtime_seconds` ≤ 21600 and `peak_ram_gb` ≤ 7.0 on the real shard.

## Phase 3: Reproducible results and paper handoff

*Note on user-story contiguity: US1's independently shippable unit ends at the Phase-1 checkpoint (T001–T003). T010–T012 serve the cross-story validation and reporting role for all user stories and are tagged [validation] / [reporting] accordingly.*

- [ ] **T011 [P3] [reporting]** Write a concise methods/results account in `specs/001-investigating-the-relationship-between-b/research.md` linked to the actual output files and figure: the descriptive vertex-block descriptor results, the sensitivity table, the power report, the conditional-association outcome (including the expected halt path and scope-gap statement), and the construct-validity limitations (arbitrary contiguous-vertex parcellation; descriptors not interpretable as brain-network properties; no verified skill-rating source). Describe null results, failures, and limitations honestly, with associational (non-causal) framing. Strictly sequential: runs after T010 (cites its performance record).
  *Artifact path*: `specs/001-investigating-the-relationship-between-b/research.md`.
  *Verification*:
  &nbsp;&nbsp;• Every numeric claim in the account cites or links to a row in `results/manifest.csv`, `results/sensitivity_summary.csv`, or `results/power_analysis.json`.
  &nbsp;&nbsp;• The scope-gap statement (expert ratings unavailable in any verified source; SC-001 unmeasurable on the expected path) appears verbatim in substance.

- [ ] **T012 [P3] [reporting]** Re-run the documented workflow from its declared inputs on a fresh state (delete `data/derived/` and `results/`, re-run the `quickstart.md` command), confirm all tests and artifact checks pass, and document the paper-stage handoff: the result tables, the topology figure, the sensitivity and power reports, the scope-gap statement for spec revision, and the pending constitution-amendment items (Constitution VI parcellation/preprocessing deviations; dependent-variable gap) that the paper stage must carry forward. Strictly sequential: runs after T011.
  *Artifact paths*: updated `specs/001-investigating-the-relationship-between-b/quickstart.md` (re-run record) and a handoff section in `research.md`.
  *Verification*:
  &nbsp;&nbsp;• The re-run reproduces byte-identical `results/manifest.csv` descriptor values (pinned seeds) and exits 0.
  &nbsp;&nbsp;• The handoff lists every artifact the paper stage consumes and states explicitly that layout/PDF/peer-review belong to the paper pipeline.

---

## Dependencies and requirement coverage

| Requirement | Satisfied by | Order |
|-------------|--------------|-------|
| FR-001 (verified data acquisition; spec names unverified ds000246/ds001600 — kickback #1) | T001, T002 | first |
| FR-002 (preprocessing, Python adaptation per plan amendment; kickback #2) | T003 | after T001 |
| FR-003 (sliding-window Ledoit-Wolf connectivity + descriptors) | T004 | after T003 |
| FR-008 (PCA) | T005 | after T004 |
| FR-010 as AMENDED (power analysis, association-stage-scoped abort; target power 0.80; kickback #6) | T006 | ratified path: after T005. Rejection path: power portion after T001 ONLY (consumes no PC scores), so the rejection-path manifest's `power_status` always has a producer |
| FR-004, FR-005 (1000 permutations, kickback #7), FR-009, FR-011 (conditional association, permutation + FDR) | T006 | after T005 (ratified path only) |
| FR-006 (window/step sensitivity) | T007 | after T004–T006 |
| FR-007 (group comparison conditional; amended fallback, kickback #5) | T008 | after T004 |
| FR-012 (master manifest) | T009 | full form after T004–T008; rejection-path form after T001 + T006's power portion only (both unconditional producers) |
| SC-001, SC-003 (conditional on real proxy; halt path expected; kickback #3) | T006 | — |
| SC-002 as amended (conditional; not-computable marker on expected path; kickback #4) | T007 | — |
| SC-004 (CPU budget) | T010 | after full pipeline |
| SC-005 as amended (power gate scoped to association stage) | T006 | — |
| SC-006 (manifest completeness, JSON-string-cell encoding defined) | T009 | — |
| Constitution VII N≥20 floor check | T001 (records `available_subject_count`), T006 (`n_ge_20_floor_check` in power report) | after T001 |

Data flow is strictly ordered: download (T001) before extraction (T003), descriptors (T004) before PCA (T005), PCA before the association stage (T006, ratified path), and all results before figures, manifest, and the report (T008–T012). T010 → T011 → T012 are strictly sequential and non-parallelizable. Amendment-contingent tasks (per plan.md): T003–T008 and T011–T012 depend on the constitution amendment being ratified. T001–T002, the power-analysis portion of T006 (which in the rejection path runs after T001 only), and the rejection-path form of T009 (b) execute unconditionally — if the amendment is rejected, the honest deliverable is the Phase-0 run plus the rejection-path manifest and a report stating the question is unanswerable with verified data and constitution-compliant methods.

## Revision behavior

The prior tasks.md's T001 (guessed `openneuro/ds000246`/`ds001600` fetch) was rejected in execution and is replaced by the verified parquet source per plan.md revision 2. The prior T002 (FSL/AFNI/Nipype preprocessing, Schaefer atlas) is replaced by the honest Python bandpass + deterministic 100-block scheme because no verified FSL/AFNI installer or atlas source exists and the verified data are pre-normalized — these deviations are routed through the constitution amendment procedure, not silently planned around. The prior T007's high/low-skill group comparison is replaced by the conditional/single-group visualization because no verified skill labels exist; a PC-1 median split would compare descriptors to themselves. This revision additionally: records `available_subject_count` (T001) and the N≥20 floor check (T006); pins target power 0.80 and a deterministic statsmodels reference check (T006); specifies the DVARS-like MAD bad-volume rule (T003); fixes the T003→T010 memory cross-reference; defines the two-form manifest with unconditional producers and the JSON-string-cell encoding for nested fields (T009); assigns concrete priorities and sequential semantics to T010–T012; and annotates FR-005/FR-007/FR-010/SC-002 coverage as amended-pending-spec-revision rather than claiming the unamended spec text is satisfied. All scientific requirements from the specification are preserved or their unmeasurability is stated honestly; nothing is fabricated.