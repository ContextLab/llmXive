# Tasks: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the JSON‑Schema contracts in `specs/…/contracts/`.

The study must use **only the FEMNIST dataset**, simulate heterogeneity with Dirichlet α ∈ {0.1, 0.5, 1.0}, run DP‑FedAvg with several ε values, and produce the statistical artefacts required by the specification.  
All tasks are written as canonical checklist items; unchecked boxes indicate work that still needs to be executed.

---

- [ ] **T001** [P] Download FEMNIST (stream → parquet) and enforce Shakespeare exclusion  
  *File*: `code/data/download.py`  
  *Description*: Stream the FEMNIST training and test splits via `datasets.load_dataset(..., streaming=True)`, write `data/raw/femnist_train.parquet` and `data/raw/femnist_test.parquet`, compute a SHA‑256 checksum of the concatenated parquet files and store it as `data/raw/femnist.sha256`. If the script is invoked with `--dataset shakespeare` it must raise `ValueError("Shakespeare excluded per plan.md Gap Analysis")`. **Note**: the correct exception behavior is ensured by task **T015**.  
  *Verification*:  
  – Unit test `tests/unit/test_download.py` that (a) runs the downloader for FEMNIST and checks that the two parquet files exist and that their SHA‑256 matches the recorded value, and (b) asserts that invoking the downloader with `dataset="shakespeare"` raises the exact `ValueError` with the required message.

- [ ] **T002** [P] Verify Shakespeare‑exclusion behaviour with a real test script  
  *File*: `tests/unit/test_shakespeare_exclusion.py`  
  *Description*: Import the download module, call its entry point with `dataset="shakespeare"` and confirm that a `ValueError` with the exact message *“Shakespeare excluded per plan.md Gap Analysis”* is raised. This replaces the brittle grep‑based T000 check noted by the reviewer.  
  *Verification*: `pytest -q tests/unit/test_shakespeare_exclusion.py` must exit with code 0.

- [ ] **T003** [P] Compute the global minority‑client entropy threshold (bottom 25 % percentile)  
  *File*: `code/data/minority_threshold.py`  
  *Description*: Load the full FEMNIST training parquet, compute per‑client label entropy for **all** clients (using the official LEAF client IDs), determine the 25th percentile of the entropy distribution, and write the numeric threshold to `data/metadata/minority_threshold.json`. This single global threshold will be used by the partitioner to flag minority clients (FR‑006).  
  *Verification*: A sanity‑check script `tests/unit/test_minority_threshold.py` loads the JSON and asserts that the value lies between 0 and log₂(62) and that at least one client’s entropy is ≤ threshold.

- [ ] **T004** [P] Dirichlet‑based client partitioning (reproducible)  
  *File*: `code/data/partition.py`  
  *Description*: For each seed in **{0,…,9}** and each α ∈ {0.1, 0.5, 1.0}, sample a Dirichlet distribution to obtain client‑label probability vectors, assign FEMNIST examples accordingly, and write the metadata to `data/partitions/partition_femnist_{seed}_{alpha}.json`. Each JSON must contain per‑client fields `client_id`, `samples`, `label_dist`, `entropy`, and `is_minority` (using the threshold from T003). After writing, compute and store the file’s SHA‑256 in the same directory (e.g., `partition_femnist_0_0.1.sha256`).  
  *Verification*: `tests/unit/test_partition_reproducibility.py` runs the partitioner twice with the same `(seed, α)` and asserts that the two JSON files are byte‑identical (matching SHA‑256).

- [ ] **T005** [P] Tiny CNN model and per‑client data loader  
  *File*: `code/models/cnn.py` and `code/data/loader.py`  
  *Description*: Implement a convolutional network with ≤ 50 k parameters suitable for FEMNIST (e.g., two Conv2d layers + one fully‑connected layer). Provide a `get_client_loader(client_id, partition_path, seed)` helper that returns a `torch.utils.data.DataLoader` for the client’s samples, seeded for deterministic shuffling.  
  *Verification*: `tests/unit/test_model_loader.py` checks that the model can be instantiated, that a loader returns at least one batch, and that two loaders created with the same seed produce identical batches.

