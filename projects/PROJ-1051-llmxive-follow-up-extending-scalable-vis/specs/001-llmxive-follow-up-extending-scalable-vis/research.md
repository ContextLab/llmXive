# Research: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence" (Re-plan v3)

## Overview
Re-planned (v3) after dataset-verification failures and the methodology panel review. Previously cited datasets (`llmXive/layout-distillation`, `pubmed-layout`, `docvqa` via `load_dataset`) are not obtainable on the CI runner and are removed. The study is reframed around the single verified dataset, with deterministic text-structure targets replacing unobtainable visual latents.

**Restated research question**: do cheap structural summary features of text, distilled into a compact model, add predictive value beyond dense text features for the dataset's overlap/CPU-score label? The original visual-latent question is recorded as not answerable with obtainable data.

**Hypothesis structure**: the downstream incremental-value test is the sole primary hypothesis. The distillation MSE convergence (SC-001) is a sanity/feasibility check only — the target is a deterministic function of the student's input, so MSE convergence is near-tautological and is not presented as hypothesis evidence. FR-008's independence claim is not executable (latent is by construction a function of text) and is replaced by an incremental-predictive-value criterion with descriptive collinearity reporting.

## Decision / Rationale

| Decision | Rationale | Compute |
|----------|-----------|---------|
| Use ONLY the verified parquet URL as input | It is the single verified, unattended-downloadable source; every other previously cited dataset failed verification | CPU |
| Replace ResNet-18 visual latents with deterministic structural feature vectors | The verified dataset has no images or bounding boxes; a visual encoder cannot run. A documented, deterministic text-structure extractor is an honest reproducible target — NOT a fake stand-in for a visual computation (no visual computation is claimed) | CPU |
| Downgrade SC-001 to a sanity check | Target is a deterministic function of the student's own input; MSE-vs-random-init can only be confirmed, never falsified — circular validation | CPU |
| Reframe FR-008 as incremental predictive value | The latent cannot contain information independent of the text representation by construction; independence is definitionally unsatisfiable | CPU |
| Compact student model (hashed n-gram features + small MLP, ≤50M params, in practice far smaller) | FR-002's 6 h CPU budget; no transformer fine-tuning needed, so no GPU escape hatch | CPU |
| Per-seed re-trained text-only downstream baseline (identical ridge head) | Removes initialization-variance confound (FR-009); pairing unit is the seed | CPU |
| Downstream task = predicting the dataset's overlap/CPU-score signal, gated by a leakage pre-check | It is the labeled signal the verified dataset actually contains; table-QA benchmarks are not obtainable. The pre-check guards against the label being a trivial function of the input text | CPU |
| Multi-seed paired tests with Bonferroni (α = 0.025) | One primary hypothesis + one ablation; stricter than and consistent with SC-003's 0.05 standard | CPU |

## Dataset Strategy

| Role | Dataset | Verified Source | Variables Used | Notes |
|------|---------|-----------------|----------------|-------|
| Corpus + downstream labels | MixSub-LLaMA-3.2 Text-Only Overlap CPU-Score | https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet | text fields; overlap/CPU-score label fields (exact column names discovered at download time and recorded in `data/raw/provenance.json`) | Downloaded via direct HTTPS (`curl`/`pandas.read_parquet`); SHA-256 recorded. **No verified source exists for page images or layout annotations** — the visual-encoder component of FR-001 is infeasible and is documented as a scope limitation, not substituted with fabricated data. |

