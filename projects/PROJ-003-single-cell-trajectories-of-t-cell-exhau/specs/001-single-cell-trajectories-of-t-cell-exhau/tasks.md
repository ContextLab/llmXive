# Tasks: Single-Cell Trajectories of T-Cell Exhaustion

**Inputs**: The active `spec.md`, `plan.md`, `data-model.md`, and `contracts/` for the feature branch `001-single-cell-trajectories-t-cell-exhaustion`.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the project environment and execute a thin, end-to-end analysis on a single real dataset to validate the pipeline from raw SRA data to velocity graphs.

- [X] T001 Establish the project layout in `projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/`, including `code/`, `data/raw/`, `data/processed/`, `data/results/`, and `tests/`. Configure linting/formatting via `pyproject.toml` (ruff/black) and document the runnable environment in `quickstart.md`.
    - Verification: File tree exists; `ruff check .` and `black --check .` pass.
- [ ] T002 Implement `code/download_data.py` to fetch raw count matrices for GSE136103, GSE127465, GSE111075, and GSE138852 using SRA Toolkit (`prefetch` and `fastq-dump`). <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 -->
    - Requirements: No synthetic fallbacks; must fail loudly if SRA fetch fails. Record SHA256 checksums of all downloaded files in the project state YAML (Constitution Principle III).
    - Verification: `tests/unit/test_download.py` asserts that the state YAML contains valid checksums and that the datasets contain necessary variables (PD-1 expression, metabolic markers, exhaustion signatures, and therapy response labels) per SC-005.
    - Output: Raw files in `data/raw/` conforming to `contracts/dataset.schema.yaml`.
- [ ] T003 Implement the preprocessing pipeline consisting of `code/preprocess.R` (Seurat v4 QC: >20% mitochondrial read filter and normalization) and a Python wrapper `code/preprocess.py` that executes the R script via `subprocess`.
    - Output: Normalized `.h5ad` files in `data/processed/`.
    - Verification: `tests/unit/test_preprocess.py` asserts that cells with >20% mitochondrial reads are removed.
- [ ] T004 Implement `code/velocity.py` to execute the scVelo dynamical model on CPU with default precision for a single dataset (GSE136103).
    - Requirements: Complete within 45 minutes on CPU; no CUDA usage.
    - Output: `data/results/velocity_graph.h5ad` containing velocity vectors and pseudotime values.
    - Verification: Integration test in `tests/integration/test_trajectory_reconstruction.py` confirms the `.h5ad` file contains `velocity`, `pseudotime`, `spliced`, and `unspliced` layers.

**Checkpoint**: The pipeline executes end-to-end on one real dataset, producing a valid velocity graph under `data/results/`.

## Phase 2: Complete the study and validate its evidence

**Goal**: Expand the analysis to all datasets, identify regulatory fork-points using a statistically rigorous null model, and validate findings against therapy response labels.

- [ ] T005 Implement the Markov-chain pseudotime aligner in `code/aligner.py` to integrate trajectories across datasets.
    - Verification: Unit tests in `tests/unit/test_aligner.py` confirm alignment convergence on a toy trajectory.
- [ ] T005_run Run the full trajectory reconstruction and pseudotime alignment for all four datasets using the aligner.
    - Requirements: Handle edge cases (skip datasets <1000 cells with a warning; retry convergence with higher regularization).
    - Output: `data/processed/unified_trajectory.h5ad`.
- [ ] T006 Implement `code/forkpoint.py` to identify branch points using a rotation-based null model (rotating velocity vectors in reduced dimension space while preserving splicing kinetics).
    - Requirements: Branch points must exceed 2.0 SD above the null mean; extract genes with differential timing > 0.1 pseudotime units. (Note: Plan corrected this from spec's permutation shuffle; flagged for spec alignment).
    - Output: `data/results/fork_points.csv` conforming to `contracts/fork_point.schema.yaml`.
- [ ] T007 Implement `code/validate.py` to perform cross-dataset validation using a Discovery/Validation split (Discovery: GSE136103, GSE127465, GSE111075; Validation: GSE138852).
    - Requirements: Use patient-level block bootstrapping to compute enrichment p-values of fork-point genes against responder vs. non-responder labels in GSE138852.
    - Verification: `tests/unit/test_validate.py` asserts that the Spearman rank correlation for the top 3 fork-point genes is $\ge 0.80$ (US-3 Scenario 2).
    - Output: `data/results/validation_results.json` conforming to `contracts/validation.schema.yaml`.
- [ ] T008 Implement `code/report.py` to generate the final validation report and a heatmap of top fork-point genes across datasets with bootstrap confidence intervals.
    - Requirements: The report MUST explicitly label all findings as associational and include a dedicated disclaimer section (SC-004).
    - Verification: A regex check in `tests/unit/test_report.py` confirms the presence of "associational"; run Reference-Validator Agent on all report citations (Constitution Principle II).

**Checkpoint**: All research requirements (FR-001 through FR-008) are implemented, and results are generated from real data.

## Phase 3: Reproducible results and paper handoff

**Goal**: Ensure the entire workflow is reproducible from raw inputs and prepare the scientific artifacts for handoff.

- [ ] T009 Execute a full end-to-end re-run of the documented workflow from the raw SRA accessions, confirming that all tests pass and result artifacts are stable.
    - Verification: Checksums of final `fork_points.csv` and `validation_results.json` are recorded.
- [ ] T010 Write a concise methods and results account in `results/summary.md` linked to the output cells and figures, honestly describing any datasets that were skipped or branches flagged as 'low_confidence'.
    - Verification: Run Reference-Validator Agent on all summary citations and claims (Constitution Principle II).
    - Handoff: Document the final state of `data/results/` for the paper-stage pipeline.

## Dependencies and requirement coverage

| Requirement | Task | Verification Command |
|-------------|------|----------------------|
| FR-001 (Download) | T002 | `python code/download_data.py` |
| FR-002 (Preprocessing) | T003 | `pytest tests/unit/test_preprocess.py` |
| FR-003 (scVelo CPU) | T004 | `python code/velocity.py` |
| FR-004 (Fork-Points) | T006 | `python code/forkpoint.py` |
| FR-005 (Ranking) | T006 | Check `data/results/fork_points.csv` |
| FR-006 (Bootstrapping) | T007 | `python code/validate.py` |
| FR-007 (Heatmap/Report) | T008 | `python code/report.py` |
| FR-008 (Therapy Validation) | T007 | Check `data/results/validation_results.json` |
| SC-001 (CPU-only) | T004 | Check runtime logs for no CUDA/GPU usage |
| SC-004 (Associational) | T008 | `pytest tests/unit/test_report.py` |
| SC-005 (Sufficiency) | T002 | `pytest tests/unit/test_download.py` |
| Constitution III (Hygiene) | T002 | Check state YAML for raw data checksums |
| Constitution II (Accuracy) | T008, T010 | Run Reference-Validator Agent |