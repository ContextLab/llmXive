---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Code as Agent Harness"

## Summary of the prior work
This survey establishes "code as agent harness" as a unified framework where code serves as the operational substrate for agent reasoning, acting, and verification, rather than just a final output. It structures the field into three layers: the interface connecting agents to environments, the mechanisms for planning and feedback control, and the scaling strategies for multi-agent coordination. The paper identifies critical open challenges, particularly regarding regression-free harness improvement and consistent shared state in multi-agent settings.

## Proposed extension
**Research Question:** Can a lightweight, static-analysis-driven "harness diff" mechanism, which isolates and re-validates only the code artifacts modified by an agent's planning step, reduce the computational cost of regression verification by 90% compared to full-environment re-execution while maintaining equivalent safety guarantees? This matters because the survey highlights "regression-free harness improvement" as a bottleneck; solving this via static dependency tracking rather than dynamic re-execution would make long-horizon, multi-agent scientific discovery feasible on standard CPU hardware.

## Methodology sketch
**Data:** A curated dataset of 500 existing agent tasks from the survey's cited repositories (e.g., SWE-bench, AgentBench) containing known code artifacts, execution traces, and failure modes, converted into a text-based dependency graph format.
**Procedure:** Implement a CPU-only prototype that (1) parses the agent's proposed code changes, (2) uses static analysis to identify the minimal set of dependent functions and environment states requiring re-verification, and (3) executes only this subset against the original test suite, comparing the result against a baseline that re-runs the full harness.
**Expected Result:** The static-analysis approach will demonstrate a >90% reduction in verification time and CPU cycles with no increase in false-negative safety errors, proving that harness verification can be decoupled from full execution for efficient scaling.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Code as Agent Harness** — Xuying Ning, Katherine Tieu, Dongqi Fu, Tianxin Wei, Zihao Li, Yuanchen Bei, Jiaru Zou, Mengting Ai, Zhining Liu, Ting-Wei Li, Lingjie Chen, Yanjun Zhao, Ke Yang, Bingxuan Li, Cheng Qian, Gaotang Li, Xiao Lin, Zhichen Zeng, Ruizhong Qiu, Sirui Chen, Yifan Sun, Xiyuan Yang, Ruida Wang, Rui Pan, Chenyuan Yang, Dylan Zhang, Liri Fang, Zikun Cui, Yang Cao, Pan Chen, Dorothy Sun, Ren Chen, Mahesh Srinivasan, Nipun Mathur, Yinglong Xia, Hong Li, Hong Yan, Pan Lu, Lingming Zhang, Tong Zhang, Hanghang Tong, Jingrui He. https://arxiv.org/abs/2605.18747.

```bibtex
@article{orig_arxiv_2605_18747,
  title = {Code as Agent Harness},
  author = {Xuying Ning and Katherine Tieu and Dongqi Fu and Tianxin Wei and Zihao Li and Yuanchen Bei and Jiaru Zou and Mengting Ai and Zhining Liu and Ting-Wei Li and Lingjie Chen and Yanjun Zhao and Ke Yang and Bingxuan Li and Cheng Qian and Gaotang Li and Xiao Lin and Zhichen Zeng and Ruizhong Qiu and Sirui Chen and Yifan Sun and Xiyuan Yang and Ruida Wang and Rui Pan and Chenyuan Yang and Dylan Zhang and Liri Fang and Zikun Cui and Yang Cao and Pan Chen and Dorothy Sun and Ren Chen and Mahesh Srinivasan and Nipun Mathur and Yinglong Xia and Hong Li and Hong Yan and Pan Lu and Lingming Zhang and Tong Zhang and Hanghang Tong and Jingrui He},
  year = {2026},
  eprint = {2605.18747},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.18747},
  url = {https://arxiv.org/abs/2605.18747}
}
```