## Modeling Approach
1. **Download** (`src/data/download.py`): fetch the parquet from the verified URL, verify SHA-256, assert row count ≥ [deferred] minimum (FR-007 graceful failure otherwise), record column inventory AND label semantics (which columns the label was computed from, per dataset card / provenance) to `provenance.json`.
2. **Preprocess** (`src/data/preprocess.py`): validate rows against `contracts/documentpair.schema.yaml` (text present, non-empty; label numeric); skip+log invalid rows; write `data/processed/document_pairs.parquet`.
3. **Structural targets + non-degeneracy gate** (`src/features/structure.py`): fixed deterministic feature vector per document (line counts, mean line length, heading/list-marker indicators, whitespace/punctuation structure ratios, etc.), dimension recorded in the schema. **Gate**: assert the feature matrix is non-degenerate (per-feature variance above a [deferred] floor; no more than a [deferred] fraction of near-constant features). If the text is stored as flattened single-line strings and line-structure features are degenerate, fall back to newline-free features (whitespace/punctuation/token-length distributions). If those are also degenerate, terminate with a clear scope-mismatch error (FR-007-style) rather than run a vacuous study.
4. **Splits** (`src/utils/split_generator.py`): deterministic 80/10/10 train/val/test.
5. **Student** (`src/models/distilled.py`): hashed character/word n-gram features → MLP → structural vector; MSE loss; Adam; early stop on val MSE; seeds pinned; memory (psutil) and wall-clock recorded (FR-002/FR-003, SC-004/SC-005/SC-007). The MSE-vs-frozen-random-head comparison is a **sanity check only** (SC-001, downgraded).
6. **Downstream baseline** (`src/models/baseline.py`): text embedding + ridge head, re-initialized and re-trained for every seed (FR-009). The frozen-random-head student is used only for the SC-001 sanity check, never downstream.
7. **Augmented representation** (FR-004, reframed): text embedding ⊕ predicted structural latent, identical ridge head.
8. **Label-semantics & leakage pre-check, then downstream** (`src/eval/downstream.py`): BEFORE interpreting any delta, (a) record the label's construction from `provenance.json`; (b) compute the correlation between the label and simple surface text-similarity features of the input text. If the label is a trivial/near-deterministic function of the input text (correlation above a [deferred] threshold), the downstream result is flagged uninterpretable and reported as a leakage finding — no augmented-vs-baseline gain is claimed. Otherwise: ridge/logistic head predicting the label from (a) text-only embedding, (b) augmented, (c) latent-only ablation; hyperparameters tuned on val, metrics reported on test only.
9. **Stats** (`src/eval/stats.py`): paired t-test across seeds (Shapiro–Wilk; Wilcoxon fallback), Bonferroni α = 0.025 (stricter than and consistent with SC-003's 0.05), power-limitation note, associational framing (FR-006).

## Evaluation Plan

| Metric | Comparison (arms, pairing unit = seed) | Test | Status |
|--------|-----------|------|--------|
| Val MSE vs frozen-random-head student | student vs frozen-head student | Paired t-test across seeds | **Sanity check only** (SC-001, downgraded — near-tautological, not hypothesis evidence) |
| Downstream score (accuracy/F1 or RMSE per label type) | augmented vs per-seed re-trained text-only baseline | Paired t-test, α = 0.025 (SC-002/SC-003) — gated by leakage pre-check | **Primary hypothesis** |
| Latent-only ablation | latent-only vs text-only baseline | Paired test | Incremental-value criterion (FR-008 reframed; independence NOT claimable) |
| Independence | MI, Pearson r (latent vs text embedding) | Descriptive only | Confounded by construction; no independent-effects claim; FR-008-as-written NOT EXECUTABLE |
| Label leakage | label vs surface text-similarity correlation | Pre-registered gate | If trivial/leaky, report finding; do not interpret delta |
| Structural target degeneracy | per-feature variance | Gate at Phase 1b | Fallback to newline-free features; else terminate |
| Peak RAM / runtime | vs 7 GB / 6 h | psutil + wall clock (SC-004/SC-005) | Feasibility |
| Valid row count | vs minimum | Count at preprocess (SC-006) | Data sufficiency |
| Val/train loss ratio | vs 2.0 | Overfitting check (SC-007) | Sanity |

## Statistical Rigor Checklist
- Multiple comparisons: Bonferroni, one primary hypothesis + one ablation, α = 0.025 each (stricter than and consistent with SC-003's 0.05).
- Power: seed count [deferred]; explicit power-limitation acknowledgement included in results.
- Causal framing: associational only (FR-006).
- Measurement validity: structural targets are defined by a documented deterministic extractor (construct is "text-recoverable structure", NOT visual layout — stated plainly). Downstream label semantics recorded and leakage-checked before interpretation.
- Collinearity: latent/text-embedding correlation reported descriptively; independence claim explicitly not supportable (FR-008 NOT EXECUTABLE as written).
- Circular validation avoided: the only hypothesis test (downstream incremental value) uses a target (the label) that is NOT the deterministic function the student learns.

## Reproducibility Measures
Pinned seeds; single canonical dataset URL; SHA-256 checksums; pure-function transforms; `requirements.txt` with exact versions; every result traceable to `artifacts/eval/results.json`.