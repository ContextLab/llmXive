# Research: Map-Free Transit Route Generation with LLMs

## Research Question

Can Large Language Models, trained exclusively on textual transit logs and station metadata without explicit geographic coordinates or map topology, learn to generate valid public transit routes that satisfy real-world connectivity constraints?

## Methodology

### 1. Dataset Construction (Map-Free Constraint)
The core challenge is constructing a dataset that strictly adheres to the "map-free" constraint.
- **Source**: **New York City MTA GTFS Feed** (Canonical Source: `https://api.mta.info/#/gtfs` or via `gtfs` Python library).
  - **Fallback**: If the live feed is unreachable, a **deterministic synthetic GTFS** will be generated using `synthetic_gtfs` with a fixed seed (42) to ensure reproducibility. This fallback is documented in `data/raw/synthetic_gtfs_source.txt`.
- **Transformation**: Convert GTFS `stops.txt`, `routes.txt`, and `stop_times.txt` into natural language sequences.
  - **Input Format**: "Take [Line ID] from [Station Name A] to [Station Name B]."
  - **Exclusion**: Strictly remove latitude/longitude coordinates, map topology (adjacency lists), and any geographic metadata.
  - **Validation**: A regex scan will verify zero coordinate patterns (e.g., `\d+\.\d+`) in the generated text.

### 2. Model Selection & Fine-Tuning
- **Model Architecture**: A small, CPU-tractable LLM (e.g., Llama-3-1.5B or Qwen2.5-1.5B).
  - **Rationale**: Must fit within 7GB RAM on GitHub Actions free-tier. Larger models (7B+) require GPU or heavy quantization incompatible with CPU-only training.
  - **Quantization**: 8-bit quantization (`bitsandbytes` CPU-compatible) for the baseline; default precision (float32/float16) for fine-tuning with LoRA to reduce memory overhead. 4-bit quantization is explicitly avoided due to instability on CPU.
- **Training Strategy**: Supervised Fine-Tuning (SFT) with LoRA (Low-Rank Adaptation).
  - **Hardware**: CPU-only (PyTorch default precision).
  - **Batch Size**: 1 or 2 to fit memory.
  - **Dataset**: ~10k sequences derived from a single city's GTFS.
 - **Data Scale Justification**: 10k sequences cover [deferred] of unique edges in a single city network. The task is treated as 'next-token prediction' on a graph structure. If performance is low, a 'Curriculum Learning' step will increase data volume by re-sampling edges, but edge coverage is prioritized over raw volume.
- **Baseline Strategy**:
  1. **Random Walk Baseline**: A simple random walk on the GTFS graph to establish a lower bound for "valid but non-optimal" paths.
  2. **Synthetic Network Control**: A model trained on a *synthetic* random graph (unknown to any pre-trained model) to isolate "learning from text" from "world knowledge".
  3. **General LLM Baseline**: A quantized 1.5B model (8-bit) on a *non-transit* corpus to control for instruction-following capability.

### 3. Evaluation Protocol
- **Held-Out Set**: Origin-Destination (O-D) pairs and intermediate connections *not* present in the training text sequences.
  - **Splitting Strategy**: **Path-Disjoint Split**. The training set contains specific station pairs (A->B). The test set contains pairs (C->D) where the *specific edge sequence* (e.g., C->E->D) is never seen in any training sequence. This ensures the model must infer connectivity, not recall a sequence.
- **Validation Oracle**: A deterministic graph-traversal script (NetworkX) built from the original GTFS data.
  - **Metric 1: Connectivity Validity**: Binary score (1 if every consecutive station pair exists as a direct connection in the GTFS graph, 0 otherwise).
  - **Metric 2: Exact Match**: Percentage of generated routes that exactly match the ground-truth shortest path.
  - **Metric 3: Shortest-Path Deviation**: Ratio of generated path length to the ground-truth shortest path length. This distinguishes between "valid but inefficient" loops and "optimal" routing.
