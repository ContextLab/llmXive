# Formal Mapping: Spatial "Rooms" to Transformer Components

## 1. Overview

This document addresses the concern raised by John von Neumann regarding the rigorous distinction between *address* (physical location) and *content* (logical interpretation) within the proposed Memory Palace architecture. It defines the mathematical and architectural mapping between the 2-D spatial grid ("rooms") and the underlying Transformer components (Attention Heads and Feed-Forward Networks).

In the EDVAC report, von Neumann emphasized that a stored-program computer must clearly separate the location of a datum from its value. Similarly, our model distinguishes the *spatial coordinate* (the "address" in the memory palace) from the *semantic embedding* (the "content" stored at that address).

## 2. The Address-Content Distinction

### 2.1 Spatial Address (The "Room")
The spatial address is a discrete coordinate $(x, y)$ in a fixed 2-D grid of size $H \times W$ (default $8 \times 8 = 64$ slots).
- **Role**: Acts as the index for retrieval and the anchor for positional encoding.
- **Representation**: A unique integer ID $k \in [0, 63]$ or a pair $(x, y)$.
- **Constraint**: The address is static for a given slot but determines the *retrieval context*.

### 2.2 Logical Content (The "Furniture")
The content is the high-dimensional semantic vector $v \in \mathbb{R}^d$ stored at address $(x, y)$.
- **Role**: Encodes the episodic memory (text tokens, facts, or narrative chunks).
- **Representation**: The output of the transformer's value projection or the stored embedding in the `MemorySlot`.
- **Constraint**: Content can be updated (via consolidation) without changing the address.

## 3. Formal Mapping Function

We define the mapping function $f: \mathbb{Z}^2 \to \text{TransformerComponent}$ that links spatial coordinates to specific attention mechanisms.

### 3.1 Modulo-Based Head Assignment
To ensure a deterministic and distributed mapping that avoids collision hotspots, we utilize modulo arithmetic to map the 2-D grid to the Transformer's $N_{heads}$ attention heads.

$$ \text{head\_index}(x, y) = (x \pmod{H_{heads}}) \times W_{heads} + (y \pmod{W_{heads}}) $$

Where:
- $H_{heads}, W_{heads}$ are virtual grid dimensions for heads such that $H_{heads} \times W_{heads} \ge N_{heads}$.
- For GPT-2 Medium ($N_{heads} = 16$), we can map directly: $x \pmod 4, y \pmod 4$.

This function ensures that:
1. **Proximity Preservation**: Adjacent rooms $(x, y)$ and $(x+1, y)$ often share or neighbor the same attention head, facilitating "local" recall.
2. **Global Distribution**: Distant rooms map to different heads, preventing a single head from becoming a bottleneck for the entire memory palace.

### 3.2 Positional Encoding Integration
The spatial coordinates are injected into the transformer via a modified Rotary Positional Embedding (RoPE) or Learnable Positional Embedding:

$$ \text{PE}_{(x,y)} = \text{Learnable}(x, y) $$

The query $q$ and key $k$ vectors for a token associated with room $(x, y)$ are adjusted:
$$ q' = q \cdot \text{rot}(x, y) $$
$$ k' = k \cdot \text{rot}(x, y) $$

This ensures the attention mechanism "knows" the spatial location of the content it is retrieving.

## 4. Architectural Components

### 4.1 The Memory Grid (External Storage)
Implemented in `code/models/memory_slot.py` as `MemoryGrid`.
- **Structure**: A fixed-size array of `MemorySlot` objects.
- **Access**: Direct $O(1)$ access via $(x, y)$.
- **Content**: Stores the `episodic_embedding` and `metadata`.

### 4.2 The Spatial Attention Layer (Internal Processing)
Implemented in `code/models/spatial.py` as `soft_addressed_retrieve`.
- **Mechanism**: Computes attention scores not just on semantic similarity, but on the **spatial proximity** of the query's target room to the stored rooms.
- **Loss Function**: `spatial_attention_loss` penalizes the model if high-similarity content is retrieved from a spatially distant room when a closer match exists, enforcing the "memory palace" topology.

### 4.3 The Consolidation Mechanism
Addressing the stability concern (Eric Kandel), the `OptimizedTrainingLoop` in `code/training/loop.py` applies an Exponential Moving Average (EMA) to the content vectors in the grid, effectively "stabilizing" the furniture in the rooms after each epoch.

## 5. Cost Analysis: Spatial Indexing vs. Baseline

| Metric | Baseline Transformer | Spatial Memory Transformer |
|:--- |:--- |:--- |
| **Retrieval Complexity** | $O(N)$ (Self-Attention over context) | $O(1)$ (Grid lookup) + $O(K)$ (Soft retrieval) |
| **Memory Footprint** | $O(N)$ (Context window) | $O(G)$ (Fixed Grid Size) + $O(N)$ (Input) |
| **Address Overhead** | None (Implicit) | Low (Modulo arithmetic + PE) |
| **Stability** | High (Static weights) | Medium (Requires consolidation logic) |

The spatial indexing adds a negligible computational overhead (modulo operations and grid lookups) but provides a structural inductive bias that significantly improves recall for long-term episodic dependencies by organizing information into a fixed, navigable topology.

## 6. Conclusion

By explicitly separating the **address** (spatial coordinate) from the **content** (semantic vector) and defining a deterministic mapping function $f(x,y)$ to the attention heads, we satisfy the von Neumann requirement for a clear distinction between order and interpretation. This formal mapping allows the model to "navigate" its latent space as a memory palace, retrieving information based on spatial relationships rather than purely sequential proximity.