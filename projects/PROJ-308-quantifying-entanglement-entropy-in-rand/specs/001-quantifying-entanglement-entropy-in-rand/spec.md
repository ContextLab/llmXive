# Feature Specification: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

**Feature Branch**: `[PROJ-308-001-quantify-entanglement]`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Entanglement Scaling for a Single Parameter Set (Priority: P1)

A researcher wants to obtain the entanglement‑entropy scaling exponent for a specific chain length \(L\) and disorder strength \(\delta\).

**Why this priority**: This is the core deliverable; without it the project provides no scientific insight.

**Independent Test**: Execute the workflow with \(L=30\), \(\delta=0.2\) and verify that a scaling exponent \(\alpha\) with a [deferred] bootstrap confidence interval is produced together with a plot of \(S(l)\) vs. subsystem size \(l\).

**Acceptance Scenarios**:

1. **Given** the default configuration (chain length 30, \(\delta=0.2\), 100 disorder realizations), **When** the GitHub‑Actions job finishes, **Then** the output folder contains  
   - `entropy_data.csv` (entropy per realization and bipartition)  
 - `scaling_fit.txt` (exponent \(\alpha\), [deferred] CI, p‑value)
   - `entropy_vs_l.png` (log‑log plot)  

2. **Given** the same configuration, **When** the reported p‑value ≤ 0.05, **Then** the result is marked “statistically significant” in `scaling_fit.txt`.

---

### User Story 2 – Scan Across Disorder Strengths to Locate the MBL‑Thermal Crossover (Priority: P2)

A researcher wants to run the workflow over a range of \(\delta\) values to map how the scaling exponent evolves from area‑law to logarithmic growth.

**Why this priority**: Enables the primary scientific objective—identifying universal scaling that distinguishes phases.

**Independent Test**: Provide a CSV `delta_grid.csv` containing \(\delta = \{0.0, 0.1, 0.2, 0.3, 0.4\}\). After the job completes, a summary file `delta_vs_exponent.csv` must list each \(\delta\) with its fitted exponent and confidence interval.

**Acceptance Scenarios**:

1. **Given** `delta_grid.csv` with five values, **When** the job runs, **Then** `delta_vs_exponent.csv` contains five rows, each with a numeric exponent \(\alpha\) and a [deferred] CI width ≤ 0.05.

2. **Given** the same run, **When** \(\delta=0.0\) the fitted exponent is within 10 % of the theoretical CFT value \((c_{\text{eff}}/3)\approx0.33\), **Then** the entry for \(\delta=0\) is flagged “critical‑regime agreement”.

---

### User Story 3 – Perform Bootstrap Validation of Scaling Exponents (Priority: P3)

A researcher wants to assess the robustness of each exponent estimate via bootstrap resampling.

**Why this priority**: Guarantees that reported scaling laws are not artefacts of finite disorder sampling.

**Independent Test**: After a run, the file `bootstrap_summary.txt` must report the number of bootstrap resamples (≥ 1000), the standard error of the exponent, and the two‑sided p‑value.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** the bootstrap analysis finishes, **Then** `bootstrap_summary.txt` shows exactly 1000 resamples and a reported standard error ≤ 0.02 for the exponent.  

2. **Given** the same, **When** the p‑value > 0.05, **Then** the exponent is labelled “not statistically significant” and the researcher is advised to increase disorder realizations.

---

### Edge Cases

- What happens when the user supplies a disorder strength \(\delta\) outside the allowed range \([0,1]\)?
- How does the system handle a chain length \(L\) that exceeds the maximum supported size (e.g., \(L>50\))?
- What if the TEBD imaginary‑time evolution fails to converge within the allotted 6‑hour job limit?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept user‑specified parameters: chain length \(L\) (integer, 20 ≤ \(L\) ≤ 40), disorder strength \(\delta\) (float, 0 ≤ \(\delta\) ≤ 1), number of disorder realizations \(N_{\text{real}}\) (default 100, max 200), and random seed (integer).  
- **FR-002**: System MUST generate the XXZ Heisenberg Hamiltonian with random nearest‑neighbour couplings \(J_i\sim\mathcal{U}[1-\delta,\,1+\delta]\).  
- **FR-003**: System MUST compute the ground state for each disorder realization using imaginary‑time TEBD via the TeNPy library, with a convergence tolerance of \(10^{-8}\) in energy.  
- **FR-004**: System MUST evaluate the von Neumann entropy \(S(l) = -\mathrm{Tr}(\rho_A \ln\rho_A)\) for every bipartition size \(l\in\{1,\dots,L-1\}\) and store the results per realization.  
- **FR-005**: System MUST perform linear regression of \(S(l)\) versus \(\log l\) (or versus \(l^\alpha\) for area‑law testing) and output the fitted exponent \(\alpha\) with a [deferred] bootstrap confidence interval.
- **FR-006**: System MUST conduct bootstrap resampling with **≥ 1000** resamples to estimate the standard error and two‑sided p‑value for \(\alpha\).  
- **FR-007**: System MUST generate the following artefacts for each run:  
  - `entropy_data.csv` (raw entropies),  
  - `entropy_vs_l.png` (log‑log plot with fit line),  
  - `scaling_fit.txt` (exponent, CI, p‑value),  
  - `bootstrap_summary.txt` (resample count, SE, p‑value).  
- **FR-008**: System MUST enforce a total wall‑clock runtime ≤ 6 hours on a GitHub‑Actions CPU‑only runner; if exceeded, the job aborts with an informative error log.  
- **FR-009**: System MUST validate input ranges before execution and abort with a clear error message if any parameter is out of bounds (e.g., \(\delta>1\) or \(L<20\)).  

### Key Entities *(include if feature involves data)*

- **ParameterSet**: Represents a single combination of \(L\), \(\delta\), \(N_{\text{real}}\), and seed.  
- **DisorderRealization**: Contains the random coupling list \(\{J_i\}\) and the corresponding ground‑state MPS.  
- **EntropyRecord**: Stores \(l\), entropy \(S(l)\), and realization identifier.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a disorder‑free chain (\(\delta=0\)), the fitted exponent \(\alpha\) must lie within \([0.30,\,0.36]\) (i.e., within ± 10 % of the theoretical \((c_{\text{eff}}/3)\approx0.33\)) with a [deferred] CI width ≤ 0.05.
- **SC-002**: For a strongly disordered chain (\(\delta\ge0.3\)), the fitted exponent \(\alpha\) must be ≤ 0.10 (area‑law) with a [deferred] CI width ≤ 0.03 and a p‑value ≤ 0.05 indicating statistical significance.
- **SC-003**: All required artefacts (`entropy_data.csv`, `entropy_vs_l.png`, `scaling_fit.txt`, `bootstrap_summary.txt`) must be present and parsable at the end of every successful run.  
- **SC-004**: The complete workflow (including TEBD, entropy calculation, regression, and bootstrap) must finish within 6 hours on the designated GitHub‑Actions runner for the default configuration ( \(L=30\), \(\delta=0.2\), 100 realizations).  

## Assumptions

- Users have a stable internet connection to clone the TeNPy repository and install its dependencies via `pip`.  
- The GitHub‑Actions runner provides at least 2 vCPUs and 7 GB RAM (the typical `ubuntu‑latest` environment).  
- Python 3.9 or newer is available in the runner environment.  
- The XXZ model’s anisotropy parameter is fixed at the isotropic point (\(\Delta=1\)) unless explicitly overridden (not part of the MVP).  
- Bootstrap resampling uses the standard non‑parametric percentile method.  
- The disorder distribution is strictly uniform; alternative distributions are out of scope for this version.
