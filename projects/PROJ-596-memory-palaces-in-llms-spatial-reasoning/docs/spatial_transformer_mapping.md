# Formal Mapping: Spatial "Rooms" to Transformer Components

This document addresses the concern raised by John von Neumann regarding the lack of a rigorous definition of the mapping function between the proposed "spatial coordinates" and the transformer's attention mechanism. It formalizes the architectural correspondence between the cognitive metaphor of "Memory Palaces" (rooms) and the mathematical operations within the transformer model.

## 1. Conceptual Framework

In the proposed architecture, the "Memory Palace" is not a physical structure but a learned, high-dimensional latent space organized by explicit coordinate assignments. The "rooms" are conceptual regions within this space, defined by the distribution of attention heads and the resulting key-value pairings.

## 2. Component Mapping

The following table details the formal mapping between the spatial metaphor and the transformer components as implemented in `code/models/spatial.py` and `code/models/memory_slot.py`.

| Spatial Metaphor | Transformer Component | Mathematical Formalism | Implementation Reference |
|:--- |:--- |:--- |:--- |
| **The Palace (Global Space)** | **Latent Embedding Space** | $\mathcal{E} \subset \mathbb{R}^d$ | `code/models/memory_slot.py` (`MemoryGrid`) |
| **Room (Specific Region)** | **Attention Head / Subspace** | $h_i \in \mathbb{R}^{d_k}$ | `code/models/spatial.py` (`soft_addressed_retrieve`) |
| **Coordinate (Address)** | **Query Vector ($Q$)** | $Q = X W_Q$ | `code/models/spatial.py` |
| **Furniture (Content)** | **Value Vector ($V$)** | $V = X W_V$ | `code/models/spatial.py` |
| **Proximity (Similarity)** | **Dot-Product Attention** | $\text{Attention}(Q, K, V) = \text{softmax}(\frac{QK^T}{\sqrt{d_k}})V$ | `code/models/spatial.py` (`compute_cosine_similarity`) |
| **Distance Metric** | **Cosine Similarity / Euclidean** | $d(x, y) = 1 - \frac{x \cdot y}{\|x\|\|y\|}$ | `code/models/spatial.py` (`compute_cosine_similarity`) |
| **Navigation (Retrieval)** | **Soft-Addressed Retrieval** | $\sum_i \alpha_i v_i$ where $\alpha_i = \text{softmax}(\text{sim}(q, k_i))$ | `code/models/spatial.py` (`soft_addressed_retrieve`) |
| **Memory Slot** | **Key-Value Pair** | $(k_i, v_i)$ | `code/models/memory_slot.py` (`MemorySlot`) |

## 3. The Addressing Function

Per the EDVAC report distinction between *order* (program) and *data*, the "spatial coordinates" in this system function as the **address** (derived from the Query), while the episodic chunks function as the **data** (stored in Values).

The mapping function $f: \mathbb{R}^d \to \mathbb{R}^d$ that transforms a raw token embedding into a "spatial address" is implemented as the projection matrix $W_Q$ in the attention mechanism.

$$ \text{Address}_i = \text{Input}_i \cdot W_Q $$

The "distance" between two memories (e.g., two rooms) is not a Euclidean distance in physical space, but a semantic distance in the attention space, computed via the cosine similarity of their respective Query vectors against the stored Keys.

## 4. Spatial Attention Loss

To enforce the "spatial" organization (i.e., to ensure that semantically related items cluster in the same "room"), we introduce an auxiliary loss term, `spatial_attention_loss`, implemented in `code/models/spatial.py`.

This loss penalizes the model if the attention weights $\alpha$ do not align with the pre-assigned spatial coordinates (from `code/models/coordinate_assigner.py`).

$$ \mathcal{L}_{spatial} = \lambda \sum_{i,j} \| \text{coord}(i) - \text{coord}(j) \| \cdot \alpha_{i,j} $$

Where:
- $\text{coord}(i)$ is the 2D coordinate assigned to chunk $i$.
- $\alpha_{i,j}$ is the attention weight from query $i$ to key $j$.
- $\lambda$ is a hyperparameter controlling the strength of the spatial constraint.

## 5. Conclusion

The "Memory Palace" is a metaphorical overlay on the standard transformer attention mechanism. The "rooms" are emergent clusters in the attention subspace, and the "coordinates" are explicit constraints applied to the Key-Value pairs to guide the attention mechanism toward a spatially organized retrieval pattern. This formalization satisfies the requirement for a rigorous definition of the mapping function, distinguishing the logical address (Query/Coordinate) from the physical content (Value/Chunk).