# Tasks: Single-Cell Trajectories of T‑Cell Exhaustion

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the contract schemas under `specs/001-single-cell-trajectories-of-t-cell-exhau/contracts/`.  
The goal is to deliver a fully reproducible, CPU‑only pipeline that satisfies every functional requirement (FR‑001 – FR‑012) and scientific criteria (SC‑001 – SC‑007).

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a thin, reproducible pipeline on a single GEO dataset and verify the project scaffolding. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] **T001** Create the required project layout, **add a `data/results/` directory with a placeholder file**, configure linting/formatting, and document a runnable command in `quickstart.md`. <!-- FAILED-IN-EXECUTION: code/setup_lint.sh exit=1 -->
  - **File path**: `projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/` (tree) and `quickstart.md`.  
  - **Verification**:  
    - `tree` shows `data/results/` containing a placeholder (e.g., `.gitkeep`).  
    - `ruff check .` and `black --check .` both return exit‑code 0 and their outputs are saved to `logs/lint.txt`.  
    - `quickstart.md` contains the command `python -m code.run_all` and a brief usage example.

- [ ] **T002** Implement a robust GEO downloader (`code/download_data.py`) that:   <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 -->
  1. Queries the NCBI GEO metadata endpoint for each accession (GSE136103, GSE127465, GSE111075, GSE138852).  
  2. Retrieves the supplementary count matrix (either `.mtx`/`.h5` or raw FASTQ converted to counts).  
  3. Saves files under `data/raw/<accession>/` and records a **SHA‑256 checksum** in `data/manifest.yaml`.  
  4. Computes `marker_gene_fraction` (≥ 0.80) against the required marker list (PD‑1, LAG3, TOX, etc.) and writes a `Dataset` entry that validates against `contracts/dataset.schema.yaml`.  
  - **File path**: `code/download_data.py`.  
  - **Verification**:  
    - Running `python -m code.download_data` completes with exit code 0, creates four `Dataset` entries in `data/manifest.yaml`, and logs success in `logs/download.log`.  
    - `pytest tests/unit/test_download.py` passes, confirming checksum existence and `marker_gene_fraction ≥ 0.80`.

- [ ] **T003** Implement the QC & normalization pipeline:  
  1. `code/preprocess.R` (Seurat v4) loads a raw count matrix, **annotates mitochondrial genes using a curated list that contains both Ensembl IDs and the `MT-` prefix**, filters cells with > 20 % mitochondrial reads, and performs log‑normalization + selection of 2 000 HVGs.  
  2. `code/preprocess.py` is a thin Python wrapper that invokes the R script via `subprocess.run(..., check=True)`.  
  3. Outputs a processed AnnData file `data/processed/<accession>_processed.h5ad`.  
  - **File path**: `code/preprocess.R`, `code/preprocess.py`.  
  - **Verification**:  
    - `pytest tests/unit/test_preprocess.py` runs the wrapper on a **real** downloaded dataset and asserts that the number of cells after QC is **< 90 %** of the original (i.e., at least some cells were removed).  
    - The test also checks that the AnnData object contains a `pct_mt` column and that the filter condition (`pct_mt > 20`) was applied.

- [ ] **T004** Implement the scVelo velocity pipeline (`code/velocity.py`) that:  
  1. Loads the processed AnnData from T003, runs `scvelo.tl.recover_dynamics` and `scvelo.tl.velocity` in **CPU‑only** mode (`device='cpu'`).  
  2. Times the run and aborts with a clear error if wall‑clock time exceeds **45 minutes**.  
  3. Writes the velocity graph (`.h5ad`) to `data/results/<accession>_velocity.h5ad`.  
  - **File path**: `code/velocity.py`.  
  - **Verification**:  
    - Execution of `python -m code.velocity --dataset GSE136103` finishes within 45 minutes, produces an `.h5ad` containing the layers `spliced`, `unspliced`, `velocity`, and an `obs` column `pseudotime`.  
    - `pytest tests/integration/test_trajectory_reconstruction.py` confirms the presence of these layers and that `runtime_seconds < 2700`.  

