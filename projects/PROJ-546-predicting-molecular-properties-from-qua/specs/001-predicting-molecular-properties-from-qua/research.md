# Research: Predicting Molecular Properties from Quantum Chemical Calculations

## Executive Summary

This research validates the feasibility of predicting molecular barrier heights using a hybrid semi-empirical and high-level DFT approach. The study leverages a verified experimental dataset from Zenodo (ID fetched from `idea.md`) and computes quantum descriptors using DFTB+ (full set) and Psi4 (subset). The primary challenge is computational feasibility within a constrained CPU time limit of GitHub Actions. The research question investigates whether a reduced subset of data can be processed efficiently under computational constraints. The method employs a scaled-down CPU to evaluate a manageable subset size, demonstrating that while full DFT remains intractable for large sets, a representative subset is feasible (). The plan strictly avoids gated datasets and relies on open, verifiable sources.

**Critical Clarification**: The goal is **purely correlational**. We do not claim that DFTB+ or DFT descriptors *cause* the barrier heights. The comparison is between two approximations of the same function (mapping descriptors to experimental barriers). The analysis cannot distinguish whether the Semi-Empirical model fails due to poor descriptors or poor model fit, as the 'truth' is fixed. The goal is to measure the correlation strength of gas-phase electronic properties with macroscopic experimental barriers.

## Dataset Strategy

### Verified Datasets

The project relies on the following verified sources for input data:

1. **Experimental Barrier Dataset (Primary)**:
 * **Source**: Zenodo (Accession ID fetched from `idea/predicting-molecular-properties-from-qua.md` and verified before execution).
 * **Verification**: The Zenodo record is the canonical source. The dataset contains `smiles`, `experimental_barrier`, and `molecule_id`.
 * **Access**: Direct download via Zenodo API or file URL.
 * **Status**: **Verified**. The spec explicitly references a Zenodo source.

2. **Auxiliary Datasets (HOMO/LUMO/SMILES)**:
 * The `# Verified datasets` block provides several Hugging Face datasets (e.g., `matchbench/semi-homo`, `maykcaldas/smiles-transformers`).
 * **Decision**: These are **NEVER used**, even for validation or pre-training. The study is strictly anchored to the Zenodo experimental barrier dataset to maintain Single Source of Truth (Principle IV). Using auxiliary datasets would introduce unverified provenance and violate the spec's requirement to compute descriptors from the specific experimental molecules.

### Data Availability & Feasibility

* **Zenodo Dataset**: Must be downloaded via programmatic fetch (e.g., `requests` or `zenodo_get`). The file size is expected to be small (CSV), fitting easily within the available disk and RAM limits.
* **Streaming**: Not required for the input CSV, but the optimized geometries (XYZ files) will be written to disk incrementally to avoid memory spikes.
* **Gated Data**: The plan explicitly avoids ADNI, HCP, or other gated datasets. The Zenodo source is open.

### Dataset-Variable Fit

* **Required Variables**: `smiles`, `experimental_barrier`, `molecule_id`.
* **Derived Variables**: `HOMO_energy`, `LUMO_energy`, `mayer_bond_order` (computed), `mw`, `atom_count`, `functional_groups` (confounds).
* **Fit**: The Zenodo dataset provides the necessary input. The computed descriptors will be generated from the SMILES strings via DFTB+ and Psi4. No external dataset is needed for predictors.

## Computational Strategy

### CPU-First Approach (GitHub Actions)

1. **Semi-Empirical (DFTB+)**:
 * **Feasibility**: DFTB+ is designed for speed and is CPU-tractable for moderate-sized molecules.
 * **Strategy**: Run geometry optimization and descriptor extraction on the full dataset.
 * **Optimization**: Use a minimal basis set (e.g., `mio` or `3ob` parameter set) and strict convergence criteria to balance speed and accuracy.
 * **Memory**: Stream the dataset; process molecules one-by-one or in small batches (e.g., 10) to stay under 7 GB RAM.

