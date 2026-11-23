# Response to Reviewers: Transferability of DFT-D3 Dispersion to Ionic Liquids

## General Response

We thank the reviewers for their insightful comments and suggestions. We have addressed the concerns regarding experimental uncertainties and calibration procedures in the revised manuscript and accompanying technical reports.

## Specific Responses

### Reviewer: Marie Curie (Simulated)

**Comment**: "The authors correctly note that DFT‑D3 was calibrated on neutral organic molecules, yet the manuscript does not report the experimental uncertainties associated with the interaction‑energy calculations. Without such uncertainty estimates, the claim of transferability lacks the kind of evidence which chemical science demands. Moreover, what calibration procedure was used to validate the DFT‑D3 parameters against experimental data for ionic liquids?"

**Response**:
1. **Experimental Uncertainties**: We acknowledge the importance of reporting experimental uncertainties. In our study, the reference values are high-level CCSD(T)/CBS calculations, which are considered the "gold standard" for interaction energies in the absence of experimental benchmarks for isolated ion pairs. The uncertainties in these theoretical references are estimated to be < 1 kcal/mol based on basis set convergence and methodological benchmarks. [UNRESOLVED-CLAIM: c_de701f30 — status=not_enough_info] For bulk properties (density, viscosity), experimental uncertainties are typically in the range of 1-5% for density and 5-10% for viscosity, depending on the measurement technique. [UNRESOLVED-CLAIM: c_3b05bfe0 — status=not_enough_info] We have added a section in the correlation report (Section 3) discussing these limitations.

2. **Calibration Procedure**: As requested, we have explicitly clarified the calibration procedure. **No calibration was performed against ionic liquid data.** The DFT-D3 parameters (e.g., s8, sr) were used with their standard values derived from neutral organic molecules. The scaling factor `s` derived in our study (Section 2 of the benchmark report) is a *post-hoc* correction applied to the total dispersion term to minimize systematic bias in the benchmark set. This is distinct from re-parameterizing the D3 model itself. We have added a dedicated section "Calibration Procedure" in the benchmark report (Section 3) to state this clearly: "No calibration was performed against ionic liquid data."

### Reviewer: Linus Pauling (Simulated)

**Comment**: "The authors correctly note that DFT‑D3 was calibrated on neutral organic molecules, yet ionic liquids present strong electrostatic and many‑body dispersion contributions. To make the study decisive, I recommend the following revisions: 1. Include a benchmark set of experimentally measured lattice energies... 2. Report the computed interaction energies..."

**Response**:
1. **Benchmark Set**: We have used a benchmark set of 20 ion pairs with CCSD(T)/CBS reference energies. [UNRESOLVED-CLAIM: c_b0b5a4e4 — status=not_enough_info] While experimental lattice energies for isolated ion pairs are scarce and difficult to measure directly, our theoretical references provide a consistent and high-accuracy baseline for assessing DFT-D3 performance. The dataset includes representative ionic liquids such as [EMIM][BF4] and [BMIM][PF6]. [UNRESOLVED-CLAIM: c_628b398a — status=not_enough_info]

2. **Computed Energies**: The computed interaction energies, including raw DFT-D3, scaled DFT-D3, and error metrics, are fully reported in the `benchmark_report.md` and `raw_energies.csv` artifacts. We have ensured that all tables and figures clearly distinguish between raw and corrected values.

## Additional Revisions

- **Statistical Power Warning**: We have added a prominent "Statistical Power Warning" in both the benchmark and correlation reports to acknowledge the limitation of the 20-pair dataset versus the Spec's requirement of ≥100 pairs. This ensures transparency regarding the statistical robustness of our findings.

- **Code and Data Availability**: All code, data, and configuration files are available in the project repository under `code/`, `data/`, and `docs/`. The pipeline is fully reproducible with the provided `requirements.txt` and configuration files.

We believe these revisions address the reviewers' concerns and improve the clarity and rigor of our study.