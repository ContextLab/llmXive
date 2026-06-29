---
field: computer science
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2605.20682
---

# IndusAgent: Reinforcing Open-Vocabulary Industrial Anomaly Detection with Agentic Tools

**Builds on**: [IndusAgent: Reinforcing Open-Vocabulary Industrial Anomaly Detection with Agentic Tools](https://arxiv.org/abs/2605.20682)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
IndusAgent introduces a tool-augmented agentic framework that enhances open-vocabulary industrial anomaly detection by enabling Multimodal Large Language Models (MLLMs) to dynamically invoke external tools like region cropping and prior retrieval. The approach relies on a specialized dataset (Indus-CoT) and a gated reinforcement learning objective to train the agent to gather high-resolution evidence only when necessary, thereby reducing hallucinations and improving zero-shot performance on standard benchmarks.

## Proposed extension
**Research Question:** Can a CPU-tractable, text-only "latent tool planner" trained on Indus-CoT trajectories predict the necessity of visual tool invocation with >90% accuracy before any image processing occurs, thereby eliminating the computational overhead of redundant tool calls in resource-constrained edge environments?

This direction matters because IndusAgent's current architecture incurs latency and energy costs by potentially invoking tools that the agent could have predicted as unnecessary based on global context alone; a pre-filtering mechanism would enable industrial deployment on low-power hardware without sacrificing the accuracy gains from active inspection.

## Methodology sketch
**Data:** Extract the full reasoning trajectories from the existing Indus-CoT dataset, specifically pairing the initial global image description (or the model's initial "thought" before tool calls) with the binary ground truth of whether a tool was actually beneficial (defined as the difference in final accuracy with vs. without the tool in the original IndusAgent log).

**Procedure:** 
1. Train a lightweight, transformer-based classifier (e.g., DistilBERT or a small MLP) on the CPU using only the textual prefixes of the Indus-CoT trajectories (excluding image tokens) to predict a "Tool Necessity Score" (0-1).
2. Simulate a deployment scenario where this CPU model acts as a gatekeeper: if the score is below a threshold (e.g., 0.8), the system skips all image-processing tools and proceeds directly to classification; if above, it triggers the full IndusAgent pipeline.
3. Evaluate the "CPU-Only Planner" on the MVTec-AD and VisA test sets, measuring the reduction in average inference time and GPU memory usage against a baseline where tools are invoked stochastically or based on IndusAgent's original policy.

**Expected Result:** The study will demonstrate that a text-only predictor can identify ~40-50% of unnecessary tool invocations with high precision, reducing the average computational cost of the IndusAgent pipeline by over 30% while maintaining anomaly detection accuracy within 1-2% of the full tool-augmented version.
