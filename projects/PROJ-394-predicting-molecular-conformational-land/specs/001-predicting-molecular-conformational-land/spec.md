# Feature Specification: Predicting Molecular Conformational Landscapes with Variational Autoencoders

**Feature Branch**: `001-predict-conformer-vae`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: “What is the relationship between 2D molecular topology and low‑energy conformational landscapes in small organic molecules? Specifically, to what extent can 2D structural features predict the relative energies and ranking of conformers without explicit 3D geometry optimization.”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Train a graph‑based VAE on 2D molecular graphs (Priority: P1)

A researcher wants to train a Variational Autoencoder that consumes only 2‑D graph representations (derived from SMILES) so that the model learns a latent space encoding structural information.

**Why this priority**: This is the core capability that makes the downstream prediction possible; without a trained VAE there is no latent representation to test.

**Independent Test**: Run the training pipeline on a curated subset of the ZINC15 dataset and verify that the loss converges and a saved checkpoint is produced.

**Acceptance Scenarios**:

1. **Given** a CSV file containing SMILES strings for ≥ 5 000 molecules, **when** the training script is executed on a CPU‑only runner, **then** a model checkpoint (`vae_checkpoint.pt`) is saved and the final reconstruction loss ≤ 0.15.
2. **Given** the same training data, **when** the encoder part of the checkpoint is used to embed a held‑out SMILES, **then** a latent vector of length 64 is returned without error.

---

### User Story 2 – Predict conformer‑energy rankings from latent vectors (Priority: P1)

A chemist supplies a novel SMILES string and wants to obtain a predicted ranking of its low‑energy conformers, compared against reference energies derived from rigorous semi-empirical geometry optimization (See FR-004).

**Why this priority**: This directly tests the scientific hypothesis that 2‑D topology contains information about the conformational energy landscape.

**Independent Test**: For a test molecule, generate an initial conformer ensemble, perform multi-start geometry optimization using GFN2-xTB to find low-energy minima, obtain the VAE latent vector, rank conformers by the latent‑derived score (reconstruction loss + linear head), and compute Spearman ρ.

**Acceptance Scenarios**:

1. **Given** a SMILES string for a molecule with ≥ 3 rotatable bonds, **when** the pipeline runs end‑to‑end, **then** it outputs a Spearman rank correlation (ρ) between predicted and reference rankings.
2. **Given** the same molecule, **when** ρ is computed, **then** the pipeline also reports a Bonferroni‑adjusted p‑value indicating statistical significance.

---

### User Story 3 – Benchmark against baseline models and perform ablations (Priority: P2)

A data scientist wants to know whether the VAE adds value beyond simple fingerprint‑based predictors and whether adding 3‑D descriptors improves performance.

**Why this priority**: Benchmarks and ablations are required to interpret any observed correlation and to bound the information content of 2‑D graphs.

**Independent Test**: Run three parallel experiments on the same test set: (a) VAE latent‑based ranking, (b) ECFP4 fingerprint regression, (c) random latent vectors. Then run an ablation where 3‑D descriptors are concatenated to the latent vector.

**Acceptance Scenarios**:

1. **Given** the test set, **when** each model is evaluated, **then** a table of Spearman ρ values is produced for VAE, fingerprint, random, and VAE+3D.
2. **Given** the VAE+3D results, **when** the difference between VAE and VAE+3D ρ is computed, **then** the pipeline reports whether the improvement is statistically significant after correction.

---

### Edge Cases

- **Boundary condition**: What happens when a molecule has zero rotatable bonds (i.e., a rigid structure)?
- **Error scenario**: How does the system handle a failure of the semi‑empirical energy calculation (e.g., xtb does not converge)?
- **Data scarcity**: What if the supplied dataset contains fewer than 1 000 molecules?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest a CSV file of SMILES strings and generate corresponding 2‑D molecular graphs using RDKit. (See US-1)  
- **FR-002**: System MUST train a graph‑based Variational Autoencoder (MPNN encoder, decoder) on the 2‑D graphs on a CPU‑only environment, producing a checkpoint file. (See US-1)  
- **FR-003**: System MUST encode any supplied SMILES into a 64‑dimensional latent vector using the trained encoder. (See US-2)  
- **FR-004**: System MUST generate an initial conformer ensemble (up to 20 per molecule) via RDKit ETKDG, then perform a multi-start geometry optimization using GFN2-xTB to identify low-energy minima and compute their reference energies. (See US-2)  
  *Clarification*: The system uses GFN-xTB (a semi-empirical tight-binding method) as the reference standard because DFT is computationally infeasible for the required scale on the specified hardware. GFN-xTB is a community-standard method for conformational landscapes (Bannwarth et al.,) and provides a rigorous, physics-based ground truth distinct from the heuristic ETKDG generator.
