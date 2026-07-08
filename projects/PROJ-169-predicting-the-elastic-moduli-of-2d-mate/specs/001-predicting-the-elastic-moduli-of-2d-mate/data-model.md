# Data Model: Predicting the Elastic Moduli of 2D Materials

## Overview

This document defines the data schemas and transformations required for the project. All data flows from raw public repositories to processed graph representations, then to model inputs/outputs.

## Entity Definitions

### 1. MaterialGraph (Core Entity)
A graph representation of a 2D crystal structure.
*   **Nodes**: Atoms in the unit cell.
*   **Edges**: Bonds between atoms (based on distance cutoff).
*   **Global Features**: Composition statistics, symmetry class.

### 2. ElasticTensor
The target variable derived from DFT.
*   **Components**: 6 independent components (Voigt notation: $C_{11}, C_{12}, C_{13}, C_{22}, C_{23}, C_{33}$).
*   **Derived Properties**: Young's Modulus ($E$), Shear Modulus ($G$), Poisson's Ratio ($\nu$).

### 3. DescriptorSet
Computed features for the GNN input.
*   **Node Features**: Element atomic number, electronegativity, coordination number, atomic radius.
*   **Edge Features**: Bond distance, bond angle (if applicable), bond type (covalent/ionic metric).
*   **Global Features**: Density, volume per atom, stoichiometry ratios.

## Data Flow & Transformations

1.  **Raw Ingestion**:
    *   Input: Unified dataset (CIFs + Elastic Tensors) from Materials Project API.
    *   Action: Download and checksum verification.
2.  **Bias Detection**:
    *   Input: Raw data.
    *   Action: Compare distributions of structural descriptors between available and hypothetical excluded entries (if applicable).
    *   Output: `bias_report.json`.
3.  **Parsing & Filtering**:
    *   Input: Raw data.
    *   Action: Parse CIF to `pymatgen.Structure`. Filter for 2D (layered) designation and complete elastic tensor.
    *   Output: `filtered_materials.csv` (ID, Formula, SpaceGroup, ElasticTensor).
4.  **Graph Construction**:
    *   Input: `filtered_materials.csv`.
    *   Action: Convert `Structure` to `torch_geometric.data.Data`. Compute node/edge features.
    *   Output: `graphs/` directory containing `.pt` (PyTorch) files or JSON.
5.  **Splitting**:
    *   Input: Graphs.
    *   Action: Stratified split by Material Family (e.g., TMDs, MXenes) and 5-fold CV. **Exclude families with < 20 entries from inter-family test.**
    *   Output: `splits/train_idx.json`, `splits/val_idx.json`, `splits/test_idx.json`.
6.  **Model Output**:
    *   Input: Trained Model + Test Graphs.
    *   Action: Predict $E, G, \nu$.
    *   Output: `predictions.csv` (ID, True_E, Pred_E, True_G, Pred_G, True_nu, Pred_nu).

## Schemas

### Input Schema: `filtered_materials.csv`
| Column | Type | Description |
| :--- | :--- | :--- |
| `material_id` | string | Unique identifier (e.g., `mp-12345`) |
| `formula` | string | Chemical formula (e.g., `MoS2`) |
| `space_group` | int | Space group number |
| `elastic_tensor` | string | JSON string of 6-component tensor |
| `family` | string | Material family (e.g., `TMD`, `MXene`) |
| `is_2d` | boolean | Flag for 2D designation |
| `sample_count` | int | Count of entries in family (for filtering) |

### Graph Schema: `graph_data.pt` (PyTorch Geometric)
*   **`x` (Node Features)**: Tensor of shape `[N_nodes, 10]` (Element, Coord, Radius, etc.)
*   **`edge_index`**: Tensor of shape `[2, N_edges]`
*   **`edge_attr`**: Tensor of shape `[N_edges, 5]` (Distance, Angle, Type, etc.)
*   **`y` (Target)**: Tensor of shape `[3]` (Young's, Shear, Poisson's)
*   **`material_id`**: string

### Output Schema: `predictions.csv`
| Column | Type | Description |
| :--- | :--- | :--- |
| `material_id` | string | Material ID |
| `family` | string | Material Family |
| `true_young` | float | True Young's Modulus (GPa) |
| `pred_young` | float | Predicted Young's Modulus (GPa) |
| `true_shear` | float | True Shear Modulus (GPa) |
| `pred_shear` | float | Predicted Shear Modulus (GPa) |
| `true_poisson` | float | True Poisson's Ratio |
| `pred_poisson` | float | Predicted Poisson's Ratio |
| `error_young` | float | Absolute Error (Young's) |
| `mape_young` | float | MAPE (Young's) |