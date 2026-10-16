# Tasks: Do distilled structural text features add predictive value beyond dense text features for the corpus overlap/CPU-score label?

**Inputs**: `spec.md` (amendments pending, see banner), `plan.md` (Re-plan v3), `data-model.md`, contract schemas, prior execution failures (T001/T002 unobtainable datasets).
**Scope note (from plan v3)**: The original visual-encoder mechanism is NOT EXECUTABLE — no verified dataset contains page images + layout annotations. This task list implements the reframed study: deterministic structural features of text as distillation targets, incremental-value evaluation against a per-seed re-trained text-only baseline. All findings are associational (FR-006). FR-008's independence claim is recorded as not supportable; the honest substitute (incremental predictive value) is executed instead.

## BLOCKING PREREQUISITES (flagged for kickback — tasks must not execute until resolved)

1. **Verified dataset URL (plan-root cause)**: plan.md's verified-datasets entry is a blank placeholder. A concrete, execution-verified parquet URL MUST be inserted into plan.md's verified-datasets block before T001 can run. T001 below detects this condition and fails loudly with an explicit message; it never substitutes a guessed URL or synthetic data.
2. **Spec amendments (spec-root cause)**: spec.md still mandates the visual-encoder mechanism (FR-001), "predicted visual latents" (FR-004), table-QA reasoning tasks (FR-005 / ReasoningTask / US-3), the cosine/KL divergence check (US-1 Scenario 2), MSE ≥5% lower at p<0.05 vs random init (US-2 Scenario 1), the `llmXive-layout-distillation`/`pubmed-layout` fallback chain (Assumptions), and the 50M-parameter Transformer DistilledModel / VisualLatent entities (Key Entities). These MUST be amended per plan.md's "Required spec amendments" table before this task list can claim full spec coverage. Until then, coverage-table rows below are marked **[pending spec amendment]**.
3. **Constitution Principle VII (constitution-root cause)**: the ratified Principle VII requires the visual-latent distillation gain that this reframed study does not execute. The amendment flagged in plan.md's Constitution Check MUST be ratified before T003–T012 execute; an unratified amendment cannot authorize the deviation.
4. **Contract path (plan-root cause)**: plan.md's Project Structure tree places contracts under `specs/001-llmxive-layout-distillation/contracts/`; the canonical location (used by data-model.md, the read-only schemas, and every task below) is `specs/001-llmxive-follow-up-extending-scalable-vis/contracts/`. plan.md's tree must be corrected to match.