- **FR-005**: System MUST compute Spearman rank correlation (ρ) between the latent‑derived ranking (predicted by a linear head on the VAE latent vector) and the reference energy ranking for each test molecule. (See US-2)  
- **FR-006**: System MUST evaluate baseline predictors: (a) ECFP4 fingerprint regression, (b) random latent vectors, and report their ρ values. (See US-3)  
- **FR-007**: System MUST perform an ablation where optional 3‑D descriptors (e.g., moment of inertia, radius of gyration) are concatenated to the latent vector and report the resulting ρ. (See US-3)  
- **FR-008**: System MUST apply a Bonferroni correction across all hypothesis tests performed on the test set. (See US-2)  
- **FR-009**: System MUST report all findings as associative (correlation) and explicitly state that no causal inference is claimed. (See US-2)  
- **FR-010**: System MUST conduct a sensitivity analysis sweeping the significance threshold α over {0.01, 0.05, 0.10} and report how the adjusted p‑values and ρ values change. (See US-2)  
- **FR-011**: System MUST validate that the on-the-fly conformer generation and energy computation workflow (FR-004) completes successfully for ≥ 95% of the input molecules. (See US-1)  
- **FR-012**: System MUST perform a power analysis to determine the minimum sample size required to detect a Spearman ρ of 0.5 with ≥ 80% power at α = 0.05, and output a report containing the calculated minimum sample size. (See US-2)  
  *Clarification*: Based on standard power analysis for rank correlation (Cohen, 1988; Faul et al., 2009), the expected minimum sample size is n ≥ 128. The test set target in SC-001 (n ≥ 1000) is set significantly higher than this minimum to ensure robustness and generalization.

### Key Entities

- **Molecule**: Represents a chemical entity identified by a SMILES string; key attributes are `smiles`, `graph (RDKit)`, `latent_vector`, `conformer_set`.  
- **Conformer**: 3‑D geometry generated by ETKDG and optimized by GFN2-xTB; key attributes are `geometry`, `xtb_energy`.  
- **ModelCheckpoint**: Serialized VAE weights (`vae_checkpoint.pt`).  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the held‑out test set (≥ 1 000 molecules, which exceeds the minimum n=128 determined by FR-012), the VAE‑based ranking achieves Spearman ρ ≥ 0.5 (moderate‑to‑strong correlation) with Bonferroni‑adjusted p < 0.05. (See US-2)  
- **SC-002**: Baseline ECFP4 fingerprint regression attains ρ ≤ 0.3, demonstrating that the VAE provides a statistically superior signal. (See US-3)  
- **SC-003**: The sensitivity analysis shows that varying the α threshold across {0.01, 0.05, 0.10} changes the adjusted p‑values by no more than ±0.02 and does not alter the qualitative conclusion (ρ ≥ 0.5). (See FR-010)  
- **SC-004**: The ablation with added 3‑D descriptors yields a Δρ ≤ 0.1 relative to the pure‑VAE model, indicating limited extra information from explicit 3‑D features. (See US-3)  
- **SC-005**: All pipelines complete within 6 hours on a GitHub Actions free‑tier runner (2 CPU cores, ≈ 7 GB RAM) for a public repository. (See Assumptions)

## Assumptions

- Pre-computed DFT or semi-empirical conformer energies are NOT available for the target ZINC15 subset; the system MUST compute reference energies on-the-fly using GFN2-xTB (CPU-compatible).
- The VAE architecture (MPNN encoder, decoder) with 64‑dim latent space fits comfortably in ≤ 2 GB RAM for ≤ 10 k molecules.
- GFN2-xTB calculations converge for > 95 % of generated conformers; failures are logged and those conformers are excluded.
- No GPU or CUDA libraries are available; all code must run on CPU using PyTorch ≥ 2.0 with `torch.set_num_threads(2)`.
- The statistical power analysis will be performed using the `statsmodels` package; the result (n ≥ 128) is a minimum, while the test set target is n ≥ 1000.
- All external tools (RDKit, xtb, PyTorch, scikit-learn) are installable from PyPI/conda and are compatible with the GitHub Actions Ubuntu-latest runner.
- The repository hosting the workflow is public, ensuring the 6-hour execution time limit on the free tier.

---