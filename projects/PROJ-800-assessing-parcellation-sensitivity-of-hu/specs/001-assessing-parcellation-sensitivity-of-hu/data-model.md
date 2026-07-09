# Data Model: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## 1. Entity Relationship Overview

The data model consists of three primary layers: **Raw Input**, **Processed Connectivity**, and **Analysis Results**.

1.  **Raw Input**: NIfTI files (fMRI time-series).
2.  **Processed Connectivity**: Adjacency matrices (numpy arrays) and node labels.
3.  **Analysis Results**: Centrality scores, hub sets, overlap metrics, and statistical outputs.

## 2. Data Flow & Transformation

1.  **Download**: Raw fMRI (NIfTI) $\rightarrow$ `data/raw/`
2.  **Masking**: Raw fMRI + Atlas $\rightarrow$ Time-series (N x T)
3.  **Correlation**: Time-series $\rightarrow$ Adjacency Matrix (N x N) $\rightarrow$ `data/processed/matrices/`
4.  **Centrality**: Adjacency Matrix $\rightarrow$ Centrality Scores (N x 1) $\rightarrow$ `data/processed/centrality/`
5.  **Hub Definition**: Centrality Scores $\rightarrow$ Hub Set (Boolean mask or list of IDs)
6.  **Overlap**: Hub Set A + Hub Set B $\rightarrow$ Jaccard/Dice $\rightarrow$ `data/results/stats.csv`
7.  **Normalization**: Calculate Expected Jaccard for random sets of sizes |A|, |B| $\rightarrow$ `data/results/stats.csv`
8.  **Permutation**: Hub Sets + Null Model $\rightarrow$ P-value $\rightarrow$ `data/results/stats.csv`

## 3. Schema Definitions

### Adjacency Matrix (Intermediate)
*   **Format**: `.npz` (compressed numpy) or `.csv`
*   **Content**: Symmetric matrix of correlation coefficients.
*   **Metadata**: Subject ID, Atlas Name, Resolution (N).

### Centrality Output (Intermediate)
*   **Format**: `.csv`
*   **Columns**: `subject_id`, `node_id`, `atlas`, `resolution`, `degree_centrality`, `betweenness_centrality`, `hub_status` (0/1).

### Analysis Results (Final)
*   **Format**: `.csv` (aggregated) and `.json` (permutation details)
*   **Columns**: `resolution_pair`, `metric_type`, `observed_jaccard`, `observed_dice`, `expected_jaccard`, `excess_overlap`, `p_value`, `n_permutations`, `correction_applied`.

## 4. File Naming Conventions

*   **Raw**: `raw/{subject_id}_func.nii.gz`
*   **Matrices**: `processed/{subject_id}_{atlas}_{resolution}_adj.npz`
*   **Centrality**: `processed/{subject_id}_{atlas}_{resolution}_centrality.csv`
*   **Results**: `results/{analysis_type}_{timestamp}.csv`