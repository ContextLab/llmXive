# Specification: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## Problem Statement

Predict the elastic moduli (Young's, Shear, Poisson's ratio) of 2D materials using only their crystallographic structure as input.

## Approach

We utilize a Graph Neural Network (GNN) trained on DFT-calculated elastic tensors from public repositories. This is a **surrogate model** approach: it learns the mapping from structure to properties based on existing high-fidelity data, rather than solving the underlying quantum mechanical equations from scratch.

## Constraints

- **Memory**: Must run on machines with ≤7GB RAM
- **Compute**: CPU-only execution preferred for reproducibility
- **Data**: Must use a single canonical source per run to avoid bias
- **Terminology**: Must explicitly distinguish between "first-principles" (DFT) and "surrogate" (ML) methods

## Success Criteria

- Achieve MAPE < 15% on held-out test families
- Demonstrate generalization to unseen chemical families
- Identify key structural descriptors influencing elastic properties
