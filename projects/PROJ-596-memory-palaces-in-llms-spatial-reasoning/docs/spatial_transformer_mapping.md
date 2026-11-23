# Formal Mapping: Spatial "Rooms" to Transformer Components

## Overview

This document provides the rigorous architectural mapping between the conceptual
"Memory Palace" spatial rooms and the concrete components of the transformer
architecture. It addresses the concern raised by John von Neumann regarding the
distinction between *order* (the program/logic) and *storage* (the physical
location of data), ensuring that the spatial indexing mechanism is formally
defined rather than metaphorical.

## 1. Conceptual Abstraction vs. Implementation Reality

| Conceptual "Memory Palace" Element | Transformer Component | Formal Mapping Logic |
|:--- |:--- |:--- |
| **The Palace (Global Context)** | **Model Hidden State ($H \in \mathbb{R}^{L \times d}$)** | The entire sequence of hidden states represents the total accessible memory space. |
| **A Room (Spatial Zone)** | **Attention Head Subspace ($H_{head}$)** | Specific attention heads are trained to specialize in retrieving memories from specific "spatial" regions defined by coordinate embeddings. |
| **A Room Number (Coordinate)** | **Positional Embedding + Learned Slot Vector** | A room is not a physical address but a vector sum: $E_{room} = P_{pos} + V_{slot}$. |
| **The Doorway (Access Point)** | **Query Vector ($Q$)** | The query vector acts as the "key" that unlocks the specific room by attending to the corresponding slot vector. |
| **Items on Shelves (Content)** | **Value Vectors ($V$)** | The actual information stored in the "room" is encoded in the value projections of the tokens residing in that spatial zone. |
| **Walking Path (Traversal)** | **Self-Attention Mechanism** | The attention mechanism computes the path, determining which "rooms" are relevant to the current context. |

## 2. The Addressing Function: From Coordinates to Attention Scores

The core of the "spatial reasoning" is the mapping function $f: \text{Coordinates} \to \text{Attention Weights}$.

### 2.1. Coordinate Encoding
Each episodic chunk is assigned a 2D coordinate $(x, y)$ in the memory grid (see `code/models/memory_slot.py`).
This coordinate is projected into the embedding space:
$$
E_{coord}(x, y) = \text{Linear}(\sin(\omega_x x), \cos(\omega_x x), \sin(\omega_y y), \cos(\omega_y y))
$$
This sinusoidal encoding ensures that spatial proximity in the grid corresponds to proximity in the latent vector space.

### 2.2. Soft-Addressed Retrieval
The transformer's attention mechanism computes the similarity between the current Query $Q_t$ and the Key $K_i$ of every token $i$ in the context.
In the spatial variant, the Key $K_i$ is augmented with the spatial coordinate embedding:
$$
K_i^{spatial} = K_i^{text} + E_{coord}(x_i, y_i)
$$
The attention score $\alpha_{t,i}$ becomes a function of both semantic similarity and spatial proximity:
$$
\alpha_{t,i} = \frac{\exp(Q_t \cdot K_i^{spatial} / \sqrt{d_k})}{\sum_j \exp(Q_t \cdot K_j^{spatial} / \sqrt{d_k})}
$$
**Formal Implication:** This creates a "soft" door. The model does not need to know the exact room number; it only needs to know the *direction* in the latent space that leads to the relevant room.

## 3. The Binding Problem: Address vs. Content

Per the EDVAC report distinction between *address* and *content*:

1. **Address (The Room):** Encoded in the *Positional/Coordinate* component of the Key vector ($E_{coord}$). This determines *where* the model looks.
2. **Content (The Item):** Encoded in the *Semantic* component of the Value vector ($V^{text}$). This determines *what* the model retrieves.

The spatial attention mechanism ensures that the "Address" component of the query aligns with the "Address" component of the keys in the target room, while the "Content" is passed through via the Value projection. This separation is critical for preventing interference between semantically similar but spatially distinct memories.

## 4. Structural Stability and Slot Occupancy

To ensure the "rooms" remain distinct and do not collapse into a single point (a failure mode known as "attention collapse"), the system enforces:

- **Coordinate Variance Regularization:** A loss term penalizes the reduction of variance in the assigned coordinates, ensuring the memory grid remains populated.
- **Slot Occupancy Monitoring:** The `log_slot_occupancy_distribution` function tracks the density of items per grid cell. High density in a single cell indicates a failure of spatial distribution, triggering a re-balancing of the coordinate assignment logic.

## 5. Conclusion

The "Memory Palace" is not a metaphor in this implementation; it is a specific modification of the Transformer's attention mechanism where **spatial coordinates are explicitly injected into the Key-Value attention calculation**. This provides a measurable, differentiable path for the model to reason about the location of information, satisfying the requirement for a formal mapping between the cognitive concept of a "room" and the mathematical operation of attention.