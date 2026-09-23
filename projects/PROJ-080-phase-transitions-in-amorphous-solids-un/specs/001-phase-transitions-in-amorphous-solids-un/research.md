# Research: Phase Transitions in Amorphous Solids Under Shear Stress

## Technical Context & Rationale

### Computational Methodology
The core challenge is computing the non-affine displacement $D^2_{min}$, which requires tracking particle neighborhoods over time.
- **Method**: Falk-Langer algorithm implementation.
- **Constraint**: Must run on CPU (GitHub Actions).
- **Rationale**: The algorithm is $O(N \log N)$ with a neighbor list. For $N \le [deferred]$, this is tractable on 2 CPU cores if implemented efficiently in NumPy/Cython. We avoid GPU offloading as the dataset size and algorithm complexity do not require CUDA acceleration, and the "GPU escape hatch" is reserved for models that cannot run on CPU (e.g., large transformer inference).
- **Dataset Fit**: The plan relies on the `amorphous-silicon-shear-trajectories` dataset. If the verified source lacks specific variables (e.g., per-particle coordinates), the plan will flag a fatal mismatch.

### Statistical Rigor
- **Permutation Test**: Used to compare distributions of $D^2_{min}$ between brittle and ductile groups.
 - *Rationale*: The KS-test assumes independent samples. However, shear bands are clustered within trajectories, violating independence. A Permutation Test accounts for this clustering.
 - *Deviation*: This replaces the KS-test mandated by FR-003 to ensure statistical validity.
- **Correction**: Bonferroni correction (FR-005) will be applied if multiple tests (e.g., across strain rates) are performed to control family-wise error rate.
- **Power Analysis**: The plan explicitly checks $n \ge 30$ per group (US-2) at the **trajectory level**. If $n < 30$, the analysis halts with a "Power Limitation" warning.
- **Causal Framing**: Results will be framed as "associational" and the predictive threshold as a **heuristic** derived from the association. No causal claims are made unless the dataset represents a randomized experiment (which is rare in MD simulations of this type). Causal inference would require a controlled experimental design (varying strain rates/temperatures as independent variables), which is outside the current scope.

### Dataset Strategy

| Dataset Name | Purpose | Source (Verified URL) | Fit Verification |
|:--- |:--- |:--- |:--- |
| `amorphous-silicon-shear-trajectories` | Primary source of particle coordinates, box dimensions, and global stress for computing $D^2_{min}$ and identifying yielding. | ` | **Critical Check**: Must confirm the dataset contains `positions` (x,y,z), `box_vectors`, and `stress_tensor` at every timestep. If it only contains global averages, the plan is invalid. |
| `synthetic_md_test` (Generated) | *Unit Testing*: Synthetic MD-like data for unit tests if the verified MD dataset is unavailable. | N/A (Locally generated) | **Fallback**: Used ONLY for unit testing statistical functions if the primary MD dataset is missing. Not for primary analysis. |

**Decision**: The plan will proceed ONLY if a verified, open dataset containing per-particle MD trajectories is identified in the input block. If the only verified sources are generic statistical datasets, the project cannot execute its primary physics analysis and must be re-scoped or halted.

*Note: The `ks_pharos` datasets listed in the verified block are for generic statistical testing and do not contain molecular dynamics data. They will NOT be used for this project.*

## Constitution Check (Research Phase)

- **Principle I (Reproducibility)**: All seeds for neighbor-list construction and random sampling (if any) are documented.
- **Principle II (Verified Accuracy)**: Dataset URLs are strictly limited to the verified block. No hypothetical URLs are generated.
- **Principle VI (Trajectory Integrity)**: The research design preserves raw trajectory files and only writes derived metrics.

## Risk Assessment

1. **Data Availability**: The biggest risk is the lack of a verified, open MD dataset with per-particle coordinates. If the `amorphous-silicon-shear-trajectories` dataset is not in the verified block, the project cannot run.
2. **Memory**: Processing 100k particles with full neighbor lists can exceed 7GB RAM if not streamed. Mitigation: Use chunked processing and `h5py` streaming.
3. **Numerical Stability**: $D^2_{min}$ calculation can be sensitive to floating-point errors. Mitigation: Use double precision (`float64`) throughout.
4. **Statistical Validity**: The switch to Permutation Tests is a necessary deviation from the spec (FR-003) to handle clustered data. This is documented and justified.