- [ ] **T006** [P] DP‑FedAvg training loop (Opacus) and non‑DP baseline  
  *Files*: `code/training/fedavg_dp.py` and `code/training/fedavg_baseline.py`  
  *Description*:  
  – Wrap the CNN with `opacus.PrivacyEngine` (Gaussian noise, clipping norm = 1.0).  
  – For a target ε (any numeric value) compute the required noise multiplier using the Moments Accountant (δ = 1e‑5).  
  – Track the cumulative privacy budget (`actual_epsilon`) after each round and log it.  
  – The baseline script runs the identical FedAvg loop **without** Opacus and records `epsilon="inf"` and `is_dp=False`.  
  *Verification*: After a short 3‑round run, `results/raw_logs.csv` must contain the columns `epsilon`, `actual_epsilon`, and `is_dp`. A deterministic sampling rule is used for the epsilon‑tolerance test: for each ε value, the first three seeds (0, 1, 2) are examined, and the test asserts `abs(actual_epsilon - target_epsilon) ≤ 0.05` for those runs.

- [ ] **T014** [P] Pre‑sweep power analysis (paired‑t, α=0.05, power=0.80)  
  *File*: `code/analysis/power.py`  
  *Description*: Before any training runs, compute the minimum detectable effect size (Cohen’s d) for the planned number of seeds per configuration (default 10). The calculation uses a paired‑t framework, α = 0.05, power = 0.80, and accounts for the Bonferroni‑adjusted number of ε‑α configurations. Write the result to `results/power_analysis.json` and record the value in `results/summary.csv` metadata. If the orchestrator later reduces the seed count (per Section 5 budget policy) the same script will be re‑run to update the detectable effect size.  
  *Verification*: Unit test `tests/unit/test_power_analysis.py` checks that the JSON file exists and that the reported `minimum_detectable_d` matches the analytic calculation for the given seed count.

- [ ] **T007** [P] Full experiment orchestrator (sweep)  
  *File*: `code/main.py`  
  *Description*: Loop over:  
  – **Seeds** = 10 (0‑9) (subject to reduction per Section 5 budget policy)  
  – **α** ∈ {0.1, 0.5, 1.0} (subject to reduction)  
  – **ε** ∈ {0.5, 1.0, 2.0, 5.0, inf} (subject to reduction)  
  For each configuration run the DP trainer **and** the baseline trainer on the **same** partition file.  
  – Enforce a wall‑clock budget: after each communication round estimate remaining time; if the projected total exceeds the CI budget, stop further rounds, set `is_time_limited=True`, and record the last round as censored.  
  – All random generators (Python, NumPy, PyTorch, and the Dirichlet sampler) are seeded with the combination `(seed, α, ε)`.  
  – Append per‑round metrics to `results/raw_logs.csv` (schema‑validated).  
  *Verification*: After the orchestrator finishes, a validation script computes the expected row count as `2 * actual_seeds * actual_alphas * actual_epsilons` (where the actual numbers reflect any reductions) and asserts that `results/raw_logs.csv` contains exactly that many rows. It also checks that each `(seed, α, ε)` pair appears twice (DP and baseline).