- [ ] **T005** Add a lightweight unit‑test suite for the three scripts above (download, preprocess, velocity) **and generate linting evidence**.  
  - **File path**: `tests/unit/test_download.py`, `tests/unit/test_preprocess.py`, `tests/unit/test_velocity.py`.  
  - **Verification**:  
    - All three tests pass on the CI runner; the test log is recorded in `logs/`.  
    - `logs/lint.txt` contains the successful output of `ruff check .` and `black --check .`.  

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Expand to all four datasets, detect fork‑points, perform power analysis, cross‑dataset validation, and generate the final report. |
|------|------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T006** **(No batch‑effect correction required)** – This task is retained for traceability but marked as *not required* because the specification does not mandate any batch‑effect step. No script is generated and verification is omitted.  

- [ ] **T007** Implement the Markov‑chain pseudotime aligner (`code/aligner.py`).  
  - Takes the (optional) integrated AnnData from T006 (if present), aligns trajectories across datasets, retries up to two times with increased regularization if convergence fails, and writes `data/processed/unified_trajectory.h5ad` plus a small `alignment_status` flag.  
  - **Verification**:  
    - `pytest tests/unit/test_aligner.py` runs on a toy dataset and asserts that `alignment_status == "success"` (or `"partial"` with a warning).  

- [ ] **T008** Implement fork‑point detection (`code/forkpoint.py`).  
  - For each dataset’s velocity graph (from T004) it computes per‑cell velocity‑field divergence, builds a **1,000‑permutation** null distribution by shuffling cell topology while preserving splicing kinetics, flags branches with `p < 0.01` and `divergence > 1.5 × null_std`.  
  - Extracts genes expressed at those branches, computes differential timing, filters for `> 0.1` pseudotime units, ranks them (1 = earliest), and writes `data/results/fork_points/<accession>_fork_points.csv` conforming to `contracts/fork_point.schema.yaml`.  
  - **Verification**:  
    - At least one high‑confidence branch (`confidence == "high"`) is present in each CSV.  
    - `pytest tests/unit/test_forkpoint.py` validates schema compliance and that the number of genes with `timing_rank ≤ 10` is ≥ 5.  

- [ ] **T009** Implement a simulation‑based power analysis (`code/power_analysis.py`).  
  - Simulates **10 000** Monte‑Carlo runs for the divergence test (effect size d = 0.5) and the enrichment test (Δ = 0.3), α = 0.05, and estimates power.  
  - If either test yields `< 80 %` power, the script aborts with a clear message and writes `data/results/validation/power_analysis.json`.  
  - **Verification**:  
    - Running the script on the real dataset set produces a JSON with `"power_adequate": true`.  
    - `pytest tests/unit/test_power_analysis.py` checks that the reported power is ≥ 0.80.  

- [ ] **T010** Implement enrichment against the independent therapy‑response signature (`code/enrichment.py`).  
  - Loads the external gene set from the supplementary file of PMID 32012345, performs Fisher’s exact test and a two‑sided t‑test on mean expression of fork‑point genes versus the signature, applies Benjamini‑Hochberg correction, and writes `data/results/validation/<accession>_enrichment.json`.  
  - **Verification**:  
    - Adjusted p‑value < 0.01 for at least one dataset.  
    - `pytest tests/unit/test_enrichment.py` confirms schema compliance (`contracts/validation.schema.yaml`) and the significance flag.  

- [ ] **T011** Implement cross‑dataset bootstrap validation (`code/validate.py`).  
  - Performs **1,000** bootstrap resamples of the combined cell population, computes enrichment confidence intervals, and calculates Spearman rank correlation of the top‑3 fork‑point genes across all four datasets (require ≥ 0.80).  
  - Writes a consolidated validation file `data/results/validation/cross_dataset_validation.json`.  
  - **Verification**:  
    - `pytest tests/unit/test_validate.py` asserts `cross_dataset_correlation >= 0.80` and that the JSON contains a 95 % CI array of length 2.  

- [ ] **T012** Generate the final HTML report (`code/report.py`).  
  - Assembles velocity UMAPs, divergence heatmaps, the ranked gene table, the cross‑dataset heatmap with bootstrap CIs, power‑analysis summary, enrichment statistics, and inserts the mandatory disclaimer (FR‑009).  
  - Outputs `data/results/report/final_report.html`.  
  - **Verification**:  
    - A regex check (`grep -i "associational"` ) succeeds on the HTML file.  
    - `pytest tests/unit/test_report.py` confirms the presence of the disclaimer paragraph and that all figure files referenced in the HTML exist.  

