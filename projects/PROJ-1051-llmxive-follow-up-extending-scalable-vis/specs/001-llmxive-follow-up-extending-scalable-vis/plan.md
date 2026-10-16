# Implementation Plan: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence" (Re-plan v3)

**Branch**: `001-llmxive-layout-distillation` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-llmxive-layout-distillation/spec.md`; re-plan v2 triggered by failed T001/T002 (unobtainable datasets); v3 addresses methodology panel concerns (circular validation, FR-008 unsatisfiability, label leakage, degenerate targets).

## Scope Revision (BLOCKING ISSUE, surfaced per plan rules)

The original plan relied on three datasets that **cannot be obtained** on the CI runner:

1. `datasets.load_dataset("llmXive/layout-distillation")` — no such public dataset exists (T001 failure, exit=1).
2. `pubmed-layout` fallback — no verified public programmatic source.
3. `docvqa` via `datasets.load_dataset("docvqa")` — not in the verified-datasets block; the hub id alone is not a verified, license-clear, unattended-downloadable source for this project.

The **only verified, directly-downloadable dataset** available is:

- ` (CPU-score text-overlap parquet).

That dataset contains **text and overlap/score fields — it does NOT contain page images or bounding-box layout annotations**. Therefore the spec's core mechanism (frozen visual encoder producing ground-truth visual latents from page images, FR-001) **cannot be executed with obtainable data**. Per the dataset-variable-fit rule, this plan does NOT pretend otherwise and does NOT fabricate images or synthetic latents.

### Restated research question (v3)

The original question ("do visual layout latents transfer into text-only representations?") is **not answerable with obtainable data**. The restated, testable question is:

> **Do cheap structural summary features of text, distilled into a compact model, add predictive value beyond dense text features for the dataset's overlap/CPU-score label?**

This is deliberately weaker than the spec's claim and is framed as such everywhere. The study does NOT claim to test "text implicitly encodes structure" in the spec's sense — the structure is explicitly computable from text by a documented extractor.

### Hypothesis structure (v3 — fixes circular-validation concern)

- **PRIMARY (and only) hypothesis**: the augmented representation (text embedding ⊕ predicted structural latent) improves the downstream metric over the capacity-matched, per-seed re-trained text-only baseline, tested with a paired t-test across seeds at Bonferroni-corrected α = 0.025. This hypothesis is falsifiable.
- **SC-001 (distillation MSE vs random init) is DOWNGRADED to a sanity/feasibility check.** Because the structural target is a deterministic function of the same text the student sees, MSE convergence is near-tautological: it can confirm the model trains within budget but is NOT evidence for any scientific claim. It is reported as a sanity check, never as hypothesis evidence.
- **FR-008 (independence of predicted latents from the text encoder) is NOT EXECUTABLE**: the latent is by construction a function of the text, so it cannot contain information independent of the text representation. The reframed criterion is **incremental predictive value** of the latent over the baseline text embedding, with MI/Pearson collinearity reported descriptively as confounded-by-construction. The independence conclusion of the original FR-008 is explicitly recorded as not supportable in this design.

### Required spec amendments (spec-root causes — flagged for kickback)

The following spec texts mandate the unexecutable mechanism and MUST be amended at the clarification pass before this plan can claim full coverage. This plan records them rather than silently substituting:

| Spec element | Required amendment |
|---|---|
| FR-001 | Reframe to: "generate deterministic structural feature targets from the verified text corpus" (visual-encoder component dropped — no obtainable image+layout dataset) |
| FR-004 | Replace "predicted visual latents" with "predicted structural latents" |
| FR-005 / US-3 / ReasoningTask entity | Redefine downstream task from table-QA to overlap-label prediction on the verified dataset (no reasoning-task dataset is obtainable) |
| US-1 Acceptance Scenario 2 | Remove the cosine/KL visual-latent divergence test (presumes a visual latent); replace with the structural-target non-degeneracy check (Phase 1b) |
| Assumptions (dataset fallback chain) | Replace `llmXive-layout-distillation` / `layout-parser` / `pubmed-layout` chain with the single verified parquet URL; align FR-007/SC-006 "primary + fallback" wording to single-source |
| Key Entities | Update VisualLatent → StructuralLatent; DistilledModel "50M-parameter Transformer" → compact hashed-feature student (≤50M, in practice far smaller) |
| Constitution Principle VII | Add a scope-limitation clause: the visual-latent mechanism is infeasible with obtainable data; the project's contribution is the reframed incremental-value question |

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `pyarrow`, `numpy`, `scipy`, `scikit-learn`, `torch==2.3.0` (CPU wheel), `jsonschema`, `psutil`, `pytest`
- **Storage**: filesystem `data/` (raw, processed), `artifacts/` (models, eval)
- **Testing**: pytest (unit, contract, integration)
- **Target Platform**: GitHub Actions free-tier runner — 2 CPU cores, ≤7 GB RAM, ≤6 h, CPU-only
- **Constraints**: deterministic seeds; every artifact checksummed; no fabricated data
- **Scale/Scope**: one parquet input (~single file), one primary analysis, one ablation/sensitivity check

## Constitution Check

