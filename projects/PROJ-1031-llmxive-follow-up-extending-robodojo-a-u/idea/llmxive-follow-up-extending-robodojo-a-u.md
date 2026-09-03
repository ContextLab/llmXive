---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluatio"

**Field**: computer science

## Research question

To what extent is high-fidelity continuous physics simulation necessary for successful long-horizon robot manipulation planning, and can topological symbolic abstractions alone suffice to bridge the sim-to-real gap in generalist policies?

## Motivation

Current benchmarks like RoboDojo rely heavily on computationally intensive GPU-based physics simulators, creating a barrier for researchers with limited hardware. This research investigates whether "logical correctness" (topological task constraints) is a more critical bottleneck than continuous physical fidelity for long-horizon tasks, potentially enabling high-throughput, CPU-tractable evaluation pipelines while challenging the assumption that high-fidelity physics is strictly necessary for complex manipulation planning.

## Related work

- [RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies](https://arxiv.org/abs/2607.04434) — Establishes the baseline 18 real-world tasks and 42 simulation tasks, highlighting the current reliance on GPU-intensive simulators and the challenges of long-horizon execution.
- [Robot Policy Evaluation for Sim-to-Real Transfer: A Benchmarking Perspective](https://arxiv.org/abs/2508.11117) — Critiques the disconnect between simulation benchmarks and real-world application, emphasizing the need for evaluation protocols that prioritize real-world viability over simulation fidelity.
- [Sim-to-Real Transfer in Deep Reinforcement Learning for Bipedal Locomotion](https://arxiv.org/abs/2511.06465) — Discusses the critical challenges of transferring learned policies from simulation to reality in dynamic environments, reinforcing the need for robust transfer mechanisms that can handle discrepancies between simulated and real-world dynamics.
- [Towards bridging the gap: Systematic sim-to-real transfer for diverse legged robots](https://arxiv.org/abs/2509.06342) — Highlights that controllers trained in simulation often fail to transfer reliably, suggesting that current simulation models may lack the necessary generalization properties for complex real-world deployment.

## Expected results

We expect to observe that a symbolic-planning extension achieves comparable success rates on long-horizon tasks (e.g., multi-step assembly) by reducing decision-space complexity, while operating with a significant reduction in computational cost compared to GPU-based baselines. Success will be measured by the binary task completion rate across the 18 real-world RoboDojo tasks and the wall-clock time required to generate valid action sequences on a standard CPU, with the null hypothesis being that the loss of physical fidelity in the symbolic layer leads to catastrophic failure in real-world execution due to unmodeled dynamics.

## Methodology sketch

- Download the RoboDojo dataset (18 real-world task videos and 42 simulation task specifications) from the official repository and pre-process visual observations into high-level semantic embeddings using a frozen, CPU-efficient vision encoder (e.g., MobileViT).
- Implement a "Symbolic-Dojo" adapter that maps these semantic embeddings into a discrete state space (e.g., PDDL-like predicates) representing object affordances and connectivity, explicitly stripping away continuous physics variables like friction coefficients and mass distribution.
- Develop a hierarchical policy architecture where a high-level symbolic planner (e.g., A* or Monte Carlo Tree Search) generates a sequence of discrete sub-goals based on the abstract task description, running entirely on CPU.
- Integrate a low-level controller using pre-trained weights from RoboDojo's baseline policies to execute the generated sub-goals in the real-world environment, utilizing the semantic embeddings for grounding without re-training on physics dynamics.
- Evaluate the hybrid system against the original RoboDojo baseline policies on the 18 real-world tasks, measuring success rate, time-to-solution, and compute overhead (CPU cycles and memory usage).
- Perform statistical analysis using a Wilcoxon signed-rank test to compare the success rates of the symbolic approach versus the continuous physics baseline, ensuring the evaluation metric (real-world success) is independent of the simulation fidelity used during planning.
- Conduct an ablation study to isolate the impact of the symbolic abstraction layer by varying the level of detail in the state representation (e.g., full affordance graph vs. simplified connectivity graph) to determine the minimum information required for successful transfer.

## Duplicate-check

- Reviewed existing ideas: llmXive follow-up: extending "RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluatio".
- Closest match: llmXive follow-up: extending "RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluatio" (similarity sketch: This is the source idea itself; no other distinct ideas in the corpus match this specific focus on symbolic abstraction for CPU-tractable long-horizon planning).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-09-03T13:09:54Z
**Outcome**: success_after_expansion
**Original term**: llmXive follow-up: extending "RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluatio" computer science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluatio" computer science | 0 |
| 1 | sim-to-real transfer learning benchmarks for robotics | 5 |
| 2 | unified simulation and real-world evaluation frameworks for robots | 0 |
| 3 | sim-to-real gap reduction in robotic policy learning | 0 |
| 4 | comprehensive robotics benchmark suites for sim-and-real deployment | 0 |
| 5 | domain randomization techniques for sim-to-real transfer | 0 |
| 6 | real-world validation of simulated robotic training environments | 0 |
| 7 | benchmarking robotic learning algorithms across simulation and reality | 0 |
| 8 | sim-to-real generalization in deep reinforcement learning for robotics | 0 |
| 9 | unified platforms for evaluating robotic sim-to-real performance | 0 |
| 10 | transfer learning from simulation to physical robots benchmarks | 0 |
| 11 | sim-to-real adaptation strategies for autonomous robots | 0 |
| 12 | evaluating robotic policies in simulated and real environments | 0 |
| 13 | cross-domain evaluation of robotic learning systems | 0 |
| 14 | sim-to-real robustness metrics for robotic control | 0 |
| 15 | standardized benchmarks for sim-and-real robot learning | 0 |
| 16 | bridging the sim-to-real gap in robotic manipulation tasks | 0 |
| 17 | simulation-based training with real-world robotic deployment benchmarks | 0 |
| 18 | comparative analysis of sim-to-real performance in robotics | 0 |
| 19 | robotic learning evaluation protocols for mixed sim-real settings | 0 |
| 20 | sim-to-real transfer efficiency in comprehensive robot benchmarks | 0 |

### Verified citations

1. **RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies** (2026). Tianxing Chen, Yue Chen, Zixuan Li, Junyuan Tang, Kailun Su, et al.. arXiv. [2607.04434](https://arxiv.org/abs/2607.04434). PDF-sampled: No.
2. **Robot Policy Evaluation for Sim-to-Real Transfer: A Benchmarking Perspective** (2025). Xuning Yang, Clemens Eppner, Jonathan Tremblay, Dieter Fox, Stan Birchfield, et al.. arXiv. [2508.11117](https://arxiv.org/abs/2508.11117). PDF-sampled: No.
3. **Towards bridging the gap: Systematic sim-to-real transfer for diverse legged robots** (2025). Filip Bjelonic, Fabian Tischhauser, Marco Hutter. arXiv. [2509.06342](https://arxiv.org/abs/2509.06342). PDF-sampled: No.
4. **Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories** (2026).  Xiaomi Robotics Team, Jun Guo, Piaopiao Jin, Jason Li, Peiyan Li, et al.. arXiv. [2607.15330](https://arxiv.org/abs/2607.15330). PDF-sampled: No.
5. **Sim-to-Real Transfer in Deep Reinforcement Learning for Bipedal Locomotion** (2025). Lingfan Bao, Tianhu Peng, Chengxu Zhou. arXiv. [2511.06465](https://arxiv.org/abs/2511.06465). PDF-sampled: No.
