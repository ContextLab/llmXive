# Constitution

## Principles

### Principle I: Scientific Integrity
The system shall prioritize scientific accuracy over computational convenience. All results must be reproducible and validated against known physical laws.

### Principle II: Transparency
All methods, parameters, and assumptions must be explicitly documented. No "black box" operations are permitted without full disclosure of underlying mechanisms.

### Principle III: Data Hygiene
All generated data must be traceable to its source parameters. Every data point must include metadata documenting the generation process, including seeds, parameters, and validation status.

### Principle IV: Validation First
No model or analysis shall be considered valid without explicit verification against ground truth or established benchmarks.

### Principle V: Error Disclosure
All limitations, failure modes, and uncertainty bounds must be explicitly reported. The system shall not hide or downplay errors or edge cases.

### Principle VI: Numerical Homogenization Method
The system shall use FFT-based numerical homogenization. The validity range of the analytical bounds used is documented for the specific microstructure topology.
Specifically:
- The FFT solver is valid for periodic microstructures on a regular grid.
- Analytical Voigt-Reuss-Hill bounds are valid for isotropic effective properties.
- For anisotropic topologies, the bounds are documented per topology type in the metadata.
- Solver convergence is required: residual must be < 1e-4.

### Principle VII: Generalization Boundary
The system shall explicitly identify and report out-of-distribution (OOD) predictions. No extrapolation beyond the training domain shall be presented as valid without explicit OOD flags and degradation rate reporting.

### Principle VIII: Computational Efficiency
The system shall prioritize CPU-optimized algorithms where possible, with GPU acceleration only when explicitly justified by performance requirements and validated for numerical equivalence.

### Principle IX: Reproducibility
All experiments must be fully reproducible. Random seeds, software versions, and hardware configurations must be recorded and preserved.

### Principle X: Ethical Use
The system shall not be used for purposes that violate scientific ethics or that could cause harm if misapplied. All findings must be contextualized within their limitations.