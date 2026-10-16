# Implementation Plan: Structure-Only Surrogate Model for 2D Material Elastic Moduli

**Branch**: `PROJ-169-surrogate-elastic-moduli` | **Date**: 2026-07-08 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This project implements a **Structure-Only Surrogate Model** (lightweight GNN) to predict Young's, Shear, and Poisson's ratios for 2D materials. The model is a fast interpolator of pre-computed DFT data — it does NOT solve the Schrödinger equation or perform first-principles calculations. The pipeline ingests DFT elastic-tensor data from the verified parquet sources listed in `research.md`, constructs PBC-aware graph representations, trains a CPU-only GNN within a 7GB memory budget, and validates inter-family generalization against a composition-only baseline.

This is a **re-plan** addressing five verifier-rejected tasks (T060c, T013f, T017b, T046, T018b) and replacing the unverified `matbench/elasticity` dataset with the verified parquet URLs. Working artifacts (repository scaffolding, loader, graph builder, splitter skeleton, training/eval scripts) are preserved and repaired rather than regenerated.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `torch==2.3.*` (CPU wheels), `torch-geometric==2.5.*`, `pandas`, `pyarrow`, `scikit-learn`, `pymatgen`, `shap`, `huggingface_hub` (pinned in `code/requirements.txt`)
**Storage**: `data/raw/` (downloaded parquet, checksummed), `data/processed/` (Parquet/JSON/PT), `data/results/` (JSON/MD)
**Testing**: `pytest` (unit + contract tests against `contracts/*.schema.yaml`)
**Target Platform**: Linux, GitHub Actions free tier (2 CPU, 7GB RAM, 14GB disk, ≤6h, no GPU)
**Project Type**: Data science / ML pipeline (CPU-first; no GPU escape hatch needed)
**Performance Goals**: inference < 100ms per material (SC-003); peak memory ≤ 7GB (SC-004, FR-003)
**Constraints**: CPU-only; single canonical source per run; no synthetic data; surrogate terminology enforced (FR-006)
**Scale/Scope**: all valid 2D entries with complete elastic tensors from the verified source (SC-001: >1,000 or all available if fewer)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **I. Reproducibility**: seeds pinned in `code/utils/seeds.py`; dataset fetched from the same verified canonical parquet URL each run; SHA-256 checksums recorded under `data/`.
2. **II. Verified Accuracy**: research.md cites ONLY the three verified URLs; no invented dataset links.
3. **III. Data Hygiene**: raw parquet preserved unchanged; every derivation writes a new file (`graphs_v1.parquet`, `split_indices.json`, etc.); checksums recorded.
4. **IV. Single Source of Truth**: every metric in reports traces to one `data/results/*.json` row produced by one `code/` block; no hand-typed numbers.
5. **V. Versioning Discipline**: artifact content hashes recorded in the project state file; `updated_at` refreshed on change.
6. **VI. Numerical Stability / DFT Fidelity**: only entries with 6 independent tensor components retained; Young's/shear/Poisson derived exclusively from the elastic tensor via continuum-mechanics relations in `code/physics/tensors.py` — never hard-coded. Accuracy evaluated on held-out families.
7. **VII. Structural Descriptor Attribution**: importance claims substantiated by permutation importance AND SHAP magnitudes on the final GNN (SC-005, FR-005).

**Title inconsistency (flagged, not silently fixed in plan)**: the constitution title still contains "First-Principles Calculations", which the spec forbids for this surrogate model. Per the spec's FR-006, the pipeline produces `constitution_title_audit.json` and **exits 1** if the forbidden term appears in the title used for reporting. The title amendment itself follows the constitution's amendment procedure (open PR, version bump) — T060b/T060c implement the audit and the amendment.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-169-surrogate-elastic-moduli/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/
├── code/
│   ├── requirements.txt
│   ├── main_pipeline.py             # end-to-end orchestrator with hard gates
│   ├── utils/
│   │   ├── seeds.py
│   │   ├── disclaimer_template.py   # T046: DISCLAIMER_TEXT + FEYNMAN_QUOTE (was missing)
│   │   └── verify_constitution_title.py  # T060c: exit 1 on FAIL + writes audit JSON
│   ├── physics/
│   │   └── tensors.py               # tensor -> moduli (Principle VI)
│   ├── data/
│   │   ├── loader.py                # verified parquet download + checksum
│   │   ├── graph_builder.py         # PBC-aware graphs
│   │   ├── split_generator.py       # T013f: full implementation (was truncated)
│   │   └── splitter.py              # T017b: validation -> split_validation.json
│   ├── model/
│   │   ├── gnn.py
│   │   ├── train.py                 # T018b: CPU-only, tracemalloc, saves model_v1.pt
│   │   ├── train_logger.py
│   │   ├── eval_runner.py           # baseline comparison + predictions.json
│   │   └── inference_benchmark.py
│   └── analysis/
│       └── feature_importance.py    # permutation + SHAP
├── data/
│   ├── raw/                         # checksummed parquet
│   ├── processed/                   # graphs_v1.parquet, split_indices.json, model_v1.pt
│   └── results/                     # all JSON/MD deliverables
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── docs/
    └── methodology.md               # DFT vs Surrogate distinction
