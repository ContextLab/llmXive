---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Mellum2 Technical Report"

## Proposed extension

**Title:** Mellum 2-Context: Dynamic Expert Routing and Adaptive Speculative Decoding for Ultra-Long Code Repositories

**Research Question:** Can we extend the static MoE routing and fixed-window speculative decoding of Mellum 2 to dynamically adapt expert activation and draft generation strategies based on the semantic complexity of code chunks within a 128K+ context window?

**Why it matters:**
While Mellum 2 successfully achieves a 128K context window and efficient inference via static architectural choices (8 active experts, single MTP head), it treats all tokens within that window uniformly regarding expert selection and speculative drafting. In real-world software engineering, codebases are highly heterogeneous: a 128K window might contain dense, logic-heavy algorithmic cores (requiring high expert activation for reasoning) alongside vast amounts of boilerplate, documentation, or simple configuration files (requiring low compute).

Current static MoE routing may under-allocate compute to complex debugging tasks buried deep in a repository while over-allocating to trivial boilerplate. Similarly, the current Multi-Token Prediction (MTP) head acts as a single, fixed draft model. It may struggle to efficiently "draft" through long, repetitive import sections or complex, multi-step refactoring logic simultaneously.

This study proposes **Dynamic Context-Aware Routing (DCAR)** and **Adaptive Multi-Head Speculation (AMHS)**. We hypothesize that by gating expert activation based on local token entropy and semantic type (e.g., distinguishing between "logic" and "boilerplate" via lightweight probes) and by training specialized MTP heads for different code genres, we can:
1.  Reduce inference latency by 15–20% on full-repository tasks without sacrificing accuracy on hard reasoning benchmarks.
2.  Improve the "per-token compute" efficiency of the Thinking model, allowing it to generate longer, more coherent reasoning traces for agentic coding workflows within the same latency budget.
3.  Extend the effective context window to 256K+ by optimizing the KV-cache management of the sliding window attention layers, which currently consumes significant memory in static configurations.

This directly builds on Mellum 2's open-weight release and its design philosophy of "efficiency on commodity GPUs," pushing the boundaries from *static* efficiency to *dynamic* efficiency.

## Methodology sketch

**Data:**
*   **Base Corpus:** The existing 10.6T token pre-training corpus used for Mellum 2, augmented with a new "Long-Context Code Repository" dataset consisting of 50,000 full GitHub repositories (Python, Java, TypeScript) with context windows ranging from 64K to 256K tokens.
*   **Synthetic Complexity Labels:** We will generate synthetic labels for each code chunk indicating "logical density" (cyclomatic complexity), "repetition ratio," and "semantic type" (logic, docs, config, test) using static analysis tools (e.g., CodeQL, tree-sitter).
*   **Evaluation Set:** A curated benchmark of 2,000 multi-file engineering tasks (e.g., "Refactor this legacy module," "Debug this race condition across 4 files") requiring full-repository context.

**Procedure:**
1.  **Dynamic Routing Probe Training:**
    *   Freeze the Mellum 2 base weights.
    *   Insert lightweight "Router Probes" (1-layer MLPs) before the MoE router in every layer. These probes take local token embeddings and the synthetic complexity labels (as auxiliary inputs) to predict an optimal "expert activation count" (ranging from 1 to 16) for that specific token.
    *   Train these probes using a reinforcement learning objective (PPO) that rewards lower compute cost (fewer active experts) while penalizing drops in next-token prediction accuracy on high-complexity tasks.

2.  **Adaptive Multi-Head Speculation (AMHS):**
    *   Replace the single MTP head with a "Mixture of Drafters" (MoD). We will train three specialized draft heads:
        *   *Draft-Logic:* Optimized for high-entropy, complex algorithmic code.
        *   *Draft-Boilerplate:* Optimized for low-entropy, repetitive patterns (imports, getters/setters).
        *   *Draft-Reasoning:* Optimized for the "Thinking" model's explicit reasoning trace generation.
    *   Implement a dynamic selector that chooses which draft head to activate based on the output of the Router Probes (e.g., if "logical density" is high, activate *Draft-Logic*).

3.  **End-to-End Fine-Tuning (RLVR):**
    *   Fine-tune the combined system (Base + Dynamic Probes + MoD) using the Reinforcement Learning with Verifiable Rewards (RLVR) framework established in Mellum 2.
    *   The reward function will be a composite of: (a) Code execution success (pass/fail tests), (b) Reasoning trace coherence (evaluated by a small judge model), and (c) Inference latency (measured in tokens/second on a single H100).

4.  **Ablation & Evaluation:**
    *   Compare the proposed model against the original Mellum 2 Instruct and Thinking variants.
    *   **Metrics:**
        *   *Efficiency:* Tokens/second (throughput) and FLOPs per token for full-repository tasks.
        *   *Quality:* Pass@1 on the 256K-context engineering benchmark.
        *   *Context Integrity:* Ability to retrieve and reason over code defined >100K tokens ago.
    *   **Stress Test:** Measure the degradation of the Thinking model's reasoning trace length under the new dynamic constraints.

**Expected Result:**
We anticipate that the Dynamic Context-Aware Routing will reduce average active parameters per token by ~20% on standard repository tasks (mostly boilerplate) while maintaining or slightly increasing active parameters for complex logic, resulting in a net 15% latency reduction. The Adaptive Multi-Head Speculation is expected to double the acceptance rate of speculative decoding for reasoning traces, allowing the Thinking model to emit 2x longer reasoning chains within the same time budget. This will effectively demonstrate that "static efficiency" can be evolved into "semantic efficiency" for next-generation coding assistants.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Mellum2 Technical Report** — Marko Kojic, Ivan Bondyrev, Aral de Moor, Joseph Shtok, Petr Borovlev, Kseniia Lysaniuk, Madeeswaran Kannan, Ivan Dolgov, Nikita Pavlichenko. https://arxiv.org/abs/2605.31268.

```bibtex
@article{orig_arxiv_2605_31268,
  title = {Mellum2 Technical Report},
  author = {Marko Kojic and Ivan Bondyrev and Aral de Moor and Joseph Shtok and Petr Borovlev and Kseniia Lysaniuk and Madeeswaran Kannan and Ivan Dolgov and Nikita Pavlichenko},
  year = {2026},
  eprint = {2605.31268},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.31268},
  url = {https://arxiv.org/abs/2605.31268}
}
```
