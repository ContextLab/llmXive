---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Dockerless: Environment-Free Program Verifier for Coding Agents"

## Summary of the prior work
The paper introduces Dockerless, an environment-free agentic verifier that evaluates code patch correctness by actively exploring repository files via parallel sub-agents rather than executing unit tests in Docker containers. By generating verification questions and gathering evidence from the codebase, it achieves high accuracy in filtering training trajectories and providing rewards for reinforcement learning, enabling a fully environment-free post-training pipeline for coding agents.

## Proposed extension
**Research Question:** Can the agentic verification process be accelerated by 10x and made fully CPU-tractable by replacing the parallel sub-agent exploration with a static, graph-based code analysis pipeline that pre-computes repository topology, without sacrificing verifier accuracy?
**Why it matters:** While Dockerless eliminates Docker overhead, its reliance on spawning multiple LLM-driven sub-agents per verification task remains computationally expensive and latency-bound; a static analysis approach would enable verification on low-cost, CPU-only infrastructure, making the pipeline viable for massive-scale, real-time coding agent deployment.

## Methodology sketch
**Data:** We will use the same SWE-Gym and Multi-SWE-RL datasets (3.7k issues) as the prior work, but additionally extract static control-flow and call-graph data for all repositories using lightweight, CPU-only tools like `pycg` (for Python) or `clang-query` (for C++), storing these as JSON graphs.
**Procedure:** We will design a new "Static-Dockerless" verifier that takes the issue, patches, and the pre-computed static graph as input. Instead of spawning LLM sub-agents to run shell commands (grep, find), a single, smaller LLM will traverse the static graph to answer the verification questions (e.g., "Does this function call chain reach the patched code?"). We will train this verifier using the same rejection sampling strategy as the original paper, comparing its verdicts against the ground-truth test execution results.
**Expected result:** We anticipate that the Static-Dockerless verifier will achieve within 2-3 AUC points of the original Dockerless verifier while reducing inference latency by an order of magnitude and eliminating the need for any GPU resources during the verification phase, proving that deep repository grounding can be achieved via static analysis alone.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Dockerless: Environment-Free Program Verifier for Coding Agents** — Wenhao Zeng, Yuling Shi, Xiaodong Gu, Chao Hu, Chaofan Wang, Yuhao Cui, Hongting Zhou, Mengnan Qi, Jianqiao Wangni, Zhaojian Yu, Shuzheng Gao, Kai Cai, Shilin He. https://arxiv.org/abs/2606.28436.

```bibtex
@article{orig_arxiv_2606_28436,
  title = {Dockerless: Environment-Free Program Verifier for Coding Agents},
  author = {Wenhao Zeng and Yuling Shi and Xiaodong Gu and Chao Hu and Chaofan Wang and Yuhao Cui and Hongting Zhou and Mengnan Qi and Jianqiao Wangni and Zhaojian Yu and Shuzheng Gao and Kai Cai and Shilin He},
  year = {2026},
  eprint = {2606.28436},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.28436},
  url = {https://arxiv.org/abs/2606.28436}
}
```
