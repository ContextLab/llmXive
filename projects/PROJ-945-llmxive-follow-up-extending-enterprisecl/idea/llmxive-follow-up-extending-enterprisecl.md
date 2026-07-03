---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions"

## Summary of the prior work
EnterpriseClawBench introduces a benchmark constructed from real-world enterprise agent sessions to evaluate the multidimensional performance of agent harnesses and models on artifact delivery, cost, and skill transfer. The study reveals that performance is heavily dependent on the specific "harness-model" coupling, with significant drops observed when models interact with incompatible execution environments, and establishes a protocol for generating reproducible tasks from proprietary data without releasing the raw data itself.

## Proposed extension
**Research Question:** Can a lightweight, CPU-tractable "Skill Adapter" module, trained solely on the *execution traces* (tool calls, error logs, and intermediate states) of a specific harness, mitigate the performance collapse observed when high-capability models are paired with restrictive harnesses (e.g., Claude models under the Hermes harness)?

This question matters because the original paper identifies harness-model incompatibility as a primary bottleneck, yet current solutions rely on expensive model retraining or switching; a trace-based adapter could decouple model capability from harness constraints using only CPU resources, offering a practical deployment fix for enterprise systems.

## Methodology sketch
*   **Data:** Use the 852-task set from EnterpriseClawBench, specifically extracting the "failed" execution traces from the Hermes/Claude-family combinations (identified in the prior work as having high cost but low score) and the corresponding "successful" traces from the OpenClaw/Claude-family combinations.
*   **Procedure:** 
    1.  Construct a dataset of (Prompt, Failed_Trace, Success_Trace) triplets. 
    2.  Train a small, CPU-optimized sequence-to-sequence model (e.g., a distilled T5 or a rule-based finetuned Llama-3-8B via 4-bit quantization on a CPU) to predict the *correction steps* required to transform a failed trace into a successful one, focusing only on tool-call syntax and state-recovery logic. 
    3.  Integrate this trained adapter as a pre-processing layer that intercepts the agent's output before it reaches the restrictive harness, rewriting tool calls or injecting state-recovery commands. 
    4.  Evaluate the new "Model + Adapter + Harness" configuration against the original "Model + Harness" baseline on the held-out 120-task Lite set.
*   **Expected Result:** The adapter should significantly increase the artifact delivery score for the previously failing combinations (e.g., Hermes/Claude) by correcting the specific trace-level mismatches, approaching the performance of the native "Model + Compatible Harness" pairs, while incurring negligible additional runtime cost and requiring no GPU acceleration for the adapter itself.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions** — Jincheng Zhong, Weizhi Wang, Che Jiang, Kai Tian, Zhenzhao Yuan, Junlin Yang, Dianqiao Lei, Kaiyan Zhang. https://arxiv.org/abs/2606.23654.

```bibtex
@article{orig_arxiv_2606_23654,
  title = {EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions},
  author = {Jincheng Zhong and Weizhi Wang and Che Jiang and Kai Tian and Zhenzhao Yuan and Junlin Yang and Dianqiao Lei and Kaiyan Zhang},
  year = {2026},
  eprint = {2606.23654},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.23654},
  url = {https://arxiv.org/abs/2606.23654}
}
```
