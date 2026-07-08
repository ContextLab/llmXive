# Data Model: Molecular Complexity and Physicochemical Properties

## Overview

This document defines the data structures, schemas, and information-theoretic definitions used throughout the `PROJ-431-predicting-molecular-complexity-with-inf` pipeline. It serves as the contract between data ingestion, feature engineering, modeling, and visualization components.

## Core Entities

### Molecule Record

The fundamental unit of analysis is a molecule, represented primarily by its SMILES string and associated physicochemical properties.

| Field | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `smiles` | string | Canonical SMILES representation of the molecular graph. | Input Dataset |
| `logS` | float | Aqueous solubility (log of molar solubility). Negative values indicate lower solubility. | Input Dataset |
| `logP` | float | Octanol-water partition coefficient (lipophilicity). Positive values indicate higher lipophilicity. | Input Dataset |

## Information-Theoretic Metrics

This project utilizes **Shannon Entropy** computed over topological distributions within the molecular graph as a proxy for structural complexity.

### Definition of "Entropy" in this Context

Per the project's foundational research (FR-002, FR-003) and reviewer clarification (john-von-neumann-simulated), the term "entropy" in this pipeline **strictly refers to Shannon Entropy of degree distributions**. It is a measure of the uncertainty in the connectivity pattern of atoms or bonds within the molecular graph.

It is **not** a measure of:
- Thermodynamic entropy (physical state).
- Mutual information between disparate variables (unless explicitly calculated as a secondary metric).
- Algorithmic complexity (Kolmogorov complexity).

The metric quantifies the "structural information" content by analyzing the heterogeneity of local connectivity.

#### 1. Atom Entropy ($H_{atom}$)

Calculated based on the distribution of **atom degrees** (number of bonded neighbors) within the molecule.

- **Distribution**: Let $D$ be the set of degrees for all atoms in the molecule $M$. The probability $p_i$ of an atom having degree $i$ is:
 $$p_i = \frac{\text{count of atoms with degree } i}{\text{total number of atoms in } M}$$
- **Entropy Calculation**:
 $$H_{atom}(M) = - \sum_{i} p_i \log_2(p_i)$$
- **Interpretation**: Higher $H_{atom}$ indicates a more diverse mix of connectivity patterns (e.g., a mix of chain, branch, and ring atoms), suggesting higher topological complexity.

#### 2. Bond Entropy ($H_{bond}$)

Calculated based on the distribution of **bond degrees** (sum of the degrees of the two atoms connected by the bond) or bond types (single, double, triple, aromatic). In this implementation, we use the **bond degree** (sum of atom degrees) to capture the connectivity load of the bond.

- **Distribution**: Let $B$ be the set of bond degrees for all bonds in $M$. The probability $q_j$ of a bond having degree $j$ is:
 $$q_j = \frac{\text{count of bonds with degree } j}{\text{total number of bonds in } M}$$
- **Entropy Calculation**:
 $$H_{bond}(M) = - \sum_{j} q_j \log_2(q_j)$$
- **Interpretation**: Higher $H_{bond}$ reflects a more heterogeneous distribution of connectivity loads across the molecular skeleton.

### Data Schema for Enriched Datasets

When the `compute_entropy` pipeline stage completes, the output CSV includes the following new columns derived from the definitions above:

| Column Name | Type | Description |
|:--- |:--- |:--- |
| `atom_entropy` | float | The Shannon entropy of the atom degree distribution. |
| `bond_entropy` | float | The Shannon entropy of the bond degree distribution. |

## Data Flow

1. **Raw Input**: CSV with `smiles`, `logS`, `logP`.
2. **Validation**: `verify_dataset_columns` ensures required fields exist.
3. **Feature Engineering**: `compute_atom_entropy` and `compute_bond_entropy` are applied per row.
4. **Intermediate Output**: CSV enriched with `atom_entropy` and `bond_entropy`.
5. **Modeling**: Ridge Regression models use these entropy columns to predict `logS` and `logP`.

## References

- **FR-002**: Implement atom entropy calculation based on degree distribution.
- **FR-003**: Implement bond entropy calculation based on degree distribution.
- **Review**: john-von-neumann-simulated (2026-06-13): Clarified distinction between structural and functional information; mandated explicit definition of entropy as Shannon entropy of degree distributions.