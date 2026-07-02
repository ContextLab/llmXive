---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mo"

## Summary of the prior work
MobileGym introduces a lightweight, browser-hosted mobile simulation platform that uses structured JSON state to enable deterministic verification and high-throughput parallel rollouts for mobile GUI agents. By replacing heavyweight emulators with a state-manipulatable environment, it facilitates scalable online Reinforcement Learning (RL) and provides a benchmark (MobileGym-Bench) with 416 parameterized tasks across 28 apps. The study validates that agents trained in this simulated environment retain over 95% of their performance gains when transferred to real devices.

## Proposed extension
**Research Question:** Can a "State-Guided Curriculum" that dynamically adjusts task difficulty based on an agent's real-time state-space coverage (rather than static parameterization) significantly accelerate RL convergence and improve Sim-to-Real transfer robustness compared to MobileGym's current static training set?

This matters because MobileGym currently relies on fixed train/test splits; however, RL agents often waste compute on tasks they have already mastered or get stuck on "hard" tasks that are solvable only via specific state configurations. A dynamic curriculum could optimize the CPU-tractable parallel rollouts by focusing agent exploration on unvisited state transitions, potentially reducing the total number of required rollouts by 50% while increasing the diversity of learned policies for real-world deployment.

## Methodology sketch
**Data:** Utilize the existing MobileGym-Bench task templates (256 test + 160 train) and the underlying JSON state schema. No new app development is required.

**Procedure:**
1.  **Instrumentation:** Extend the MobileGym judging mechanism to log a "State Coverage Vector" for every parallel rollout, tracking which specific state variables (e.g., `app_settings.dark_mode`, `message_list.unread_count`) have been successfully transitioned from their initial values.
2.  **Algorithm Design:** Implement a CPU-tractable curriculum scheduler (e.g., a simple bandit algorithm or entropy-based selector) that runs on the host server. This scheduler will dynamically select the next batch of task parameters for the parallel workers. It will prioritize tasks where the agent's current policy has low "state novelty" (high uncertainty in transition outcomes) or where the current success rate is near a "sweet spot" (e.g., 30-70% success) to maximize learning signal.
3.  **Experiment:** Train two agents using Group Relative Policy Optimization (GRPO) on Qwen3-VL-4B-Instruct: one using MobileGym's original static random sampling, and one using the proposed dynamic State-Guided Curriculum. Both will run for a fixed wall-clock time (e.g., 24 hours) on a single 64-core CPU server to ensure fairness and CPU-tractability.

**Expected Result:** The State-Guided Curriculum agent will achieve the same target success rate (e.g., 50% on the test set) in significantly fewer total environment steps (e.g., 40% reduction) compared to the static baseline. Furthermore, on the real-device transfer subset, the curriculum-trained agent is expected to show higher robustness (lower variance in performance) across apps with complex state dependencies, demonstrating that focusing on state-space coverage yields more generalizable policies than random task sampling.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mobile GUI Agent Research** — Dingbang Wu, Rui Hao, Haiyang Wang, Shuzhe Wu, Han Xiao, Zhenghong Li, Bojiang Zhou, Zheng Ju, Zichen Liu, Lue Fan, Zhaoxiang Zhang. https://arxiv.org/abs/2605.26114.

```bibtex
@article{orig_arxiv_2605_26114,
  title = {MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mobile GUI Agent Research},
  author = {Dingbang Wu and Rui Hao and Haiyang Wang and Shuzhe Wu and Han Xiao and Zhenghong Li and Bojiang Zhou and Zheng Ju and Zichen Liu and Lue Fan and Zhaoxiang Zhang},
  year = {2026},
  eprint = {2605.26114},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.26114},
  url = {https://arxiv.org/abs/2605.26114}
}
```
