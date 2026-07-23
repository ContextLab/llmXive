# Data Model Specification: llmXive Follow-up (Extending Intern-Atlas)

**Project**: PROJ-815-llmxive-follow-up-extending-intern-atlas
**Version**: 1.0.0
**Date**: 2023-10-27
**Status**: Draft

## Overview

This document defines the core data structures used to represent the scientific method evolution graph, retraction metadata, and computed topological features. These schemas ensure consistency across the extraction, feature engineering, and modeling phases of the pipeline.

## Core Entities

### 1. MethodNode

Represents a scientific method, technique, or algorithm as a node in the Intern-Atlas graph.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `node_id` | `str` | Unique identifier for the node (e.g., internal graph ID). | Required, Unique |
| `method_name` | `str` | Human-readable name of the method. | Required |
| `doi` | `str` | Digital Object Identifier of the primary publication. | Optional, Unique |
| `publication_year` | `int` | Year of publication. | Required, Range: 2010-2018 (for this study) |
| `field_of_study` | `str` | Broad academic field (e.g., "Machine Learning", "Genomics"). | Required |
| `publication_venue` | `str` | Name of the journal or conference. | Required |
| `citation_count` | `int` | Total number of citations at the time of data extraction. | Non-negative |
| `is_llm_inferred` | `bool` | Flag indicating if edge types connected to this node were inferred by an LLM. | Required (Default: False) |

### 2. RetractionLabel

Represents the ground truth status of a method node based on retraction databases.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `node_id` | `str` | Foreign key referencing `MethodNode.node_id`. | Required, Unique |
| `retraction_status` | `int` | Categorical label for retraction status. | Enum: 0 (Robust), 1 (Fragile), 2 (Retraction-Only) |
| `retraction_reason` | `str` | Textual reason for retraction (if applicable). | Optional |
| `retraction_date` | `str` | ISO 8601 date string of the retraction notice. | Optional |
| `journal` | `str` | Journal where the retraction was published. | Optional |
| `match_type` | `str` | Method used to link the node to the retraction record. | Enum: "exact_doi", "fuzzy_title", "fuzzy_author" |
| `match_confidence` | `float` | Confidence score for fuzzy matches (0.0-1.0). | Optional, Range: 0.85-1.0 for fuzzy |

**Label Definitions**:
- `0`: **Robust** - No retraction found; method is considered stable.
- `1`: **Fragile** - Retraction due to methodological errors, irreproducibility, or honest mistakes.
- `2`: **Retraction-Only** - Retraction due to fraud, misconduct, or data fabrication.

### 3. TopologicalFeatures

Computed features derived from the graph structure of the Intern-Atlas dataset.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `node_id` | `str` | Foreign key referencing `MethodNode.node_id`. | Required, Unique |
| `bottleneck_resolution_ratio` | `float` | Ratio of "improves"/"replaces" edges to total outgoing edges. | Range: 0.0-1.0 |
| `branching_entropy` | `float` | Shannon entropy of the distribution of downstream method types. | Range: 0.0-∞ |
| `total_out_degree` | `int` | Total number of outgoing edges. | Non-negative |
| `improves_count` | `int` | Count of outgoing edges labeled "improves". | Non-negative |
| `replaces_count` | `int` | Count of outgoing edges labeled "replaces". | Non-negative |
| `extends_count` | `int` | Count of outgoing edges labeled "extends". | Non-negative |

## Derived Data Artifacts

### Dataset: `features_2010_2018.csv`

The primary output of the data extraction pipeline (Task T017). This file merges `MethodNode`, `RetractionLabel`, and `TopologicalFeatures` into a single flat table for modeling.

| Column Name | Source Entity | Type | Notes |
|:--- |:--- |:--- |:--- |
| `node_id` | MethodNode | str | Primary Key |
| `method_name` | MethodNode | str | |
| `publication_year` | MethodNode | int | Filtered 2010-2018 |
| `field_of_study` | MethodNode | str | |
| `citation_count` | MethodNode | int | |
| `retraction_status` | RetractionLabel | int | 0, 1, or 2 |
| `retraction_reason` | RetractionLabel | str | |
| `bottleneck_resolution_ratio` | TopologicalFeatures | float | |
| `branching_entropy` | TopologicalFeatures | float | |
| `retraction_status_binary` | Derived | int | 1 if `retraction_status` == 1, else 0 |

## Validation Rules

1. **Edge Type Integrity**: Any node connected to an edge where `is_llm_inferred` is `True` must be excluded from the training dataset unless explicitly handled by the abort logic in `code/utils/graph_utils.py`.
2. **Label Consistency**: The sum of counts for `retraction_status` (0, 1, 2) must equal the total number of rows in the final dataset.
3. **Feature Bounds**: `bottleneck_resolution_ratio` must be strictly within [0, 1]. `branching_entropy` must be >= 0.
4. **Missing Data**: Nodes with missing `publication_year` or missing edge metadata must be dropped prior to feature computation.