- [ ] **T008** [P] Statistical analysis and power‑analysis integration  
  *File*: `code/analysis/stats.py`  
  *Description*:  
  1. Load `results/raw_logs.csv`.  
  2. Flag `utility_collapse=True` for any run with `global_accuracy < 1/62`.  
  3. Compute `rounds_to_target` as the first round where `global_accuracy ≥ target_fraction * baseline_final_accuracy` (default `target_fraction=0.90`) for each `(α, ε, seed)`; if never reached, set `converged=False` and keep the final round number.  
  4. Perform a **paired** comparison of DP vs. baseline global accuracy for each `(α, ε)` using:  
     – Shapiro‑Wilk normality test on the paired differences.  
     – If normal (p > 0.05) → paired t‑test; else → Wilcoxon signed‑rank test.  
     – Report raw p‑value, Cohen’s d (or rank‑biserial), and a significance flag (α = 0.05). No Bonferroni correction is applied (as not required by the specification).  
  5. Fit a mixed‑effects model `degradation ~ α * ε * is_minority + (1 + ε + α | seed)` using `statsmodels.MixedLM`; extract the three‑way interaction coefficient, the two‑way interaction coefficients, 95 % CIs, and raw p‑values.  
  6. Compute the minority‑vs‑majority accuracy gap per configuration and its effect size.  
  7. Incorporate the pre‑sweep power‑analysis result from `results/power_analysis.json` into the final report.  
  8. Write all statistics to `results/final_stats.csv`.  
  *Verification*: `tests/unit/test_statistics.py` loads the CSV and asserts that required columns exist, that the three‑way interaction term is present, and that raw p‑values are ≤ 1.

- [ ] **T009a** [P] Convergence speed measurement (relative target)  
  *File*: `code/analysis/convergence.py`  
  *Description*: For each run, compute `rounds_to_target` as described in T008 (90 % of the corresponding non‑DP baseline’s final global accuracy). Record this value in `results/raw_logs.csv` under the column `rounds_to_target`. Flag runs that never reach the target with `converged=False`. No extra `matched_rounds` or `censoring` fields are generated, keeping the output compatible with the existing results schema.  
  *Verification*: Unit test `tests/unit/test_convergence.py` confirms that the column exists, that at least one run has `converged=True`, and that runs with `is_time_limited=True` are still present.

- [ ] **T009b** [P] Generate privacy‑utility and convergence‑speed figures  
  *File*: `code/analysis/plots.py`  
  *Description*: Using the aggregated statistics:  
  – Plot **accuracy vs. ε** for each α (error bars = 95 % CI), saved as `figures/privacy_utility_accuracy.png`.  
  – Plot **rounds_to_target vs. ε** for each α (censored points shown with an open marker), saved as `figures/privacy_utility_convergence.png`.  
  – Overlay minority‑client accuracy degradation on the global accuracy curves (`figures/minority_overlay.png`).  
  All plots include axis labels, legends, and a caption describing the confidence‑interval method. No extra `matched_rounds` or `censoring` fields are generated.  
  *Verification*: `tests/unit/test_plots.py` loads each PNG and checks that the file size > 5 KB and that the PNG header is valid.

- [ ] **T010** [P] Assemble final summary table and validation report  
  *File*: `code/analysis/summary.py`  
  *Description*: Combine the per‑configuration rows from `final_stats.csv` into `results/summary.csv` containing the fields enumerated in FR‑011 (mean/std accuracy, mean degradation, p‑values, interaction estimates, counts of collapsed and time‑limited runs, minority‑gap, power‑effect‑size, etc.). Create `results/validation_report.md` that documents:  
  – SHA‑256 verification of the raw FEMNIST parquet files,  
  – Reproducibility of partitions (matching hashes),  
  – Correlation (Pearson r) between client entropy and α (diagnostic from T004),  
  – Confirmation that the Shakespeare‑exclusion unit test passes,  
  – Counts of flagged collapsed and time‑limited runs, and  
  – Results of a sensitivity analysis that excludes those flagged runs.  
  *Verification*: `tests/unit/test_summary.py` parses both CSV and MD files and asserts that all required columns/sections are present and that the reported hash values match the actual files on disk.

