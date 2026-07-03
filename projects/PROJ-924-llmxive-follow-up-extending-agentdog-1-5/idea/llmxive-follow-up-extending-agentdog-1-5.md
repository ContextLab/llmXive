---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "AgentDoG 1.5: A Lightweight and Scalable Alignment Framework for AI Ag"

## Summary of the prior work
The paper introduces AgentDoG 1.5, a lightweight (0.8B–8B parameter) agent safety alignment framework that utilizes a taxonomy-guided data engine and influence-function purification to achieve state-of-the-art safety performance with only ~1k training samples. It updates the safety taxonomy to address risks from modern execution environments like OpenClaw and Codex, demonstrating that small models can effectively serve as real-time, training-free guardrails with significantly reduced deployment overhead.

## Proposed extension
**Research Question:** Can a CPU-tractable, zero-shot "Safety Taxonomy Drift" detector, built solely on the static semantic embeddings of the AgentDoG 1.5 taxonomy, identify emergent agent attack vectors that were not present in the original training data?

This extension matters because AgentDoG 1.5 relies on a fixed, curated taxonomy; as agents evolve, new attack patterns (e.g., novel prompt injection chains or multi-step sandbox escapes) may fall outside this static definition, creating a "blind spot" that traditional fine-tuning cannot address without re-collecting data. By focusing on the semantic distance between new agent behaviors and the original taxonomy centroids, we can create a lightweight, CPU-only early warning system that flags potential safety drift before it causes harm.

## Methodology sketch
*   **Data:** Utilize the open-source AgentDoG 1.5 taxonomy definitions to generate centroid embeddings (using a small, CPU-friendly model like `all-MiniLM-L6-v2`), then collect a fresh, uncurated dataset of 500+ novel agent interaction logs from open-source repositories (e.g., GitHub issues, recent arXiv agent papers) that were published after the AgentDoG 1.5 training cutoff.
*   **Procedure:** Compute the semantic similarity (cosine distance) between the novel interaction logs and the existing taxonomy centroids without any model fine-tuning; define a "Drift Score" for each log based on its distance from the nearest known risk category. Conduct a human evaluation on a stratified sample of high-drift vs. low-drift logs to verify if high-drift logs correspond to genuinely novel or severe safety violations.
*   **Expected Result:** We anticipate that logs with high Drift Scores will correlate significantly with novel attack patterns (e.g., previously unseen jailbreak structures) that standard AgentDoG 1.5 inference might miss or misclassify, thereby validating the "Taxonomy Drift" metric as a CPU-tractable proxy for emerging threats.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **AgentDoG 1.5: A Lightweight and Scalable Alignment Framework for AI Agent Safety and Security** — Dongrui Liu, Yu Li, Zhonghao Yang, Peng Wang, Guanxu Chen, Yuejin Xie, Qinghua Mao, Wanying Qu, Yanxu Zhu, Tianyi Zhou, Leitao Yuan, Zhijie Zheng, Qihao Lin, Yimin Wang, Haoyu Luo, Shuai Shao, Chen Qian, Qingyu Liu, Ling Tang, Ruiyang Qin, Qihan Ren, Junxiao Yang, Kun Wang, Zhiheng Xi, Linfeng Zhang, Ranjie Duan, Bo Zhang, Wenjie Wang, Wen Shen, Qiaosheng Zhang, Yan Teng, Chaochao Lu, Rui Mei, Man Li, Jialing Tao, Xi Lin, Tianhang Zheng, Yong Liu, Quanshi Zhang, Lei Zhu, Xingjun Ma, Junhua Liu, Hui Xue, Xiaoxiang Zuo, Xiangnan He, Chao Shen, Xianglong Liu, Minlie Huang, Jing Shao, Xia Hu. https://arxiv.org/abs/2605.29801.

```bibtex
@article{orig_arxiv_2605_29801,
  title = {AgentDoG 1.5: A Lightweight and Scalable Alignment Framework for AI Agent Safety and Security},
  author = {Dongrui Liu and Yu Li and Zhonghao Yang and Peng Wang and Guanxu Chen and Yuejin Xie and Qinghua Mao and Wanying Qu and Yanxu Zhu and Tianyi Zhou and Leitao Yuan and Zhijie Zheng and Qihao Lin and Yimin Wang and Haoyu Luo and Shuai Shao and Chen Qian and Qingyu Liu and Ling Tang and Ruiyang Qin and Qihan Ren and Junxiao Yang and Kun Wang and Zhiheng Xi and Linfeng Zhang and Ranjie Duan and Bo Zhang and Wenjie Wang and Wen Shen and Qiaosheng Zhang and Yan Teng and Chaochao Lu and Rui Mei and Man Li and Jialing Tao and Xi Lin and Tianhang Zheng and Yong Liu and Quanshi Zhang and Lei Zhu and Xingjun Ma and Junhua Liu and Hui Xue and Xiaoxiang Zuo and Xiangnan He and Chao Shen and Xianglong Liu and Minlie Huang and Jing Shao and Xia Hu},
  year = {2026},
  eprint = {2605.29801},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.29801},
  url = {https://arxiv.org/abs/2605.29801}
}
```
