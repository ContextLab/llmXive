# Data Model: llmXive follow-up: extending "OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers"

## Overview

This document defines the data structures used for spectral feature extraction, labeling, and correlation analysis. All data is stored in `data/processed/` as JSON/CSV files with checksums.

## Entities

### 1. SpectralFeatureVector

A structured record representing the spectral signature of a model's initial gradient covariance.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `model_id` | `string` | Unique identifier for the architecture (e.g., "ResNet-18-TinyImageNet"). | Required, Unique |
| `dataset` | `string` | Name of the proxy dataset used (e.g., "TinyImageNet"). | Required |
| `step_count` | `integer` | Number of training steps used for gradient aggregation. | Must be 100 |
| `probe_optimizer` | `string` | Optimizer used for feature extraction (e.g., "SGD", "Adam"). | Required, Default "SGD" |
| `spectral_radius` | `float` | Largest eigenvalue ($\lambda_{max}$). | > 0, No NaN |
| `condition_number` | `float` | Ratio $\lambda_{max} / (\lambda_{min} + \epsilon)$. | > 1, No NaN |
| `spectral_entropy` | `float` | Entropy of the normalized top-$k$ eigenvalues. | >= 0, No NaN |
| `num_eigenvalues` | `integer` | Number of eigenvalues used for entropy calculation. | Minimum 10, Target 50 |
| `extraction_time_sec` | `float` | Time taken to extract features. | > 0 |

### 2. OptimalMechanismLabel

The ground truth label mapping a model/task to the best optimizer.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `model_id` | `string` | Reference to `SpectralFeatureVector.model_id`. | Required, Foreign Key |
| `ground_truth_optimizer` | `string` | The optimizer used to generate the ground truth label (e.g., "Adam", "SGD"). | Required, Enum |
| `optimizer_family` | `string` | The best optimizer (e.g., "Adam", "SGD", "Lion"). | Required, Enum |
| `validation_loss` | `float` | Final validation loss from OmniOpt. | > 0 |
| `source` | `string` | Source of the label (e.g., "OmniOpt_Paper_Table_3", "Re-run"). | Required |

### 3. LabeledDataset

The merged dataset used for correlation analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `row_id` | `integer` | Auto-incremented index. |
| `features` | `object` | Embedded `SpectralFeatureVector` (minus `model_id`). |
| `label` | `string` | `OptimalMechanismLabel.optimizer_family`. |
| `ground_truth_optimizer` | `string` | `OptimalMechanismLabel.ground_truth_optimizer`. |
| `split` | `string` | "train" (full dataset used for correlation). |

### 4. CorrelationResults

The output of the analysis phase.

| Field | Type | Description |
| :--- | :--- | :--- |
| `feature_name` | `string` | "condition_number", "spectral_entropy". |
| `spearman_rho` | `float` | Spearman correlation coefficient. |
| `p_value` | `float` | Approximate p-value from Monte Carlo Permutation Test. |
| `bonferroni_p_value` | `float` | Bonferroni-corrected p-value. |
| `n_samples` | `integer` | Number of samples used. |
| `significance` | `boolean` | True if `bonferroni_p_value < 0.05`. |

## File Formats

### `data/processed/spectral_features.csv`
-   Delimiter: `,`
-   Header: `model_id,dataset,step_count,probe_optimizer,spectral_radius,condition_number,spectral_entropy,num_eigenvalues,extraction_time_sec`
-   Encoding: UTF-8

### `data/processed/labeled_dataset.json`
-   Format: JSON Lines (`.jsonl`) or single JSON array.
-   Schema: `LabeledDataset` structure above.

### `data/processed/results.json`
-   Format: JSON.
-   Schema: `CorrelationResults` structure above.

## Data Flow

1.  **Input**: `TinyImageNet` (streamed) + `OmniOpt Lookup` (Primary: Paper Tables, Secondary: Re-run).
2.  **Process**: `spectral_extractor.py` generates `spectral_features.csv`.
3.  **Process**: `label_mapper.py` merges features with labels, producing `labeled_dataset.json`.
4.  **Process**: `correlation_analyzer.py` computes Spearman correlations and generates `results.json`.
5.  **Output**: `results.json` is the single source of truth for the paper.