| Principle | Check |
|-----------|-------|
| I. Reproducibility | Single verified parquet URL downloaded identically every run; seeds pinned in `src/utils/seed.py`; deterministic structural-feature extractor (pure functions). |
| II. Verified Accuracy | Only the verified dataset URL is cited; no invented dataset URLs; scope mismatch stated explicitly rather than papered over. |
| III. Data Hygiene | SHA-256 of the downloaded parquet recorded under `data/`; all transforms write new files with provenance columns. |
| IV. Single Source of Truth | Every reported statistic traces to `artifacts/eval/results.json`, produced by exactly one code block. |
| V. Versioning Discipline | Content hashes of all artifacts recorded in the project state YAML. |
| VI. Resource-Constrained Efficiency | Full pipeline CPU-only, ≤7 GB RAM, ≤6 h; no GPU escape hatch needed (no transformer fine-tuning beyond small CPU models). |
| VII. Latent Space Fidelity | **Scope limitation**: the visual-latent mechanism is infeasible with obtainable data (see Required spec amendments). The reframed contribution — statistically significant incremental predictive value of distilled structural features over a text-only baseline, verified via paired t-tests across seeds — is tested at Bonferroni α = 0.025, associational framing enforced. Constitution amendment flagged for kickback. |

## Project Structure

```text
specs/001-llmxive-layout-distillation/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/
│   ├── documentpair.schema.yaml
│   └── results.schema.yaml
└── tasks.md   (later stage)

src/
├── data/
│   ├── download.py          # curl the verified parquet, sha256, row-count check, column inventory
│   └── preprocess.py        # schema-validate rows, build DocumentPair parquet
├── features/
│   └── structure.py         # deterministic structural-feature extractor + non-degeneracy gate
├── models/
│   ├── distilled.py         # text -> structural-latent student (MSE, sanity check)
│   └── baseline.py          # text-only downstream baseline (re-trained per seed)
├── eval/
│   ├── downstream.py        # label-semantics/leakage pre-check; augmented vs baseline
│   └── stats.py             # paired t-test / Wilcoxon, Bonferroni, power note
└── utils/
    ├── seed.py
    └── split_generator.py
```

## Phase Mapping (all FRs / SCs covered or explicitly marked)

| Phase | FR(s) | SC(s) | Notes |
|-------|-------|-------|-------|
| 0 – Download & validate verified parquet | FR-007 (single-source wording pending spec amendment) | SC-006 | Graceful failure if row count < minimum; column inventory + label semantics recorded to `provenance.json`. |
| 1 – Structural target generation | FR-001* (reframed; visual-encoder part NOT EXECUTABLE, flagged for spec kickback) | — | Deterministic feature vectors replace visual latents. |
| 1b – Non-degeneracy gate | FR-007 (analog) | — | Variance / near-constant assertions on the structural feature matrix. Fallback: newline-free features (whitespace/punctuation/token-length distributions). If still degenerate, terminate with clear scope-mismatch error rather than run a vacuous study. |
| 2 – Distillation training (multi-seed) — SANITY CHECK | FR-002, FR-003 | SC-001 (downgraded to sanity check), SC-004, SC-005, SC-007 | MSE vs frozen-random-head student, paired per seed; explicitly NOT hypothesis evidence (near-tautological). Memory/runtime tracked via psutil + wall clock. |
| 3 – Downstream baseline (multi-seed) | FR-009 | — | Text embedding + ridge head, re-initialized and re-trained for every seed; pairing unit for SC-002/SC-003 is the seed. |
| 4 – Augmented representation | FR-004* (reframed; "visual latents" wording pending spec kickback) | — | Concatenate text embedding + predicted structural latent. |
| 5 – Label-semantics & leakage pre-check, then downstream evaluation | FR-005* (reframed task), FR-006 | SC-002, SC-003 | Pre-registered leakage check gates interpretation: if the label is a trivial function of input text, report that finding and do NOT claim an interpretable augmented-vs-baseline gain. Otherwise: val-tuned, test-reported metrics, paired t-test, associational framing; null results reported with delta + p. |
| 6 – Incremental-value ablation & reporting | FR-008 (NOT EXECUTABLE as independence; reframed to incremental predictive value) | — | Latent-only arm; MI/Pearson reported descriptively as confounded-by-construction; results.json + summary tables state the independence claim is not supportable. |

**Comparison arms and pairing unit (unambiguous, per concern 6d20841e)**:
- SC-001 sanity check: student vs *frozen-random-head student* (identical architecture, same seed) — used ONLY for the sanity check, never downstream.
- SC-002/SC-003 downstream: per seed, *augmented* (text embedding ⊕ predicted latent, ridge head) vs *text-only baseline* (text embedding, identical ridge head, re-initialized and re-trained per seed per FR-009). Paired t-test pairs the two arms within each seed.

**Statistical rigor**: ONE primary hypothesis (downstream gain) plus the FR-008-reframed incremental-value ablation → Bonferroni α = 0.025 each. This corrected threshold is **stricter than and consistent with** SC-003's p < 0.05 standard: any result passing α = 0.025 also passes SC-003. Paired t-test across seeds (normality checked via Shapiro–Wilk, Wilcoxon fallback); power limitation acknowledged explicitly (seed count and effect size deferred, with a stated power note rather than an invented justification); all claims associational (FR-006); collinearity between predicted latent and text embedding reported descriptively, never claimed as independent effects.

**Compute feasibility**: all steps are classical ML / small torch CPU models over a single parquet — comfortably within 2 cores / 7 GB / 6 h. No GPU escape hatch required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| FR-001 visual-encoder component dropped | No verified dataset contains page images + layout annotations; fabricating them violates the fabrication gate | Synthesizing images/latents would be fabrication, rejected at execution gate |
| FR-008 independence ablation reframed | Latent is by construction a function of text; independence is definitionally unsatisfiable | Reporting MI/Pearson as an independence test would be a false claim; incremental-value criterion is the honest substitute |
| SC-001 downgraded to sanity check | Target is a deterministic function of the student's input; MSE convergence is near-tautological | Presenting it as hypothesis evidence would be circular validation |