# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-06-27 | **Spec**: `specs/feature/motif-rsfc/spec.md`
**Input**: Feature specification from `/specs/feature/motif-rsfc/spec.md`

## Summary

This project investigates whether specific 3-node network motif configurations in structural brain connectomes constrain individual variation in resting-state functional connectivity (rsFC). The technical approach involves: () downloading HCP diffusion and rs-fMRI data for a representative subset of subjects; (2) constructing binary structural connectomes using the Schaefer parcellation with density-based thresholding; (3) enumerating k-node motifs (undirected) and computing z-scores against degree-preserving null models; (4) calculating rsFC strength (mean absolute correlation) and global efficiency; (5) performing partial correlations (controlling for global degree via residualization) with Bonferroni correction and a secondary FDR check; (6) running permutation tests for significant motifs; and (7) generating a comprehensive PDF report including a mandatory disclaimer and power analysis section. All analysis is CPU-first, designed to run within GitHub Actions free-tier constraints (limited CPU, constrained RAM, 6h limit).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `networkx`, `matplotlib`, `seaborn`, `nibabel`, `h5py`, `requests`, `jinja2`, `weasyprint` (or `matplotlib` PDF backend), `awscli` (for HCP S3), `statsmodels`
**Storage**: Local file system (GitHub Actions runner ephemeral storage: limited disk space)
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for motif counting logic, integration tests for pipeline phases)
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)
**Project Type**: scientific-research-pipeline
**Performance Goals**: Motif enumeration ≤300s/subject (3-node only); full pipeline ≤6h; PDF generation ≤2min.
**Constraints**: No GPU required (CPU-only); no external API keys beyond HCP public access; memory <7GB (streaming/lazy loading where possible); strict reproducibility (seed=42).
**Scale/Scope**: 50 subjects, 100-node graphs, 13 possible 3-node motifs (undirected: several types), A sufficient number of permutation iterations.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (NON-NEGOTIABLE)**:
    *   **Plan Compliance**: The plan mandates fixed random seeds (`seed=42`) for null model generation and permutation tests. All external data is fetched from the canonical HCP S3 source via programmatic download (`awscli` anonymous). The `requirements.txt` will pin exact versions.
    *   **Verification**: The `quickstart.md` includes a command to re-run the full pipeline on a fresh environment to verify output hashes.

2.  **Verified Accuracy**:
    *   **Plan Compliance**: Citations in `research.md` (e.g., Schaefer atlas, HCP data release) will be cross-referenced with the "Verified datasets" block in the input context. The plan explicitly avoids inventing dataset URLs.
    *   **Verification**: The `Reference-Validator` agent will be invoked during the task execution phase to validate all citations before the `research_review` stage.

3.  **Data Hygiene**:
    *   **Plan Compliance**: Raw HCP data is processed in a temporary directory. Derived binary connectomes (`data/processed/canonical_binary_adj.npy`) are saved with provenance metadata (checksum of source file). No in-place modifications.
    *   **Verification**: The `setup-plan.sh` script will generate a `checksums.json` manifest for all *derived* data artifacts. (Note: Raw data cannot be retained in CI due to size constraints, but derived data is checksummed).

4.  **Single Source of Truth**:
    *   **Plan Compliance**: All statistical outputs (correlation coefficients, p-values) are written to `data/processed/` JSON/CSV files. The PDF report is generated *programmatically* from these files, ensuring no manual transcription.
    *   **Verification**: The `report.py` script will include a footer with the hash of the input `subject_metrics.csv` to prove traceability.

5.  **Versioning Discipline**:
    *   **Plan Compliance**: Every artifact (scripts, data files) will be associated with a content hash in the project state file.
    *   **Verification**: The `Advancement-Evaluator` will check artifact hashes before stage transitions.

6.  **Structural Data Integrity**:
    *   **Plan Compliance**: The pipeline downloads unaltered HCP diffusion data to a temporary location. Parcellation to Schaefer-100 is performed as a distinct step, saving the result as a new file (`canonical_binary_adj.npy`) with a reference to the raw source ID. Raw data is deleted after processing to fit CI limits, but the *derived* structural matrix (the basis of analysis) is stored and checksummed, satisfying the integrity requirement for the analyzed data.
    *   **Verification**: The `data-model.md` defines the schema for the derived connectome, linking it to the raw source ID.