- **Statistical Analysis**:
  - **Binary Metrics (Validity)**: **McNemar's Test** for paired binary data (Valid/Invalid) to compare fine-tuned vs. baseline.
  - **Continuous Metrics (Deviation)**: **Permutation Test** (10,000 iterations) to compare distributions without assuming normality.

## Dataset Strategy

| Dataset | Source / Loader | Purpose | Verification Status |
| :--- | :--- | :--- | :--- |
| **NYC MTA GTFS** | `gtfs` library / `https://api.mta.info/#/gtfs` | Ground-truth graph construction and text generation. | **Verified Source** (Canonical API). Fallback: Deterministic Synthetic (fixed seed). |
| **Training Text** | Derived from GTFS | Fine-tuning the LLM. | N/A (Derived artifact). |
| **Held-Out O-D Pairs** | Derived from GTFS (Path-Disjoint) | Evaluation of generalization. | N/A (Derived artifact). |
| **Synthetic Network** | `synthetic_gtfs` (Seed 42) | Control experiment to isolate "learning from text". | N/A (Synthetic). |

*Note: The verified dataset URLs provided in the spec (e.g., `gorilla-llm`, `Exgentic`) are for general LLM traces and do not contain transit-specific GTFS data. Therefore, the project relies on the canonical NYC MTA feed or deterministic synthetic generation as described.*

## Statistical Rigor

- **Multiple Comparison Correction**: Bonferroni correction applied if testing multiple models or cities.
- **Power Analysis**: A power analysis will be conducted *post-hoc* or based on pilot runs to determine the minimum N required for significance (target p < 0.05). If the sample size is small (N < 30), the permutation test will be preferred.
- **Causal Inference**: The study is observational regarding the model's internal state. Claims will be framed as "improvement in topological reasoning performance" rather than "causal learning of geography".
- **Measurement Validity**: The GTFS graph serves as the ground truth for connectivity. The "map-free" constraint is validated via regex scanning of the input text.
- **Statistical Method Selection**: McNemar's test is the default for binary outcomes (Valid/Invalid) as it handles paired data correctly. T-tests are avoided for binary data.

## Compute Feasibility

- **Hardware Constraints**: GitHub Actions free-tier (2 CPU, 7GB RAM, 14GB disk, 6h limit).
- **Model Size**: ≤ 1.5B parameters (e.g., Llama-3-1.5B-Instruct).
- **Quantization**: 8-bit quantization (`bitsandbytes` CPU-compatible) for baseline; default precision for fine-tuning with LoRA.
- **Data Sampling**: Dataset limited to ~10k sequences to ensure training completes within 6 hours.
- **Inference**: Batch size 1 for generation to avoid OOM errors.
- **Validation**: Graph traversal is O(V+E) and computationally negligible.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **OOM on Training** | Use LoRA, reduce batch size to 1, limit sequence length. |
| **Coordinate Leakage** | Rigorous regex validation of input text; manual spot-checks. |
| **Hallucinated Stations** | The graph-traversal script will detect these and flag as "Invalid". |
| **No Valid Route Exists** | The system will return "No Route" or validity 0. This is a valid outcome. |
| **Training Time Exceeds 6h** | Limit dataset size to 5k-10k sequences; use early stopping. |
| **Pre-trained Knowledge Confound** | Use the Synthetic Network Control experiment to isolate "learning from text". |

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use LoRA for Fine-Tuning** | Reduces memory footprint, enabling training on 7GB RAM CPU. |
| **Use NetworkX for Validation** | Deterministic, lightweight, and standard for graph connectivity checks. |
| **NYC MTA GTFS as Primary Source** | Canonical source with deterministic fallback for reproducibility. |
| **McNemar's Test** | Statistically valid for paired binary data (Valid/Invalid). |
| **Path-Disjoint Splitting** | Ensures the test measures topological inference, not sequence memorization. |
| **Synthetic Network Control** | Isolates "learning from text" from pre-trained world knowledge. |
| **8-bit Quantization (No 4-bit)** | 4-bit is unstable on CPU; 8-bit is the most aggressive stable quantization. |
