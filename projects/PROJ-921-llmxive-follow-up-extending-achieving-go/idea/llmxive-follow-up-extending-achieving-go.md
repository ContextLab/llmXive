---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Summary of the prior work
The paper introduces a unified training recipe (reverse-perplexity SFT, two-stage RL, and test-time scaling) to convert a 30B parameter reasoning backbone into SU-01, a model capable of gold-medal-level performance on International Mathematical and Physics Olympiads. The core contribution is demonstrating that rigorous proof-search and self-checking behaviors can be instilled and scaled effectively to handle trajectories exceeding 100K tokens, achieving strong generalization across scientific domains.

## Proposed extension
**Research Question:** Does the "reverse-perplexity" curriculum used to instill self-checking behaviors in SU-01 inadvertently encode a rigid, domain-specific heuristic that degrades performance when applied to open-ended, ill-structured scientific problems lacking verifiable ground-truth answers (e.g., hypothesis generation or experimental design)?

This matters because while the original paper validates success on well-defined Olympiad problems with deterministic solutions, it remains untested whether the model's learned "rigorous" reasoning patterns generalize to the ambiguity of real-world scientific discovery, where the "correct" path is often non-unique or subjective. This hypothesis is falsifiable by comparing performance on standard Olympiad benchmarks versus a newly constructed "Ambiguous Science" benchmark.

## Methodology sketch
**Data:** Construct a new benchmark dataset titled "OpenSci-Reason," comprising 500 real-world, ill-structured scientific prompts (e.g., "Design an experiment to test X given constraints Y and Z") sourced from historical grant proposals and open-ended physics challenges, where answers are evaluated by a panel of human domain experts rather than automated verifiers. Pair this with the existing IMO/IPhO datasets for baseline comparison.

**Procedure:** 
1. Take the pre-trained SU-01 backbone and the final SU-01 model.
2. Evaluate both models on the "OpenSci-Reason" dataset using a CPU-only inference setup (batch size 1, no parallel sampling) to measure reasoning depth and coherence without GPU acceleration.
3. Have three independent human experts rate the generated solutions on a 1-5 scale for "Novelty," "Feasibility," and "Logical Consistency," specifically looking for signs of the model over-applying Olympiad-style rigid proof structures to problems requiring creative exploration.
4. Compare the expert scores against the models' performance on the standard Olympiad benchmarks to identify any negative correlation between rigid self-checking and open-ended creativity.

**Expected Result:** We hypothesize that while SU-01 will maintain high scores on standard Olympiad problems, its performance on "OpenSci-Reason" will drop significantly compared to a baseline model without the reverse-perplexity curriculum, specifically showing a tendency to "hallucinate" false certainties or reject valid but non-standard approaches due to an over-optimized heuristic for verifiable proof steps.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified Scaling** — Yafu Li, Runzhe Zhan, Haoran Zhang, Shunkai Zhang, Yizhuo Li, Zhilin Wang, Jiacheng Chen, Futing Wang, Xuyang Hu, Yuchen Fan, Bangjie Xu, Yucheng Su, Xinmiao Han, Chenxi Li, Haodi Lei, Yufeng Zhao, Zejin Lin, Qianjia Cheng, Tong Zhu, Xiaoye Qu, Ganqu Cui, Peng Ye, Yun Luo, Zhouchen Lin, Yu Qiao, Bowen Zhou, Ning Ding, Yu Cheng. https://arxiv.org/abs/2605.13301.

```bibtex
@article{orig_arxiv_2605_13301,
  title = {Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified Scaling},
  author = {Yafu Li and Runzhe Zhan and Haoran Zhang and Shunkai Zhang and Yizhuo Li and Zhilin Wang and Jiacheng Chen and Futing Wang and Xuyang Hu and Yuchen Fan and Bangjie Xu and Yucheng Su and Xinmiao Han and Chenxi Li and Haodi Lei and Yufeng Zhao and Zejin Lin and Qianjia Cheng and Tong Zhu and Xiaoye Qu and Ganqu Cui and Peng Ye and Yun Luo and Zhouchen Lin and Yu Qiao and Bowen Zhou and Ning Ding and Yu Cheng},
  year = {2026},
  eprint = {2605.13301},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.13301},
  url = {https://arxiv.org/abs/2605.13301}
}
```
