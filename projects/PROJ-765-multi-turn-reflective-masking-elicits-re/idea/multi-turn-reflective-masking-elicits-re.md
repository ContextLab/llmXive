---
field: linguistics
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2606.16700
---

# Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Models

**Builds on**: [Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Models](https://arxiv.org/abs/2606.16700)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
The paper introduces Reflective Masking (RM), a lightweight post-training technique for Mask Diffusion Models (MDMs) that enables multi-turn, iterative local refinement of outputs without architectural changes. By leveraging a "History Reference" mechanism to utilize intermediate denoising states, RM allows MDMs to perform native test-time scaling similar to Chain-of-Thought reasoning in autoregressive models. The approach demonstrates superior performance over standard masking baselines across text, Sudoku, and image editing tasks by mimicking human-like iterative correction.

## Proposed extension
**Research Question:** Can the computational overhead of multi-turn Reflective Masking be reduced to near-zero by dynamically pruning the "History Reference" context based on the entropy of the current masking step, thereby enabling efficient reasoning on CPU-only environments?

This matters because while RM is effective, its requirement to maintain and attend to intermediate denoising states across multiple turns creates a quadratic memory and compute bottleneck that hinders deployment on resource-constrained devices; proving that only a sparse subset of historical states is necessary for high-quality reasoning would make MDM-based reasoning scalable and practical for edge computing.

## Methodology sketch
**Data:** We will utilize the existing Sudoku and GSM8K (math word problem) benchmarks from the original paper, specifically focusing on instances where the model initially fails but succeeds after 2+ refinement turns.
**Procedure:** We will implement a "Sparse History Reference" variant where, at each refinement turn $t$, the model computes the entropy of the current masked token distribution; if entropy is below a threshold $\tau$, the model discards all historical states prior to turn $t-k$ (where $k$ is a small constant, e.g., 1 or 2), retaining only the immediate predecessor and the initial prompt. We will run this on a standard CPU (e.g., Intel Xeon) to measure inference latency and memory usage, comparing the accuracy-latency trade-off against the full-history RM baseline.
**Expected Result:** We anticipate that the sparse variant will achieve parity in accuracy (within 1-2% of the full-history baseline) while reducing CPU inference time by 40-60% and memory footprint by 50%, demonstrating that high-entropy "decision points" are the only critical moments requiring deep historical context for effective reasoning.