7.  **Statistical Transparency**:
    *   **Plan Compliance**: The `stats.py` module will log exact parameters (Bonferroni alpha, permutation count, seed, VIF threshold) to `pipeline.log`. The PDF report includes a "Methods" section with these exact values.
    *   **Verification**: The `results.pdf` will contain a machine-readable metadata block with the statistical parameters used.

## Project Structure

### Documentation (this feature)

```text
specs/feature/motif-rsfc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── motif_profile.schema.yaml
│   ├── results.schema.yaml
│   ├── analysis_results.schema.yaml
│   └── structural_connectome.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── pipeline.py          # Main orchestration script
├── preprocess.py        # Data download, parcellation, rsFC calculation
├── motifs.py            # Motif enumeration, null model generation, z-score calc
├── stats.py             # Correlations, VIF check, Bonferroni, Permutation tests
├── report.py            # PDF generation (matplotlib + text)
└── utils.py             # Logging, I/O helpers

data/
├── raw/                 # HCP downloaded files (nifti/h5) - TEMPORARY
├── processed/           # Derived .npy, .json, .csv artifacts
└── logs/                # pipeline.log

tests/
├── contract/            # YAML schema validation tests
├── integration/         # End-to-end pipeline tests (small subset)
└── unit/                # Motif counting, correlation logic tests
```

**Structure Decision**: A single `code/` directory with modular scripts is chosen over a web-service or mobile structure because this is a batch-processing scientific pipeline. This minimizes overhead and aligns with the CPU-first, script-based execution model of GitHub Actions. The separation of `preprocess`, `motifs`, and `stats` ensures clear data flow and easier unit testing for specific mathematical components.

## Compute Feasibility & Data Strategy

### Compute Strategy
*   **CPU-First**: All operations (motif counting on 100-node graphs, correlation, permutation) are computationally feasible on CPU cores.
    *   *Motif Counting*: 3-node motifs on a 100-node graph (max a large number of triplets) are trivial for `networkx` or custom C-optimized Python loops. The 300s timeout is a safe upper bound; expected time is <10s/subject.
    *   *Permutation*: A sufficient number of permutations of 50 data points is negligible (<1s).
*   **Memory**: Adequate RAM capacity is sufficient.. We process subjects sequentially (or in small batches of varying sizes) to keep memory footprint low. We do not load all raw NIfTI files simultaneously.
*   **Disk**: GB is sufficient. **Critical Adjustment**: HCP raw data is large (multi-GB per subject). We cannot store 50 full HCP raw datasets.
    *   *Solution*: The pipeline will **stream** raw data: download a subject's files, process them immediately to extract the -node matrix, save the derived `.npy` matrix to `data/processed/`, and **delete the raw files** for that subject before moving to the next. Only the derived `.npy` matrices (100x100 floats = 80KB each) and metadata will be retained in `data/processed/`. This keeps disk usage well within acceptable limits.
    *   *Constitution Alignment*: While raw data cannot be retained in CI due to size, the *derived* structural matrices (the actual data used for analysis) are stored unchanged in `data/processed/` and checksummed, satisfying Structural Data Integrity for the analyzed data.

### Data Availability
*   **Source**: Human Connectome Project (HCP) Large-Sample Release.
*   **Access Method**: **HCP S1200 via AWS S3 public bucket (us-east-1) using `awscli` with anonymous public read access**.
    *   *Fallback*: If the specific HCP S3 bucket is inaccessible or the download fails for a subject, the pipeline will skip the subject, log the error, and continue. If >5% of subjects fail, the pipeline will abort and suggest using the verified OpenNeuro dataset `ds000222` (HCP minimal processing pipeline data) as a smaller, verified alternative.
    *   *Constraint Check*: The spec assumes a cohort of subjects. If the CI cannot hold 50 raw datasets, we will process them one-by-one (download -> process -> delete raw) to stay within disk limits.

## Phase Breakdown

### Phase 0: Research & Data Verification
*   **Goal**: Confirm dataset variables and access method.
*   **Tasks**:
    *   Verify HCP S1200 diffusion and rsfMRI availability for 50 subjects.
    *   Verify Schaefer-100 parcellation compatibility.
    *   Finalize `research.md` with dataset URLs and access strategy.

