# Research: Memory Palaces in LLMs - Spatial Reasoning for Enhanced Episodic Recall

## Overview

This document outlines the research methodology, experimental design, and structural metrics used to evaluate the efficacy of spatial memory organization in Large Language Models (LLMs). The core hypothesis is that explicitly organizing episodic memories into a 2D spatial grid (a "Memory Palace") improves recall accuracy and reduces interference compared to standard sequential attention mechanisms.

## Structural Metrics

To validate the "spatial organization" hypothesis, we move beyond simple accuracy metrics and quantify the structural properties of the memory representation. These metrics provide the quantitative "diffraction patterns" (per Rosalind Franklin's critique) necessary to distinguish true spatial organization from arbitrary embedding clustering.

### 1. Interference Distance Metric

**Methodology**:
The Interference Distance metric quantifies the semantic collision between memory chunks assigned to proximal spatial coordinates. In a standard transformer, interference is a function of sequence position and attention heads. In the Memory Palace architecture, interference is also a function of Euclidean distance in the 2D grid.

**Calculation**:
For a given set of episodic chunks $E = \{e_1, e_2,..., e_n\}$, each assigned a coordinate $C(e_i) = (x_i, y_i)$:
1. Compute the semantic similarity $S(e_i, e_j)$ using cosine similarity of their hidden state embeddings.
2. Compute the spatial distance $D(e_i, e_j) = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}$.
3. The Interference Distance $I$ for a specific memory slot is defined as the weighted sum of similarities of all other chunks within a radius $R$:
 $$ I(slot) = \sum_{j \in Neighbors(slot)} S(e_i, e_j) \cdot \frac{1}{D(e_i, e_j) + \epsilon} $$

**Expected Outcome**:
A successful spatial organization strategy should maximize the distance $D$ between semantically similar chunks (high $S$), resulting in a lower aggregate Interference Distance compared to a non-spatial baseline where coordinates are assigned randomly or sequentially.

**Implementation**:
This metric is computed in `code/evaluation/metrics.py` via `compute_interference_distance()`. Results are logged to `artifacts/results/interference_distance.json`, separating `spatial` (Memory Palace) and `baseline` (Standard Transformer) variants to measure the delta ($\Delta$).

### 2. Slot Occupancy Logging

**Methodology**:
To monitor the stability and utilization of the memory grid over time, we track the occupancy of each slot in the 2D grid. This addresses concerns regarding "static retrieval indices" (per Eric Kandel) by observing how the grid evolves during training and under interference.

**Calculation**:
For each training epoch $t$:
1. Iterate through all active episodic chunks.
2. Count the number of chunks assigned to each grid cell $(x, y)$.
3. Record the distribution as a histogram or density map.

**Significance**:
- **Uniformity**: A well-organized memory palace should exhibit a relatively uniform distribution, avoiding "hotspots" where the coordinate assignment logic fails to spread memories.
- **Drift**: Changes in occupancy distribution over epochs indicate the model's ability to reorganize memories (consolidation) or the presence of catastrophic interference.

**Implementation**:
The `log_slot_occupancy_distribution()` function in `code/evaluation/metrics.py` records this data per epoch. Outputs are saved to `artifacts/results/slot_occupancy_epoch_{epoch}.csv`.

### 3. Coordinate Variance Tracking

**Methodology**:
Coordinate Variance measures the "spread" of the memory assignments in the latent space. If the coordinate assignment logic collapses memories into a single region (e.g., the origin), the spatial reasoning capability is lost.

**Calculation**:
For a given epoch, let $X$ and $Y$ be the sets of x and y coordinates for all active chunks.
1. Calculate the variance: $Var(X) = \frac{1}{N}\sum (x_i - \mu_x)^2$ and $Var(Y) = \frac{1}{N}\sum (y_i - \mu_y)^2$.
2. The total Coordinate Variance is $V = Var(X) + Var(Y)$.

**Significance**:
- **High Variance**: Indicates the model is effectively utilizing the full spatial extent of the "palace," maximizing the potential for separation.
- **Low Variance**: Suggests clustering or failure of the coordinate assignment heuristic (e.g., `code/models/coordinate_assigner.py`), potentially leading to high interference.

**Implementation**:
The `log_coordinate_variance()` function in `code/evaluation/metrics.py` tracks this metric per epoch. Results are written to `artifacts/results/coordinate_variance_epoch_{epoch}.csv`.

## Integration with Statistical Analysis

These structural metrics are not merely descriptive; they are inputs to the statistical validation framework (User Story 2).
- The **Interference Distance** is the primary dependent variable for paired t-tests comparing the Spatial vs. Baseline models.
- **Slot Occupancy** and **Coordinate Variance** serve as control variables to ensure that observed improvements in recall are due to the spatial mechanism itself, not artifacts of uneven data distribution or grid collapse.

## Conclusion

By rigorously defining and tracking Interference Distance, Slot Occupancy, and Coordinate Variance, this research moves beyond qualitative assertions of "spatial reasoning." These metrics provide the necessary quantitative evidence to validate whether the Memory Palace architecture genuinely enhances episodic recall through structural organization, addressing the critical feedback regarding measurable correlates and formal mappings.