- [ ] **T011** [P] Write a reproducible quick‑start guide  
  *File*: `quickstart.md` (project root)  
  *Description*: Provide step‑by‑step commands to (1) install dependencies (`pip install -r requirements.txt`), (2) run the full pipeline (`python -m code.main`), (3) locate the key artefacts (`results/summary.csv`, `figures/*.png`), and (4) verify reproducibility by re‑running and checking that the SHA‑256 values in `validation_report.md` match. Include the exact command used by the orchestrator (`python -m code.main --seeds 0-9 --alphas 0.1,0.5,1.0 --epsilons 0.5,1.0,2.0,5.0,inf`).  
  *Verification*: Running `bash scripts/quickstart_check.sh` (generated by the guide) must complete without error and produce a log file `results/quickstart_verification.log` containing the phrase “All checks passed”.

- [ ] **T012** [P] Comprehensive pytest suite covering all scientific components  
  *Directory*: `tests/` (unit + integration)  
  *Description*: Add tests for:  
  1. Download & Shakespeare exclusion (T001, T002).  
  2. Global minority‑threshold computation (T003).  
  3. Partition reproducibility and minority flag correctness (T004).  
  4. Model instantiation & deterministic client loader (T005).  
  5. DP budget tracking tolerance (T006).  
  6. Orchestrator output completeness and dynamic row‑count verification (T007).  
  7. Pre‑sweep power analysis (T014).  
  8. Statistical analysis outputs, three‑way interaction term, and power‑analysis integration (T008).  
  9. Plot generation sanity checks (T009b).  
  10. Summary table integrity and validation‑report completeness (T010).  
  11. Quick‑start reproducibility script (T011).  
  All tests must pass (`pytest -q`) on a fresh CI runner.  
  *Verification*: The CI pipeline will execute `pytest -q`; a passing run is the required evidence.

- [ ] **T013** [P] End‑to‑end reproducibility verification on a clean environment  
  *File*: `scripts/reproducibility_check.sh`  
  *Description*: A shell script that (a) deletes the `data/`, `results/`, and `figures/` directories, (b) runs the quick‑start command, (c) recomputes the SHA‑256 checksums of the generated FEMNIST parquet files and partition JSONs, (d) compares them against the values recorded in `validation_report.md`, and (e) writes a concise pass/fail summary to `results/reproducibility_log.txt`.  
  *Verification*: The script must exit with status 0 and the log must contain “Reproducibility check passed”. This script is invoked as the final step of the CI pipeline to certify that the entire study is fully reproducible from scratch.

- [ ] **T015** [P] Fix download script to raise correct `ValueError` for Shakespeare exclusion  
  *File*: `code/data/download.py`  
  *Description*: Ensure the argument parser validates the `--dataset` option and raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` when the value is `"shakespeare"`. Add explicit unit‑test coverage if needed.  
  *Verification*: Running the module with `--dataset shakespeare` must raise the exact `ValueError`; the existing `test_download.py` will now pass.

- [ ] **T016** [P] Fix Shakespeare‑exclusion unit test to correctly assert `ValueError`  
  *File*: `tests/unit/test_shakespeare_exclusion.py`  
  *Description*: Update the test to import the corrected download entry point and use `with pytest.raises(ValueError, match="Shakespeare excluded per plan.md Gap Analysis"):` to verify the exception.  
  *Verification*: `pytest -q tests/unit/test_shakespeare_exclusion.py` exits with code 0.

- [ ] **T017** [P] Remove unsupported fields from results output  
  *Files*: `code/training/fedavg_dp.py`, `code/training/fedavg_baseline.py`, `code/analysis/convergence.py`  
  *Description*: Ensure that the CSV writer does not include `matched_rounds` or `censoring` columns; rename any existing logic to drop them before writing. Update any downstream scripts to rely only on schema‑defined fields.  
  *Verification*: Run a short sweep and validate `results/raw_logs.csv` against `specs/001-evaluating-the-effectiveness-of-differen/contracts/results.schema.yaml` using a schema validator; it must pass.