### Phase 1: Data Model & Contracts
*   **Goal**: Define schemas for all I/O.
*   **Tasks**:
    *   Define `dataset.schema.yaml` (raw input metadata).
    *   Define `motif_profile.schema.yaml` (z-scores).
    *   Define `results.schema.yaml` (correlations, p-values).
    *   Define `analysis_results.schema.yaml` (statistical outputs).
    *   Define `structural_connectome.schema.yaml` (subject processing status).
    *   Generate `data-model.md`.

### Phase 2: Implementation (Code Generation)
*   **Goal**: Generate `code/` scripts.
*   **Tasks**:
    *   **T014c (Data Download & Parcellation)**: Download diffusion data, apply Schaefer-100, binarize using **median graph density threshold**, and save `data/processed/canonical_binary_adj.npy`. Log status to `data/processed/structural_connectome_metadata.json` (schema: `structural_connectome.schema.yaml`). **Logic for SC-001**: Parse this JSON, count 'complete' vs 'skipped' statuses, calculate success rate, and write to `results.json` and `pipeline.log`.
    *   **T015 (Functional Processing)**: Compute Pearson correlation of rs-fMRI time-series for 100 nodes, calculate global efficiency, and write `data/processed/rsfc.npy` and `data/processed/global_efficiency.json`.
    *   **T017 (Logging)**: Ensure `data/logs/pipeline.log` is created and updated with all processing steps, warnings, and errors.
    *   **T025c_loop (Threshold Sensitivity)**: Iterate over `z` thresholds {1.5, 2.0, 2.5}. For each, save output to `data/processed/sensitivity_z<value>.json`.
    *   **T026 (Motif Aggregation)**: Enumerate 3-node motifs, generate null models, compute z-scores, aggregate median z-scores, and write `data/processed/motif_profiles.json`.
    *   **T030a (VIF Check & Selection)**: Compute VIF for degree control. If VIF > 5, switch to permutation-only analysis. Write `data/processed/quality_flags.json` with the method selected and VIF values.
    *   **T032a (Correlation)**: Compute partial correlations (residualization method) between motif z-scores and rsFC metrics, applying Bonferroni and FDR corrections.
    *   **T032c (Permutation)**: Iterate over significant motifs, run a sufficient number of permutations, and write `results/permutation_results.json`.
    *   **T035a (Power Analysis)**: Compute min detectable r (N=50, alpha adjusted, power=0.80). **Output**: Write a JSON object with `min_detectable_r`, `power`, and `adjusted_alpha` to `data/processed/power_analysis.json`, which will be embedded in the PDF.
    *   **T035b (Report Generation)**: Generate `results.pdf`. **Mandatory**: Include the exact string "These findings are associational only and do not imply causation." in the report. Include the power analysis section with the specific values from T035a.
    *   **T039 (Metrics Aggregation)**: Read inputs, compute `network_density`, join data, and write `data/processed/subject_metrics.csv`.

### Phase 3: Execution & Validation
*   **Goal**: Run pipeline, validate outputs.
*   **Tasks**:
    *   Run on GitHub Actions.
    *   Validate `results.pdf` against `results.schema.yaml`.
    *   Verify `pipeline.log` and `checksums.json`.

## Risk Mitigation

*   **Risk**: HCP data download fails or is too large for CI.
    *   *Mitigation*: Process subjects sequentially; delete raw files immediately after parcellation. If download fails, log error and skip subject (US-1). **Success Rate Logic**: Skipped subjects are counted in the denominator for SC-001 (e.g., 45 complete / 50 total = 90%).
*   **Risk**: Motif counting is too slow.
    *   *Mitigation*: Limit to 3-node motifs (as per spec). Use optimized `networkx` or `igraph` (if available) or a custom C-extension if necessary (unlikely needed for N=100).
*   **Risk**: Zero variance in motif scores.
    *   *Mitigation*: `stats.py` includes a check for zero variance (std dev < 1e-6); skips correlation and logs "insufficient variance" (Edge Case).
*   **Risk**: Bonferroni correction is too strict (no significant results).
    *   *Mitigation*: The plan includes the power analysis (FR-010) to report the detectable effect size, ensuring the report is scientifically valid even if no motifs are significant. Secondary FDR calculation provided for context.