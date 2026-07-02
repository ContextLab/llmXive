---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Summary of the prior work
The paper introduces MinT, a managed infrastructure system designed to train and serve millions of Low-Rank Adaptation (LoRA) policies by keeping a massive base model resident while moving only lightweight adapter revisions through the training-serving lifecycle. It achieves scalability along three axes: "Scale Up" to frontier 1T+ parameter architectures, "Scale Down" by minimizing data handoff to sub-1% adapter sizes, and "Scale Out" by decoupling a million-scale policy catalog from active GPU working sets. The system validates that this adapter-centric approach drastically reduces handoff latency and enables concurrent multi-policy training without increasing peak memory overhead.

## Proposed extension
**Research Question:** Can we construct a "LoRA Topology Graph" that predicts the optimal sequence of adapter loadings and base-model context switches to minimize cold-start latency and maximize cache hit rates in a multi-tenant scheduling environment, purely based on adapter rank, parameter overlap, and historical access patterns?

This direction matters because MinT identifies "cold loading" of adapters as a primary bottleneck; while MinT solves the *mechanism* of loading, it does not yet solve the *scheduling intelligence* required to predict which adapters will be needed next, thereby leaving potential for further latency reduction without requiring additional GPU hardware or training runs.

## Methodology sketch
**Data:** We will synthesize a dataset of 10,000 synthetic LoRA adapters with varying ranks (1–256) and random parameter sparsity patterns, paired with a trace of access logs simulating 10^6 requests across different policy "hotspots" derived from the MinT paper's scale-out metrics.

**Procedure:** Using a CPU-only discrete-event simulation (e.g., in Python with SimPy), we will implement three scheduling policies: (1) MinT's current First-Come-First-Served (FCFS) with scheduled cold loading, (2) a Greedy policy that loads the most frequently requested adapters, and (3) our proposed "Topological Lookahead" policy which clusters adapters by parameter overlap (simulating shared weight updates) and pre-fetches clusters based on a Markov chain of request transitions. We will measure the total simulated wall-clock time to serve the request trace and the number of cache evictions.

**Expected Result:** We hypothesize that the Topological Lookahead policy will reduce average cold-start latency by at least 15% and decrease cache eviction rates by 20% compared to FCFS, demonstrating that intelligent, CPU-tractable scheduling of lightweight adapters can significantly enhance the efficiency of the MinT infrastructure without modifying the underlying training algorithms.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **MinT: Managed Infrastructure for Training and Serving Millions of LLMs** — Mind Lab, :, Song Cao, Vic Cao, Andrew Chen, Kaijie Chen, Cleon Cheng, Steven Chiang, Kaixuan Fan, Hera Feng, Huan Feng, Arthur Fu, Jun Gao, Hongquan Gu, Aaron Guan, Nolan Ho, Mutian Hong, Hailee Hou, Peixuan Hua, Charles Huang, Miles Jiang, Nora Jiang, Yuyi Jiang, Qiuyu Jin, Fancy Kong, Andrew Lei, Kyrie Lei, Alexy Li, Lucian Li, Ray Li, Theo Li, Zhihui Li, Jiayi Lin, Kairus Liu, Kieran Liu, Logan Liu, Xiang Liu, Irvine Lu, Maeve Luo, Runze Lv, Pony Ma, Verity Niu, Anson Qiu, Vincent Wang, Rio Yang, Maxwell Yao, Carrie Ye, Regis Ye, Wenlin Ye, Josh Ying, Danney Zeng, Yuhan Zhan, Anya Zhang, Di Zhang, Ruijia Zhang, Sueky Zhang, Ya Zhang, Wei Zhao, Ada Zhou, Changhai Zhou, Yuhua Zhou, Xinyue Zhu, Murphy Zhuang. https://arxiv.org/abs/2605.13779.

```bibtex
@article{orig_arxiv_2605_13779,
  title = {MinT: Managed Infrastructure for Training and Serving Millions of LLMs},
  author = {Mind Lab and : and Song Cao and Vic Cao and Andrew Chen and Kaijie Chen and Cleon Cheng and Steven Chiang and Kaixuan Fan and Hera Feng and Huan Feng and Arthur Fu and Jun Gao and Hongquan Gu and Aaron Guan and Nolan Ho and Mutian Hong and Hailee Hou and Peixuan Hua and Charles Huang and Miles Jiang and Nora Jiang and Yuyi Jiang and Qiuyu Jin and Fancy Kong and Andrew Lei and Kyrie Lei and Alexy Li and Lucian Li and Ray Li and Theo Li and Zhihui Li and Jiayi Lin and Kairus Liu and Kieran Liu and Logan Liu and Xiang Liu and Irvine Lu and Maeve Luo and Runze Lv and Pony Ma and Verity Niu and Anson Qiu and Vincent Wang and Rio Yang and Maxwell Yao and Carrie Ye and Regis Ye and Wenlin Ye and Josh Ying and Danney Zeng and Yuhan Zhan and Anya Zhang and Di Zhang and Ruijia Zhang and Sueky Zhang and Ya Zhang and Wei Zhao and Ada Zhou and Changhai Zhou and Yuhua Zhou and Xinyue Zhu and Murphy Zhuang},
  year = {2026},
  eprint = {2605.13779},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.13779},
  url = {https://arxiv.org/abs/2605.13779}
}
```
