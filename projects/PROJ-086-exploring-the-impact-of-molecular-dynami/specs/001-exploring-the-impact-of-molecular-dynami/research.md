# Research: Exploring the Impact of Molecular Dynamics Simulation Parameters on Predicted Protein-Ligand Binding Affinity

## 1. Problem Definition & Scope

The project investigates how variations in MD simulation parameters—specifically **force field** (ff14SB, CHARMM36m) and **duration** (0.5ns, 1.0ns, 1.5ns)—affect the accuracy of predicted protein-ligand binding affinities. The accuracy is measured by the **Absolute Error (AE)** between predicted and experimental values from the PDBbind v2020 dataset.

**Constraints**:
- **Hardware**: GitHub Actions Free Tier (2 CPU cores, 7GB RAM, no GPU).
- **Time**: Total wall-clock time ≤ 6 hours.
- **Dataset**: Subsampled to [deferred: target 10] high-quality complexes (≤2.0 Å resolution) from PDBbind v2020 refined subset.
- **Deviation from Constitution**: Due to hardware limits, the study uses shorter durations (0.5-1.5ns vs 5-20ns) and a single temperature (300K vs 300K/310K) and omits ff19SB. This is an exploratory approximation.

## 2. Dataset Strategy

The primary data source is the **PDBbind v2020 refined subset**, which contains protein-ligand complexes with experimentally determined binding affinities.

### Verified Datasets

| Dataset | Source URL | Usage | Notes |
|---------|------------|-------|-------|
| **PDBbind Complexes** | ` | Source of protein-ligand structures and experimental affinities. | Filtered for resolution ≤2.0 Å and size ≤200 residues. |
| **PDBbind Affinities** | ` | Ground truth for error calculation. | Contains `Kd`, `Ki`, and `IC50` converted to kcal/mol. |
| **PDBbind Full** | ` | Backup source for metadata. | Used only if specific complex IDs are missing in the primary source. |

**Dataset Selection Rationale**:
The PDBbind v2020 dataset is the standard for benchmarking binding affinity prediction methods. The "refined" subset is chosen for its high-quality structural data. The subsampling to [deferred: target 10] complexes is a **computational necessity** to satisfy the 6-hour CI limit while still allowing for a blocked experimental design.

**Variable Fit Verification**:
- **Required**: Protein structure (PDB), Ligand structure, Experimental affinity (kcal/mol).
- **Available in PDBbind**: All required variables are present.
- **Gap**: The dataset does not provide pre-simulated trajectories. The pipeline must generate these.

## 3. Methodology

### 3.1 Simulation Protocol (FR-001)
- **Engine**: OpenMM (CPU platform).
- **Solvent**: TIP3P explicit water model.
- **Ions**: Neutralizing ions (Na+/Cl-) added to 0.15M concentration.
- **Force Fields**:
 1. `ff14SB` (Amber)
 2. `CHARMM36m`
- **Durations**: 0.5ns, 1.0ns, 1.5ns (Deviation from Constitution VI).
- **Temperature**: 300K (Langevin thermostat).
- **Time Step**: 2fs.
- **Equilibration**: 100ps NVT + 100ps NPT (minimized).
- **Production**: Variable duration (0.5-1.5ns).
- **Timeout**: Hard 5-minute limit per run (simulation + MM-PBSA).

### 3.2 Binding Energy Calculation (FR-002, FR-003)
- **Method**: MM-PBSA.
- **Tool**: `openmmtools` or `gmx_MMPBSA` (CPU version).
- **Input**: Snapshots extracted from the production trajectory (e.g., every 50ps, max 20 frames).
- **Output**: $\Delta G_{bind}$ in kcal/mol.
- **Error Metric**: **Absolute Error (AE)** = $| \Delta G_{pred} - \Delta G_{exp} |$.
 - *Note*: RMSE is calculated post-hoc as a summary statistic, not as the response variable for the statistical model.

### 3.3 Statistical Analysis (FR-004, FR-005)
- **Design**: Blocked Experiment. 'Complex' is treated as a random blocking factor.
- **Model**: Linear Mixed-Effects Model (LMM).
 - **Formula**: `AE ~ Force_Field + Duration + (1 | Complex)`
 - **Response**: Absolute Error (AE) per complex per parameter set.
 - **Fixed Effects**: Force Field, Duration.
 - **Random Effect**: Complex (intercept).
- **Output**:
 - Fixed effect estimates (coefficient, standard error, 95% CI).
 - Variance components (Variance of Complex, Residual Variance).
 - **Post-hoc**: RMSE calculated from model residuals.
- **Assumptions**:
 - **Normality**: Residuals of the LMM are assumed normal.
 - **Independence**: Errors are independent conditional on the random effect.
 - **Power**: N=10 complexes is low. The study is **exploratory**. Results will be interpreted as effect size estimates with caution, not definitive hypothesis tests.
- **Scientific Caveat**: MM-PBSA is known to have systematic bias that may dominate duration effects in short simulations. The analysis will report effect sizes with wide confidence intervals and acknowledge that 'duration' may show no significant effect due to the short timescale and methodological bias.

## 4. Compute Feasibility & Risk Mitigation

### 4.1 Resource Estimation
- **Simulation Time**: A ns simulation of a medium-sized protein complex on 2 CPU cores typically takes 1-2 minutes in OpenMM.
- **Total Runs**: [deferred: target 10] complexes × 2 FF × 3 Durations = [deferred: ~60] runs.
- **Total Time**: [deferred: 60] runs × 5 min/run (including MM-PBSA) = [deferred: 300] minutes (5 hours).
- **Buffer**: 1 hour remaining for setup and analysis.
- **Risk**: MM-PBSA can be memory-intensive or slow.
 - **Mitigation**: Extract only 10-20 snapshots per trajectory. Hard 5-minute timeout per run.

### 4.2 Dataset & Variable Mismatch
- **Check**: Does PDBbind contain the ligand coordinates? Yes.
- **Check**: Does PDBbind contain the experimental value? Yes.
- **Check**: Are the force fields compatible with the structures? Yes. Ligand parameters will be generated using `antechamber` (Amber) or `CGenFF` (CHARMM) via OpenMM's `pdbfixer` and `openmmforcefields`.

### 4.3 Statistical Rigor
- **Power Limitation**: Acknowledged. N=10 is small. The study is **exploratory**.
- **Causal Framing**: Explicitly stated that results are associational within the blocked design.
- **Validation**: MM-PBSA is an approximation. We will not claim "true" binding energy, but rather "relative accuracy of parameter sets."

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Subsample to [deferred: target 10] complexes** | Required to fit 6-hour CI limit. Full dataset is computationally infeasible. |
| **OpenMM (CPU)** | Only MD engine with reliable CPU-only wheels in `pip` for CI. |
| **MM-PBSA over FEP** | FEP is too computationally expensive for 60 runs on CPU. |
| **Fixed Temperature (300K)** | Deviation from Constitution VI due to time limits. |
| **Short Durations (0.5-1.5ns)** | Deviation from Constitution VI (5-20ns) due to time limits. |
| **LMM over ANOVA** | Required to model 'Complex' as a random effect and handle small N. ANOVA on aggregated RMSE is invalid. |
| **5-minute Timeout** | Stricter than spec's 7-minute limit to ensure total 6-hour budget is met. |
| **Scientific Caveat** | Acknowledged that MM-PBSA bias may dominate duration effects in short simulations. |