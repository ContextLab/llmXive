---
field: computer science
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2606.06036
---

# Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents

**Builds on**: [Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents](https://arxiv.org/abs/2606.06036)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
The paper introduces MRAgent, a framework that replaces static retrieval with an active, graph-based memory reconstruction mechanism for LLM agents. By organizing memory into a Cue-Tag-Content graph and integrating reasoning directly into the traversal process, the system dynamically prunes retrieval paths based on intermediate evidence. This approach significantly improves long-horizon reasoning performance on benchmarks like LoCoMo while reducing computational costs compared to traditional retrieve-then-reason pipelines.

## Proposed extension
**Research Question:** How does the topological sparsity of the Cue-Tag-Content graph influence the "reconstruction latency" (steps required to converge on a valid memory path) in MRAgent, and can a lightweight, CPU-tractable graph pruning heuristic outperform the LLM-guided active reconstruction in low-complexity domains?

This matters because the current active reconstruction mechanism relies on iterative LLM calls to traverse the graph, which may introduce unnecessary overhead when the memory structure is already highly optimized or the reasoning task is shallow. Determining if structural properties alone can drive efficient retrieval would allow for hybrid systems that bypass LLM inference for memory access in specific contexts, drastically reducing latency and enabling deployment on edge devices without GPUs.

## Methodology sketch
**Data:** We will synthesize a suite of 500 "Long-History Logic Puzzles" with controlled graph properties, varying the average degree (sparsity) of the Cue-Tag-Content graph from 2 to 10 while keeping the total memory size constant. We will also use a subset of the existing LoCoMo benchmark filtered for tasks requiring fewer than 5 reasoning steps to ensure CPU tractability.

**Procedure:**
1.  **Graph Construction:** Generate the Cue-Tag-Content graphs for each puzzle instance, ensuring distinct sparsity levels.
2.  **Baseline Execution:** Run the original MRAgent (LLM-guided active reconstruction) on these instances to establish a baseline for "reconstruction latency" (number of graph hops) and token usage.
3.  **Heuristic Intervention:** Implement a CPU-only "Structural Pruning Heuristic" that calculates node centrality and path entropy to pre-filter retrieval candidates before any LLM inference occurs, effectively replacing the active reconstruction loop with a deterministic graph traversal for low-complexity tasks.
4.  **Comparison:** Measure the success rate, reconstruction latency (in seconds on a single CPU core), and total token cost for both the baseline and the heuristic approach across varying sparsity levels.

**Expected Result:** We anticipate finding a "tipping point" in graph sparsity where the LLM-guided active reconstruction becomes less efficient than the deterministic structural heuristic. Specifically, we expect the heuristic to match or exceed the baseline accuracy while reducing reconstruction latency by 40-60% in sparse graphs (degree < 4), demonstrating that for certain memory structures, active reconstruction is redundant and structural properties alone suffice for efficient retrieval.
