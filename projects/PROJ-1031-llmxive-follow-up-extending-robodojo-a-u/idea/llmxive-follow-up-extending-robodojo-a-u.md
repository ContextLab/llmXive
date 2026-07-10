---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluatio"

## Summary of the prior work
RoboDojo introduces a unified benchmark combining 42 simulation tasks and 18 real-world tasks to systematically evaluate generalist robot manipulation policies across five dimensions: generalization, memory, precision, long-horizon execution, and open-vocabulary instruction following. It bridges the sim-to-real gap by providing a reproducible real-world evaluation system (RoboDojo-RealEval) and a standardized integration framework (XPolicyLab) that allows 30 diverse policies to be tested across both domains with minimal adaptation. The work establishes a public leaderboard to track policy performance and highlights current limitations in handling complex, long-horizon physical interactions.

## Proposed extension
**Research Question:** To what extent does a lightweight, CPU-tractable "symbolic-simulation" abstraction layer improve the long-horizon planning success rate of generalist policies in RoboDojo's real-world tasks compared to end-to-end learned sim-to-real transfer, without requiring GPU-accelerated physics engines?

This direction matters because current RoboDojo evaluations rely heavily on GPU-intensive physics simulators (Isaac Sim) for training and testing, which limits scalability and excludes researchers with limited hardware. By exploring a symbolic abstraction that strips away continuous physics details while preserving topological task constraints, we can determine if "logical correctness" is the primary bottleneck for long-horizon tasks, potentially enabling high-throughput evaluation on standard CPUs.

## Methodology sketch
**Data:** Utilize the existing 18 real-world RoboDojo tasks and their corresponding 42 simulation counterparts, but replace the Isaac Sim physics backend with a custom, lightweight Python-based symbolic simulator (e.g., using a grid-world or PDDL-like state representation) that models object affordances and connectivity rather than continuous dynamics.

**Procedure:** 
1. Implement a "Symbolic-Dojo" adapter that maps the visual observations from the real-world tasks (or high-level semantic embeddings) into discrete state spaces compatible with the CPU-based symbolic simulator.
2. Train a hierarchical policy where a high-level symbolic planner (running on CPU) generates a sequence of sub-goals based on the abstract task, and a low-level controller (pre-trained on RoboDojo) executes these sub-goals in the real world.
3. Evaluate this hybrid approach against the baseline end-to-end policies from the original RoboDojo leaderboard on the same 18 real-world tasks, measuring success rate, time-to-solution, and compute overhead (FLOPs/Time).

**Expected Result:** We hypothesize that the symbolic-planning extension will achieve comparable or superior success rates on long-horizon tasks (e.g., multi-step assembly) by reducing the complexity of the decision space, while operating entirely on CPU resources with a 10x-100x reduction in computational cost compared to the original GPU-based Isaac Sim evaluations.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies** — Tianxing Chen, Yue Chen, Zixuan Li, Junyuan Tang, Kailun Su, Haoran Lu, Weijie Wan, Baijun Chen, Songling Liu, Haowen Yan, Honghao Su, Zhiyang Dou, Kaixuan Wang, Dandan Zhang, Yunze Liu, Yan Qin, Qiwei Liang, Qiwei Wu, Zijian Lin, Wenwei Lin, Yuran Wang, Minghua He, Tianshu Wu, Ruihai Wu, Jingquan Zhou, Kai-Chong Lei, Haibao Yu, Yuanfeng Ji, Weiyang Jin, Guanyu Lin, Xiaofan Li, Qi Xiong, Renjing Xu, Zhongyu Li, Wenhao Chai, Enze Xie, Ziwei Wang, Yao Mu, Hao Dong, Wojciech Matusik, Mingyu Ding, Wenbo Ding, Ping Luo, Masayoshi Tomizuka. https://arxiv.org/abs/2607.04434.

```bibtex
@article{orig_arxiv_2607_04434,
  title = {RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies},
  author = {Tianxing Chen and Yue Chen and Zixuan Li and Junyuan Tang and Kailun Su and Haoran Lu and Weijie Wan and Baijun Chen and Songling Liu and Haowen Yan and Honghao Su and Zhiyang Dou and Kaixuan Wang and Dandan Zhang and Yunze Liu and Yan Qin and Qiwei Liang and Qiwei Wu and Zijian Lin and Wenwei Lin and Yuran Wang and Minghua He and Tianshu Wu and Ruihai Wu and Jingquan Zhou and Kai-Chong Lei and Haibao Yu and Yuanfeng Ji and Weiyang Jin and Guanyu Lin and Xiaofan Li and Qi Xiong and Renjing Xu and Zhongyu Li and Wenhao Chai and Enze Xie and Ziwei Wang and Yao Mu and Hao Dong and Wojciech Matusik and Mingyu Ding and Wenbo Ding and Ping Luo and Masayoshi Tomizuka},
  year = {2026},
  eprint = {2607.04434},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.04434},
  url = {https://arxiv.org/abs/2607.04434}
}
```
