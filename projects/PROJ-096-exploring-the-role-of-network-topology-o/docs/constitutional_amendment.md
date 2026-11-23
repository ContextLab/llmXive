# Constitutional Amendment Log: Base Graph Source Correction

**Date**: 2026-06-25
**Project**: PROJ-096-exploring-the-role-of-network-topology-o
**Amendment ID**: CA-001
**Status**: Active

## 1. Original Spec ID
**FR-001**: "The base graph MUST be reconstructed as a regular ring lattice of the ca-AstroPh dataset."

## 2. Methodological Flaw
The original specification (FR-001) mandated the use of the "ca-AstroPh" (Astrophysics Citation) dataset from the Stanford Network Analysis Project (SNAP) as the source for the base graph. The requirement was to "reconstruct" this irregular citation network into a regular ring lattice to serve as the starting point for the Watts-Strogatz small-world model.

This approach contains a fundamental methodological incoherence:
1. **Structural Incompatibility**: The ca-AstroPh dataset is an irregular, scale-free citation network with a highly heterogeneous degree distribution. It does not possess the uniform degree ($k$) or the local clustering properties of a regular ring lattice.
2. **Loss of Parameter Meaning**: The Watts-Strogatz model relies on a well-defined "rewiring probability" ($p$) applied to a regular ring lattice. If the base graph is an arbitrary irregular network, the concept of "rewiring" becomes ill-defined, and the parameter $p$ no longer represents a controlled perturbation of a regular topology. This invalidates the experimental variable.
3. **Reproducibility Violation**: Attempting to "reconstruct" an irregular graph into a specific regular topology introduces arbitrary choices (e.g., which edges to drop, how to add new ones) that are not uniquely determined by the data, violating the principle of reproducible research.

## 3. New Approach
The base graph for this study is now defined as a **synthetic regular ring lattice** with the following parameters:
- **Node Count ($N$)**: 500
- **Degree ($k$)**: 2 (each node connected to its 2 nearest neighbors in the ring)
- **Generation Method**: Deterministic generation using the standard Watts-Strogatz algorithm with rewiring probability $p=0.0$.
- **Random Seed**: A documented, fixed seed is used for the lattice generation to ensure reproducibility, although the lattice structure itself is deterministic for $p=0.0$.

This synthetic base ensures that the "small-world" parameter $p$ (ranging from 0.0 to 1.0) has a precise, theoretically valid meaning: the probability of rewiring an edge in a perfect regular ring.

## 4. Rationale
1. **Theoretical Validity**: The Watts-Strogatz model was explicitly designed to interpolate between a regular ring lattice and a random graph. Starting from a true regular ring lattice preserves the integrity of the model's parameters.
2. **Controlled Experiment**: By generating the base graph synthetically, we eliminate the confounding variables present in real-world citation networks (e.g., temporal evolution, citation bias, subject-specific clustering) that are irrelevant to the study of topology's role in synchronization.
3. **Alignment with Research Question**: The research question asks about the impact of *network topology* on synchronization. Using a synthetic lattice allows us to isolate the topological variable (rewiring probability) without the noise of an uncontrolled, irregular base structure.

## 5. Constitution Impact
This amendment resolves the conflict with **Constitution Principle I (Single Source of Truth)** and **Constitution Principle VI (Reproducibility)**:
- **T000**: The `spec.md` has been updated to replace the ca-AstroPh requirement with the synthetic ring lattice requirement.
- **T000a**: The `constitution.md` has been amended to remove the download requirement for ca-AstroPh and replace it with the generation requirement for the synthetic lattice.
- **T012**: The implementation code (`code/generate_topology.py`) now generates the synthetic lattice, explicitly noting this deviation from the original FR-001.

This document serves as the updated single source of truth for the data source methodology. Any future analysis or simulation in this project must assume a synthetic regular ring lattice ($N=500, k=2$) as the base topology.

## 6. Verification
The validity of this amendment is verified by:
- The presence of this document in `docs/constitutional_amendment.md`.
- The successful generation of a connected graph with $N=500$ and average degree $k=2$ by `code/generate_topology.py`.
- The absence of any code attempting to download or process the ca-AstroPh dataset.