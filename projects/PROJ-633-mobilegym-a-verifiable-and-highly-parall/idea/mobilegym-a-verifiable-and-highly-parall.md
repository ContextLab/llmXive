---
field: computer science
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2605.26114
---

# MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mobile GUI Agent Research

**Builds on**: [MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mobile GUI Agent Research](https://arxiv.org/abs/2605.26114)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
MobileGym introduces a lightweight, browser-hosted Android simulation environment that achieves high interaction fidelity by representing app states as structured JSON, enabling deterministic verification and massive parallelization (hundreds of instances) on a single server. It addresses the trade-off between the reproducibility of emulators and the realism of real-device benchmarks by allowing agents to interact with simulated everyday apps while researchers retain full programmatic control over state forking and reset. The accompanying MobileGym-Bench provides 416 parameterized tasks with deterministic judges, demonstrating that online RL training in this simulation transfers effectively (95.1% gain retention) to real devices.

## Proposed extension
**Research Question:** Can a "State-Aware Curriculum" that dynamically adjusts task difficulty based on the agent's specific failure modes in the structured JSON state space accelerate RL convergence and improve Sim-to-Real transfer more effectively than static, pre-parameterized task templates?

This matters because MobileGym's current benchmark uses fixed parameterized templates; however, the rich, structured state model allows for real-time diagnosis of *why* an agent failed (e.g., wrong navigation path vs. incorrect data entry). A curriculum that adapts to these specific failure modes could solve the "sparse reward" problem in complex GUI tasks without requiring expensive GPU-based pre-training, leveraging the platform's CPU-tractable parallelism to generate adaptive training data on the fly.

## Methodology sketch
**Data:** We will utilize the existing MobileGym-Bench 416 templates but augment them with a "failure taxonomy" derived from the structured JSON state diffs (e.g., `navigation_error`, `data_mismatch`, `side_effect`).
**Procedure:** 
1. Implement a "Curriculum Controller" that runs parallel RL rollouts (using GRPO) on a subset of 50 tasks. 
2. After every epoch, the controller analyzes the JSON state diffs to identify the dominant failure mode for each agent. 
3. The controller dynamically generates new task instances by modifying the JSON state parameters (e.g., increasing data complexity if `data_mismatch` is high, or adding decoy UI elements if `navigation_error` is high) to target the specific weakness, rather than selecting from a static pool.
4. Compare this adaptive approach against the static baseline from the original paper using a CPU-only setup (no GPUs required for the environment or the RL loop itself, only for the policy model inference if using a small distilled model, or even CPU-only inference for small agents).
**Expected Result:** The adaptive curriculum will achieve the same success rate as the static baseline in fewer training steps (measured in environment steps) and demonstrate a higher retention of training gains (e.g., >98% vs. 95.1%) on a held-out real-device subset, proving that leveraging structured state for dynamic curriculum design improves sample efficiency and generalization.