- [ ] **T013** Add integration tests that run the **full pipeline** on a reduced‑size but real subset (first 500 cells of each dataset) to guarantee end‑to‑end reproducibility within the CI time budget.  
  - **File path**: `tests/integration/test_full_pipeline.py`.  
  - **Verification**: The test completes in < 6 h on the CI runner and all intermediate artifacts validate against their schemas.  

---

## Phase 3 – Reproducible results and paper handoff  

| Goal | Demonstrate that the entire workflow can be rerun from raw inputs and produce stable, documented artifacts for the downstream paper pipeline. |
|------|------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T014** Provide a single entry‑point script (`code/run_all.py`) that orchestrates the steps: download → preprocess → (optional) batch‑correct → velocity → aligner → fork‑point → power analysis → enrichment → validation → report.  
  - The script reads the global random seed from `code/config.yaml` (`seed: 42`) and logs each stage to `logs/<stage>.log`.  
  - **Verification**:  
    - Running `python -m code.run_all` from a clean checkout reproduces **identical SHA‑256 hashes** for all final artifacts (`data/results/fork_points/*`, `data/results/validation/*`, `data/results/report/final_report.html`).  
    - The CI logs contain “Pipeline completed successfully” and a summary table of runtimes.  

- [ ] **T015** Write a concise methods & results narrative (`docs/summary.md`) that:  
  1. Describes each pipeline stage, references the exact script and artifact paths.  
  2. Lists any datasets that were skipped (e.g., < 1000 cells) and any low‑confidence branches.  
  3. Includes the disclaimer verbatim (FR‑009).  
  - **Verification**:  
    - `pytest tests/unit/test_summary.py` runs a reference‑validator that checks for required citation formats and the presence of the disclaimer.  

- [ ] **T016** Handoff to the paper‑stage pipeline: create a `paper/` directory containing a `manifest.yaml` that lists all figures, tables, and the final HTML report with their SHA‑256 hashes, and a short README pointing to `docs/summary.md`.  
  - **Verification**:  
    - `ruff` and `black` checks pass on the new `paper/` files.  
    - A CI step runs `python -c "import yaml, sys; yaml.safe_load(open('paper/manifest.yaml'))"` to ensure the manifest is valid YAML.  

---

## Dependencies and requirement coverage  

| Spec requirement | Task(s) that satisfy it | Verification command |
|------------------|------------------------|----------------------|
| **FR‑001** (download & cache) | T002 | `python -m code.download_data` |
| **FR‑002** (QC & normalization) | T003 | `pytest tests/unit/test_preprocess.py` |
| **FR‑003** (scVelo CPU ≤45 min) | T004 | `pytest tests/integration/test_trajectory_reconstruction.py` |
| **FR‑004** (fork‑point significance) | T008 | `pytest tests/unit/test_forkpoint.py` |
| **FR‑005** (gene ranking) | T008 | CSV contains `timing_rank` column |
| **FR‑006** (bootstrap enrichment) | T011 | `pytest tests/unit/test_validate.py` |
| **FR‑007** (final heatmap & report) | T012 | `pytest tests/unit/test_report.py` |
| **FR‑008** (therapy‑response signature) | T010 | Adjusted p‑value < 0.01 |
| **FR‑009** (observational disclaimer) | T012, T015 | Regex search for “associational” |
| **FR‑010** (marker‑gene ≥80 %) | T002 | `tests/unit/test_download.py` |
| **FR‑011** (power ≥80 %) | T009 | `tests/unit/test_power_analysis.py` |
| **FR‑012** (no dataset substitution) | T002 | Manifest lists the four exact GEO IDs |
| **SC‑001** (CPU‑only feasibility) | T004 | Log shows `device='cpu'` and no CUDA errors |
| **SC‑002** (enrichment significance) | T010 | Adjusted p‑value < 0.01 |
| **SC‑003** (statistical thresholds) | T008, T010 | p‑values < 0.01 in respective outputs |
| **SC‑004** (disclaimer) | T012, T015 | Regex check passes |
| **SC‑005** (marker‑gene presence) | T002 | `marker_gene_fraction >= 0.80` |
| **SC‑006** (therapy‑response enrichment) | T010 | Fisher’s exact test p < 0.01 |
| **SC‑007** (power adequacy) | T009 | `"power_adequate": true` in JSON |

---  

*All tasks remain unchecked (`- [ ]`) until the corresponding implementation and verification pass in CI. The ordering respects data flow: each downstream task depends on the artifact(s) produced by its predecessor(s).*