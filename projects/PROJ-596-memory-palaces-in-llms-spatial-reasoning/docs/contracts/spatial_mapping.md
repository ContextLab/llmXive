# Formal Mapping: Spatial "Rooms" to Transformer Components

## Overview

This document addresses the concern raised by John von Neumann regarding the rigorous definition of the mapping function between the "spatial coordinates" of the Memory Palace architecture and the transformer's attention mechanism. Specifically, it formalizes the distinction between **Address** (physical location in the grid) and **Content** (logical interpretation/data stored), ensuring a deterministic and computable relationship that avoids the "binding problem" in artificial memory systems.

## 1. The Address-Content Distinction

Per the EDVAC report, a computational system must distinguish between the *order* (program) and the *content* (data). In the context of the Memory Palace:

- **Address (Spatial Coordinate)**: A fixed 2D integer pair $(x, y)$ representing a specific "room" or slot in the $8 \times 8$ grid. This acts as the *index* into the memory structure.
- **Content (Episodic Chunk)**: The vector representation $V \in \mathbb{R}^d$ (embedding) of the episodic memory stored at that address.

The mapping function $f: (x, y) \to \text{AttentionMechanism}$ is not a direct physical wiring but a **logical addressing scheme** mediated by the coordinate assignment logic.

## 2. Formal Mapping Function

The project implements a **Modulo Arithmetic Mapping** to translate spatial coordinates into transformer-compatible attention heads and key-value projections. This ensures that the spatial topology is preserved in the latent space without requiring a separate physical memory bank for every coordinate.

### 2.1. Coordinate-to-Head Mapping

Given a grid of width $W=8$ and height $H=8$, and a transformer with $N_{heads}$ attention heads, the mapping $M_{head}$ is defined as:

$$M_{head}(x, y) = (x \pmod{H}, y \pmod{W}) \pmod{N_{heads}}$$

This function ensures that:
1. **Determinism**: The same coordinate $(x, y)$ always maps to the same attention head (or subset of heads).
2. **Coverage**: The modulo operation distributes spatial locations across available heads, preventing head saturation.
3. **Locality Preservation**: Adjacent coordinates $(x, y)$ and $(x+1, y)$ map to adjacent or nearby head indices, preserving the topological structure required for "soft-addressed retrieval."

### 2.2. Spatial Attention Mechanism

The transformer's standard attention mechanism is augmented with a **Spatial Bias Term** $B_{spatial}$. For a query $Q$ at coordinate $(x_q, y_q)$ and a key $K$ at $(x_k, y_k)$, the attention score $A_{q,k}$ is computed as:

$$A_{q,k} = \frac{(Q \cdot K^T)}{\sqrt{d_k}} + \lambda \cdot \text{Cosine}((x_q, y_q), (x_k, y_k))$$

Where:
- $\lambda$ is a learnable scalar controlling the strength of spatial bias.
- $\text{Cosine}(\cdot)$ computes the similarity of the coordinate vectors, effectively implementing a "distance penalty" or "proximity bonus" in the attention weights.

This formulation ensures that the model explicitly "attends" to memories stored in spatially proximate "rooms," mimicking the cognitive phenomenon of context-dependent recall.

## 3. Implementation Traceability

The following code artifacts implement the formal mappings described above:

- **Coordinate Assignment**: `code/models/coordinate_assigner.py` implements the sequential row-major mapping and the modulo-based head selection.
- **Spatial Attention**: `code/models/spatial.py` contains the `soft_addressed_retrieve` and `spatial_attention_loss` functions, which apply the bias term $B_{spatial}$ during forward passes.
- **Memory Grid**: `code/models/memory_slot.py` defines the `MemoryGrid` data structure, which enforces the $8 \times 8$ capacity and FIFO eviction policy, acting as the physical constraint on the logical address space.

## 4. Addressing the Binding Problem

The "binding problem" arises when the system fails to associate a specific feature (content) with its correct location (address). By using the **Modulo Arithmetic Mapping** as a deterministic index, the system guarantees that:
- The address $(x, y)$ is an immutable property of the slot during the retrieval phase.
- The content $V$ is stored *only* at the slot determined by $f(x, y)$.
- Retrieval queries explicitly include the target coordinate, ensuring that the attention mechanism focuses on the correct "room."

This design satisfies the requirement for a rigorous, computable distinction between the physical location of a datum and its logical interpretation, as mandated by von Neumann's architectural principles.

## 5. Conclusion

The Memory Palace architecture is not merely a heuristic but a formally defined mapping between 2D spatial coordinates and transformer attention mechanisms. The use of modulo arithmetic for head selection and spatial bias terms for attention scoring provides a robust, deterministic framework for episodic recall, directly addressing the concerns regarding the binding problem and the address-content distinction.