# Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

## Research Context

This project investigates whether explicit spatial organization of episodic memories within a transformer architecture enhances recall accuracy compared to standard attention mechanisms. By mapping latent representations to a 2D grid (a "Memory Palace"), we aim to reduce interference between similar episodic traces and improve retrieval precision.

## Structural Metrics

To validate the efficacy of the spatial organization hypothesis, we employ three quantitative structural metrics. These metrics move beyond simple accuracy scores to analyze the internal geometry and stability of the learned memory representations.

### 1. Interference Distance

**Methodology**
The interference distance metric quantifies the "spatial separation" between memory slots used to store semantically similar but distinct episodic chunks. In a non-spatial baseline, similar items may collapse into overlapping latent regions, causing interference (catastrophic forgetting or hallucination). In the spatial variant, the coordinate assignment logic (implemented in `code/models/coordinate_assignment.py`) attempts to maximize the Euclidean distance between these slots.

**Calculation**
For a given set of retrieved chunks, we compute the average pairwise Euclidean distance between their assigned 2D coordinates $(x, y)$.
$$ D_{interference} = \frac{1}{N(N-1)} \sum_{i \neq j} || \vec{c}_i - \vec{c}_j ||_2 $$
Where $\vec{c}_i$ is the coordinate of the $i$-th retrieved chunk.

**Implementation**
- **Code**: `code/evaluation/metrics.py` (`compute_interference_distance`)
- **Output**: `artifacts/results/interference_distance.json`
- **Interpretation**: A higher interference distance in the spatial variant compared to the baseline suggests successful segregation of memories, correlating with reduced interference during recall.

### 2. Slot Occupancy Distribution

**Methodology**
This metric tracks how evenly the memory grid is utilized over the course of training. A healthy "Memory Palace" should distribute information across the available grid space rather than clustering heavily in a few "rooms." This addresses the biological concern of synaptic saturation and ensures the model is utilizing its full capacity.

**Calculation**
We maintain a histogram of slot usage counts per epoch. The distribution is logged as the number of unique memory slots activated divided by the total grid size, alongside the entropy of the occupancy distribution.

**Implementation**
- **Code**: `code/evaluation/metrics.py` (`log_slot_occupancy_distribution`)
- **Output**: `artifacts/results/slot_occupancy_epoch_{epoch}.csv`
- **Columns**: `epoch`, `total_slots`, `active_slots`, `occupancy_ratio`, `entropy`
- **Interpretation**: An increasing occupancy ratio and stable entropy indicate effective exploration of the memory space.

### 3. Coordinate Variance Tracking

**Methodology**
Coordinate variance measures the stability of the spatial mapping over time. If the model's assigned coordinates for similar inputs fluctuate wildly between epochs, the spatial structure is unstable, hindering reliable recall. This metric validates the "consolidation" phase of memory formation.

**Calculation**
For each epoch, we calculate the variance of the x and y coordinates across the entire set of stored episodic chunks.
$$ Var(C) = \frac{1}{N} \sum_{i=1}^{N} (c_i - \mu_c)^2 $$
We track the variance of the distribution of assigned coordinates to ensure it remains within a bounded, predictable range relative to the grid dimensions.

**Implementation**
- **Code**: `code/evaluation/metrics.py` (`log_coordinate_variance`)
- **Output**: `artifacts/results/coordinate_variance_epoch_{epoch}.csv`
- **Columns**: `epoch`, `variance_x`, `variance_y`, `total_variance`
- **Interpretation**: Low variance in later epochs suggests that the spatial mapping has stabilized, a prerequisite for long-term episodic recall.

## Integration with Training Pipeline

These metrics are computed automatically during the evaluation phase of the training loop (`code/training/loop.py`). The `code/main.py` entry point orchestrates the logging of these metrics to the `artifacts/results/` directory, ensuring that every training run produces a complete structural analysis alongside its accuracy scores.

The results are subsequently aggregated in `artifacts/results/interference_metrics.json` and `artifacts/results/statistical_summary.json` to provide a holistic view of the spatial reasoning capabilities of the model.