```

**Structure Decision**: single project layout; strict phase ordering Data → Split → Train → Eval → Analysis → Audit.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Hard gate on constitution title (T060c) | Prevents "First-Principles" mislabeling of a surrogate model (spec §4, FR-006). | Removing the gate propagates a scientific-integrity error. |
| Inter-family stratified split (T013f/T017b) | Required by SC-002/FR-002; random split allows family memorization. | Random split fails the generalization criterion. |
| CPU-only + tracemalloc enforcement | FR-003 / SC-004 hard 7GB limit on free-tier runner. | No GPU is available; unenforced memory risks OOM kills. |
| Both permutation AND SHAP importance | SC-005 and FR-005 require both; SHAP handles collinear descriptors, permutation gives ablation deltas. | Either alone fails SC-005. |

## Tasks

### Phase 0: Setup & Constitution
- [X] T001a: Initialize repository structure.
- [X] T001b: Create initial state yaml.
- [ ] T060b: Amend constitution title via amendment procedure (remove "First-Principles Calculations"; version bump to 1.1.0).
- [ ] **T060c (REDO)**: `verify_constitution_title.py` MUST (a) scan the constitution title for forbidden terms ("First-Principles", "Schrödinger Equation"), (b) write `data/results/constitution_title_audit.json` conforming to `contracts/constitution_audit_schema.schema.yaml`, and (c) call `sys.exit(1)` on FAIL and `sys.exit(0)` on PASS. Add a unit test proving both exit codes and the JSON file's existence. **HARD GATE** for all downstream tasks.

### Phase 1: Data Pipeline (US1 — FR-001, SC-001)
- [ ] T013d1: Download the verified canonical parquet (URL pinned in `code/data/loader.py` from research.md's verified list); validate schema (`structure`/CIF + `elastic_tensor`); SHA-256 checksum to `data/raw/`.
- [ ] T013d0_validation: Verify valid-entry count; log if < 1,000 (SC-001 accepts all available if fewer).
- [ ] T013d2: Parse structures with pymatgen `CifParser`/`Structure.from_dict`; filter to 2D entries and complete 6-component tensors (Principle VI).
- [ ] T013d3: Build PBC-aware graphs (adaptive covalent cutoff).
- [ ] T013d4: Save `data/processed/graphs_v1.parquet` (contract-validated).
- [ ] **T013f (REDO)**: Complete `split_generator.py` — load structures (pickle/parquet → pymatgen Structure), cluster by chemical family (space group + stoichiometry class, with `StructureMatcher` grouping where applicable), `train_test_split` families with pinned seed, **atomically write** `data/processed/split_indices.json` (write temp file + `os.replace`). Unit test: no family appears in both train and test.
- [ ] **T017b (REDO)**: `splitter.py` validates the split (family disjointness, size distribution, leakage check) and **writes `data/results/split_validation.json`** with per-split counts, family lists, and PASS/FAIL status. Contract test validates the file.

### Phase 2: Model Training (US2 — FR-003, FR-004, SC-002, SC-004)
- [ ] T016/T018c: Define weighted/normalized-MSE loss and lightweight GNN (2–3 layers, hidden ≤ 64).
- [ ] **T018b (REDO)**: `train.py` MUST (a) force CPU (`torch.device("cpu")` + assert no CUDA usage), (b) wrap training in `tracemalloc` and record `peak_memory_gb` in `training_logs.json` with `memory_limit_exceeded` flag, (c) **save `data/processed/model_v1.pt`** (state dict + seed + disclaimer), (d) run `eval_runner.py` to produce **`data/results/predictions.json`** on the test set. Hard gate: exit 1 if peak memory > 7GB.
- [ ] T022: Inference benchmark → `inference_benchmark.json`; hard gate exit 1 if > 100ms/material.
- [ ] **T046 (REDO)**: Create the missing `code/utils/disclaimer_template.py` defining `DISCLAIMER_TEXT` (scientific-integrity statement: surrogate interpolator, not first-principles; DFT ground truth; interpolation-only validity) and `FEYNMAN_QUOTE`. Unit test asserts both constants are non-empty strings and that `train_logger.py`/`eval_runner.py` import them successfully.

### Phase 3: Evaluation & Analysis (US3 — FR-004, FR-005, SC-002, SC-005)
- [ ] Tb: Inter-family evaluation: GNN vs composition-only baseline (linear regression on Magpie-style composition features); report relative MAPE reduction and 95% CI for MAPE → `generalization_metrics.json`. SC-002 gate: ≥10% relative MAPE reduction vs baseline.
- [ ] T003: Feature importance via permutation importance AND SHAP magnitudes; unified ranked list with ablation deltas → `feature_importance_report.md`. SC-005 gate: ≥3 significant descriptors.

### Phase 4: Finalization
- [ ] T008a: Integration test (end-to-end on a real small subset).
- [ ] T001c: Compute and record artifact hashes; update state `updated_at`.
- [ ] T057: Final title audit re-run; `docs/methodology.md` (DFT vs Surrogate distinction).

## Reproducibility Notes
- Dataset fetched by pinned verified URL each run; checksum verified before use.
- All seeds pinned via `code/utils/seeds.py`.
- Memory managed by batch processing (batch 16–32) and streaming row iteration during ingestion.
- All claims framed as surrogate accuracy relative to DFT ground truth; associational only.