**Pre-registered constants (fixed by this task list; no implementation-time discretion)**:
- `DATASET_URL`: literal URL constant in `src/data/download.py`; MUST be populated from plan.md's verified-datasets block once kickback item 1 is resolved. Empty constant ⇒ loud failure.
- `MIN_VALID_ROWS = 1000`: pre-registered minimum schema-valid row count for the FR-007/SC-006 gate (a code constant in `src/data/download.py`, recorded — not defined — in `provenance.json`).
- `SEEDS = [42, 43, 44]`: fixed seed list for all multi-seed stages (T005, T006, T007, T009); the pairing sample size for all paired tests is exactly 3.
- `LEAKAGE_THRESHOLD = 0.95`: pre-registered leakage-gate threshold (|Spearman rho| between label and surface text-similarity features); justification: a correlation ≥ 0.95 indicates the label is near-deterministically reconstructible from surface text similarity, making any augmented-vs-baseline delta uninterpretable as structural-feature value.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US-1] Download and validate the single verified real dataset, and record its provenance.
  **Implementation**: `src/data/download.py` defines the literal constant `DATASET_URL` (populated from plan.md's verified-datasets block after kickback item 1 is resolved). If `DATASET_URL` is empty or the fetch fails, the script MUST `raise` and exit non-zero with the message `VERIFIED DATASET URL MISSING/UNREACHABLE — plan.md verified-datasets block must supply a concrete URL; no substitution permitted` — NO synthetic/mock fallback, ever, and NO guessed hub id or mirror. On success it computes the SHA-256 of the raw file, counts rows, inventories columns, and records label semantics (which column is the label, what it measures, from which source columns) into `data/raw/provenance.json`. `provenance.json` also records the pre-registered constants `MIN_VALID_ROWS = 1000` and `SEEDS = [42, 43, 44]` verbatim (recorded, not redefined).
  **Verification**:
  - `data/raw/mixsub_overlap.parquet` exists and its SHA-256 in `data/raw/provenance.json` matches a re-computation.
  - `provenance.json` contains `sha256`, `n_rows`, `columns`, a `label_semantics` block, and the recorded `min_valid_rows: 1000` and `seeds: [42, 43, 44]`.
  - Unit test `src/tests/test_download.py` asserts the file loads via pyarrow, the row count matches provenance, and that an empty `DATASET_URL` constant produces the loud failure (non-zero exit, explicit message).
  - The FR-007 gate threshold is the pre-registered constant 1000 — NOT a value this task invents.

- [ ] T002 [US-1] Preprocess the raw parquet into schema-valid `DocumentPair` records.
  **Implementation**: `src/data/preprocess.py` reads `data/raw/mixsub_overlap.parquet`, validates every row against `specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml` (jsonschema), assigns `doc_id`, `source_url`, `row_index`, drops empty-text rows with a logged warning, and writes `data/processed/document_pairs.parquet`. No OCR, no image handling — the visual pipeline is out of scope per plan v3.
  **Verification**:
  - Every row passes the `DocumentPair` schema; `n_valid_rows` written to `data/processed/preprocess_stats.json`.
  - Re-running is deterministic (byte-identical parquet).
  - If `n_valid_rows < MIN_VALID_ROWS (1000, the pre-registered constant in `src/data/download.py`, not a provenance-defined value), the script exits non-zero with the FR-007 failure message naming both the count and the constant.
  - Unit test `src/tests/test_preprocess.py` passes, including the below-minimum failure path.

- [ ] T003 [US-1] Implement the deterministic structural-feature extractor with a non-degeneracy gate (Phase 1 + 1b; reframed FR-001 [pending spec amendment]).
  **Implementation**: `src/features/structure.py` computes a fixed-dimension deterministic structural feature vector per document from plain text: line-count statistics, line-length distribution, newline/whitespace ratios, punctuation densities, token-length distribution, indentation/blank-line patterns. Pure functions, no randomness. If the primary line-structure features are degenerate (near-constant variance across the corpus), fall back to the newline-free feature set (whitespace/punctuation/token-length distributions); if that is ALSO degenerate, terminate with a clear scope-mismatch error rather than run a vacuous study. Write `data/processed/document_pairs_with_latent.parquet` (adds the `structural_latent` column, dimension D recorded in `provenance.json`) ONLY if the gate passes.
  **Verification**:
  - `structural_target_degeneracy` block (passed, fallback_used, min_feature_variance, n_near_constant_features) written to `data/processed/degeneracy_report.json`.
  - Every row's `structural_latent` has dimension D, no NaNs.
  - Unit tests `src/tests/test_structure.py` cover determinism (same input → same vector) and the degeneracy gate logic.

- [ ] T004 [US-2] Generate deterministic train/val/test splits, author the initial quickstart, and run a thin end-to-end analysis on a small real sample.
  **Implementation**: `src/utils/seed.py` pins seeds; `src/utils/split_generator.py` reads `document_pairs_with_latent.parquet` and writes `data/splits/splits.yaml` (ratios 0.8/0.1/0.1, seed 42, deterministic — re-run must be byte-identical). T004 also authors the feature's `quickstart.md` documenting the runnable commands (starting with the smoke command below; later tasks append their stages). Then a thin end-to-end driver `src/cli/run_pipeline.py --smoke` executes: load splits → extract features → fit a small ridge downstream head on the train split → report val metric for (a) text-embedding-only and (b) text-embedding ⊕ structural-latent arms, writing real result rows to `data/results/smoke_results.json`.
  **Dependencies**: T004 hard-depends on T003's output `document_pairs_with_latent.parquet` and on T003's degeneracy gate having passed; it is NOT order-independent of T003 (the former [P] tag is removed for this reason — [P] on T001/T002 denotes only parallel-safety between those two siblings).
  **Verification**:
  - `data/splits/splits.yaml` exists; split sizes within ±1 document of target ratios; deterministic re-run.
  - `data/results/smoke_results.json` contains real computed metrics (no placeholders) for both arms on real data.
  - `quickstart.md` exists and documents `python src/cli/run_pipeline.py --smoke`; running that exact command exits 0 end-to-end on real data.

**Checkpoint**: The documented smoke command executes on real data and its numerical outputs are checkable. No report writing from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US-2] Train the distillation student (text → structural latent) across the fixed seed list, as a SANITY CHECK only (FR-002, FR-003; SC-001 downgraded [pending spec amendment], SC-004, SC-005, SC-007).
  **Implementation**: `src/models/distilled.py` trains a compact CPU-tractable student (hashed/TF-IDF text features → small MLP, ≤50M parameters, in practice far smaller) with MSE loss on the train split, invoked via the CLI stage defined by T004's driver: `python src/cli/run_pipeline.py --stage distill --seeds 42,43,44` (the driver's `--stage distill` subcommand is implemented in this task; `--seeds` defaults to the pre-registered list and rejects any other value). The seed list is FIXED at exactly [42, 43, 44] — no runtime judgment call. Checkpoints under `artifacts/models/distilled_{seed}/`. Memory tracked via psutil; wall-clock recorded. The comparison arm is a frozen-random-head student with identical architecture and same seed. Per-seed metrics (val MSE, frozen-random-init MSE, val/train loss ratio, peak RAM, runtime) are written to `artifacts/eval/distill_metrics_{seed}.json`, and aggregated into `artifacts/eval/distill_summary.json` (including the paired test result and the SC-007 ratios).
  **Decision rule (explicit)**: the sanity check PASSES iff p < 0.025 (Bonferroni; paired t-test or Wilcoxon per Shapiro–Wilk across the 3 seeds) AND mean val MSE < mean frozen-random-init MSE. If it FAILS, the pipeline TERMINATES with non-zero exit and the message `distillation sanity check failed` — it does not continue with a flag, because a student that cannot even fit a deterministic function of its own input invalidates all downstream stages.
  **Verification**:
  - `artifacts/eval/distill_summary.json` records mse_val_mean, mse_random_init_mean, p_value, test_name, alpha = 0.025, `is_sanity_check_only: true` (explicitly NOT hypothesis evidence — the target is a deterministic function of the input; convergence is near-tautological), and per-seed val_loss/train_loss ratios.
  - Peak RAM ≤ 7 GB (SC-004); total runtime ≤ 21,600 s (SC-005), recorded in `artifacts/eval/resources.json`.
  - val_loss/train_loss ratio ≤ 2.0 per seed (SC-007), recorded in `artifacts/eval/distill_summary.json`.
  - Exactly 3 checkpoints (seeds 42, 43, 44) exist.

- [ ] T006 [US-3] Train the per-seed re-trained text-only downstream baseline (FR-009).
  **Implementation**: `src/models/baseline.py` builds the text-only downstream model (dense text embedding, e.g., TF-IDF or hashed n-gram features, + ridge head), re-initialized and re-trained independently for EVERY seed in the fixed list [42, 43, 44]. Checkpoints under `artifacts/models/baseline_{seed}/`.
  **Verification**:
  - Exactly 3 baseline checkpoints (one per seed), each with recorded val metric on the val split and test metric on the test split, written to `artifacts/eval/baseline_{seed}.json`.
  - No OOM; peak RAM ≤ 7 GB.
  - The pairing unit for all downstream statistics is the seed (n = 3, fixed).

- [ ] T007 [US-3] Label-semantics and leakage pre-check, then downstream evaluation: augmented vs baseline (FR-004 reframed [pending spec amendment], FR-005 reframed [pending spec amendment], FR-006; SC-002, SC-003).
  **Implementation**: `src/eval/downstream.py` first runs the pre-registered leakage gate: Spearman correlation between the label and surface text-similarity features of the input text, against the PRE-REGISTERED constant `LEAKAGE_THRESHOLD = 0.95` (fixed in the task and as a named constant in the script; justification recorded in the output block: |rho| ≥ 0.95 means the label is near-deterministically reconstructible from surface text similarity, so any delta is uninterpretable). If `is_trivial_function_of_text: true`, the downstream delta is reported as uninterpretable and NO gain is claimed — the finding itself is reported honestly. Otherwise, per seed in [42, 43, 44]: predict structural latents with the T005 checkpoint, concatenate text embedding ⊕ predicted latent, train an identical ridge head (val-tuned, test-reported), and compare against the T006 per-seed baseline.
  **Verification**:
  - `label_semantics` and `leakage_check` blocks populated with real measured values, including `threshold: 0.95` and the justification string.
  - Per-seed `metric_baseline`, `metric_augmented`, `delta` written to `artifacts/eval/downstream_{seed}.json`; deltas paired across the 3 seeds.
  - Negative deltas (null results) are reported with delta and p-value, not suppressed (US-3 scenario 3).

- [ ] T008 [US-3] Statistical analysis with Bonferroni correction and associational framing (FR-005, FR-006; SC-003 [stricter-than-spec: α = 0.025 < 0.05, pending spec amendment]).
  **Implementation**: `src/eval/stats.py` runs the paired t-test across the 3 fixed seeds on the downstream deltas (Wilcoxon fallback if Shapiro–Wilk rejects normality), at Bonferroni-corrected α = 0.025 for the primary hypothesis. Includes a stated power note (fixed n = 3 seeds, observed effect size) rather than an invented justification. All output text uses associational framing; no causal language.
  **Verification**:
  - `artifacts/eval/results.json` validates against `specs/001-llmxive-follow-up-extending-scalable-vis/contracts/results.schema.yaml` (jsonschema check in `src/tests/test_results_contract.py`).
  - `downstream.p_value`, `test_name`, `alpha` populated; `framing: "associational"`; `interpretable` reflects the leakage gate.

- [ ] T009 [US-2] Incremental-value ablation and descriptive collinearity (FR-008 reframed — independence NOT EXECUTABLE).
  **Implementation**: `src/eval/ablation.py` trains a latent-only downstream arm (predicted structural latent alone, same ridge head) per seed in [42, 43, 44] and compares it to the T006 baseline. It also computes mutual information (bits) and Pearson r between predicted latents and the baseline text embeddings, reported DESCRIPTIVELY as confounded-by-construction — never as an independence test.
  **Verification**:
  - `ablation_incremental_value` block (latent_only_mean, p_value_vs_baseline, `independence_claim_supportable: false`) and `independence_descriptive` block (mutual_information_bits, pearson_r) in `artifacts/eval/results.json`.
  - The results file and summary explicitly state the original FR-008 independence conclusion is not supportable in this design.

- [ ] T010 [US-3] Resource and reproducibility checks across the full pipeline.
  **Implementation**: The pipeline driver records peak RAM (psutil) and wall-clock for every stage into `artifacts/eval/resources.json`; asserts peak_ram_gb ≤ 7 (SC-004) and runtime_seconds ≤ 21,600 (SC-005). Re-running the full documented workflow from `data/raw/mixsub_overlap.parquet` reproduces `artifacts/eval/results.json` numerically (same seeds → same metrics within float tolerance).
  **Verification**:
  - `resources` block in `results.json` within limits.
  - Deterministic re-run check documented in `artifacts/eval/repro_check.md` with actual second-run values.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 [US-3] Generate summary tables and figures from the validated outputs.
  **Implementation**: `src/eval/report.py` reads `artifacts/eval/results.json` (single source of truth) and produces `figures/per_seed_downstream.png` (per-seed baseline vs augmented metrics), `figures/distillation_sanity.png` (MSE curves / sanity comparison), and `data/results/summary_table.md` (all SC-001–SC-007 outcomes with the sanity-check downgrade and scope limitation stated).
  **Verification**:
  - Every number in the tables/figures traces to `results.json`; no hard-coded values.
  - The scope-limitation statement (visual latents infeasible; structural features used; FR-008 independence not executable) appears in the summary.

- [ ] T012 [US-3] Write the methods/results account and paper-stage handoff.
  **Implementation**: `artifacts/report/final_report.md` documents: the reframed research question and why the original was unanswerable with obtainable data; methods (extractor, student, arms, pairing unit, pre-registered constants); results with exact artifact citations; negative/null findings and limitations (near-tautological sanity check, confounded-by-construction collinearity, power note at fixed n = 3, associational framing per FR-006); and a named paper-stage handoff (layout, PDF compilation, peer review belong to the paper pipeline — requirements preserved there, not duplicated here).
  **Verification**:
  - Every cited artifact file exists; report contains no numeric value without provenance.
  - `quickstart.md` (authored in T004, extended by later stages) documents the single runnable command for the full workflow; re-running it confirms all tests (`src/tests/`) pass and artifact checks succeed.

---

## Dependencies and requirement coverage

**Execution order**: T001 → T002 → T003 → T004 → (T005, T006 parallel) → T007 → T008 → T009 → T010 → T011 → T012. T005/T006 are independent of each other but both precede T007 (downstream needs per-seed checkpoints from both). T004 hard-depends on T003 (gate + latent parquet); [P] on T001/T002 denotes parallel-safety between those siblings only.

| Requirement | Task(s) | Demonstrating command / artifact |
|---|---|---|
| FR-001 (reframed: structural targets) [pending spec amendment] | T001–T003 | `python src/cli/run_pipeline.py --smoke` |
| FR-002, FR-003 | T005 | `python src/cli/run_pipeline.py --stage distill --seeds 42,43,44` (CLI stage defined in T005); checkpoints `artifacts/models/distilled_{42,43,44}/` |
| FR-004 (reframed) [pending spec amendment] | T007 | `artifacts/eval/downstream_{seed}.json` |
| FR-005 (reframed), FR-006 | T007, T008 | `artifacts/eval/results.json` |
| FR-007 (single-source, pre-registered minimum 1000) | T001, T002 | `provenance.json` + failure-path test in `test_preprocess.py` |
| FR-008 (reframed: incremental value) | T009 | ablation block of `results.json` |
| FR-009 | T006 | `artifacts/models/baseline_{42,43,44}/` |
| SC-001 (sanity), SC-004, SC-005, SC-007 | T005, T010 | `artifacts/eval/distill_summary.json` (per-seed MSE, ratios, paired test) and `artifacts/eval/resources.json` |
| SC-002, SC-003 [α = 0.025, stricter than spec's 0.05; pending spec amendment] | T007, T008 | `results.json` downstream block |
| SC-006 (minimum = 1000, pre-registered) | T001, T002 | `provenance.json` + FR-007 gate |

**Revision behavior**: Prior T001–T013 are superseded by this re-plan v3 — the datasets they named (`allenai/pubmed-layout`, DocVQA, ResNet-18 visual latents) are unobtainable or out of reframed scope; no completed work existed to preserve (all tasks were rejected/failed). This list is the smallest complete study answering the reframed question. Plan/spec/constitution root causes (blank dataset URL, unamended spec texts, Principle VII conflict, contract-path divergence) are flagged in the BLOCKING PREREQUISITES banner for kickback; they cannot be resolved by editing tasks.md alone.