2. **High-Level DFT (Psi4)**:
 * **Feasibility**: Full DFT for a large dataset is **not** feasible on the CPU runner.
 * **Strategy**: Restrict to a **stratified random subset of 50 molecules** (as per US2).
 * **Method**: Use a modest basis set (e.g., `def2-SVP`) and a limited number of SCF iterations.
 * **Environment**: **Both DFTB+ and Psi4 are installed in the SAME Conda environment** to ensure identical library versions and floating-point precision, eliminating hardware/software confounds.
 * **No GPU Offload**: The pipeline is self-contained within GitHub Actions. No external GPU kernels are used.

### Statistical Rigor

* **Paired T-Test**: The comparison between Semi-Empirical RF and DFT RF models will use a paired t-test on the **out-of-fold** predictions from the 50-sample subset.
 * **Null Hypothesis**: No difference in error distribution between Semi-Empirical RF and DFT RF models.
 * **Significance**: α = 0.05.
 * **Correction**: Not strictly required for a single t-test, but the sensitivity analysis will involve multiple comparisons. A Bonferroni correction or False Discovery Rate (FDR) will be applied if multiple hypothesis tests are run on the sensitivity results.
* **Power Analysis**: The sample size is fixed by the spec. The plan acknowledges the **low statistical power** to detect small effect sizes. To mitigate this:
 * Use **5-fold Cross-Validation** with **out-of-fold** predictions for the t-test.
 * Apply **bootstrapping** to estimate confidence intervals.
 * Use a **Wilcoxon signed-rank test** if normality assumptions fail.
 * Explicitly state in the report that results are interpreted with caution due to low power.
* **Causal Inference**: The study is observational (correlational). Claims will be framed as "association" between descriptors and barriers, not causation.
* **Collinearity**: HOMO and LUMO are often correlated. The plan will check for multicollinearity (VIF) in the Random Forest models and report the relationship descriptively.
* **Confound Control (FR-008)**:
 * Calculate Molecular Weight (MW), Atom Count, and **functional group enumeration**.
 * Perform **partial correlation analysis** to isolate the effect of quantum descriptors from molecular size.
 * Report the **change in R²** when MW/functional groups are added as covariates.

## Edge Case Handling

* **Convergence Failure**:
 1. Retry once with a different initial guess.
 2. If failed, log to `logs/convergence_failures.log` with `molecule_id`, `timestamp`, `error_code`, `error_message`.
 3. Status: `failed_after_retry`.
* **OOM**: Monitor memory usage. If exceeded, kill process, log to `logs/oom_failures.log`.
* **Physical Invalidity**:
 1. If `HOMO >= LUMO`, retry once.
 2. If still failed, log to `logs/structural_failures.log`.
 3. Do not blindly skip to avoid selection bias.

## Limitations

* **Circular Validation**: The comparison is between two approximations of the same function against a noisy experimental target. It does not validate the physical accuracy of the quantum calculations. The analysis cannot distinguish whether the Semi-Empirical model fails due to poor descriptors or poor model fit.
* **Category Error**: Experimental barrier heights are macroscopic observables influenced by solvent, temperature, and entropy, whereas HOMO/LUMO are gas-phase electronic properties. The model learns a statistical mapping, not a physical verification.
* **Low Power**: N=50 limits the ability to detect small effect sizes. Results are interpreted with caution.
* **Confound Bias**: Despite partial correlation analysis, unmeasured confounds may exist.

## Decision/Rationale

* **CPU vs. GPU**: The primary pipeline (DFTB+) is CPU-first. The DFT subset (50 samples) is small enough to be attempted on CPU. The pipeline is self-contained within GitHub Actions. No external GPU kernels are used.
* **Dataset Choice**: The Zenodo dataset is the only verified source for the *experimental barriers*. Auxiliary HuggingFace datasets are **NEVER used**.
* **Statistical Method**: Paired t-test on out-of-fold predictions is appropriate for comparing two models on the same test set. Sensitivity analysis uses rank correlation (Spearman) to assess stability. Bootstrapping and Wilcoxon tests are used to mitigate low power.
