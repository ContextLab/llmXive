---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Scaling the Horizon, Not the Parameters: Reaching Trillion-Parameter P"

## Summary of the prior work
The paper introduces Agents-A1, a 35B Mixture-of-Experts model that achieves performance comparable to trillion-parameter models by scaling the "agent horizon" rather than parameter count, utilizing a 45K-token trajectory infrastructure and a three-stage multi-teacher distillation recipe. It demonstrates that connecting external knowledge, actions, and verifiers allows a smaller model to master complex, long-horizon tasks across six heterogeneous domains. The core innovation lies in shifting the scaling law focus from model size to the depth and diversity of agentic reasoning trajectories.

## Proposed extension
How does the *semantic density* (information per token) of a 45K-token agentic trajectory correlate with the final task success rate, and can we identify a "critical compression threshold" where increasing trajectory length beyond a certain point yields diminishing returns or active performance degradation for a 35B agent? This matters because the original work assumes "longer is better" for scaling the horizon, but without quantifying the efficiency of information retention, we risk training on noisy, redundant data that wastes compute and potentially confuses the model's reasoning chain.

## Methodology sketch
We will curate a subset of the existing 45K-token trajectories and systematically generate synthetic variations by applying rule-based token pruning (removing repetitive tool calls or verbose self-reflection) and token expansion (inserting synthetic "thought bubbles" or redundant checks) to create a spectrum of trajectory lengths (5K, 15K, 30K, 60K) while controlling for total semantic content. Using a CPU-tractable evaluation protocol, we will run these modified trajectories through the frozen Agents-A1 model (in inference mode) on a held-out set of 500 tasks from the SEAL-0 and FrontierScience-Olympiad benchmarks, measuring success rates and token-level entropy. We expect to observe an inverted-U curve where performance peaks at a specific density (e.g., 20K tokens with high semantic compression) and drops significantly when trajectories become too sparse (losing context) or too verbose (suffering from "context dilution"), providing a concrete guideline for optimal horizon scaling.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Scaling the Horizon, Not the Parameters: Reaching Trillion-Parameter Performance with a 35B Agent** — Lei Bai, Zongsheng Cao, Yang Chen, Zhiyao Cui, Shangheng Du, Yue Fan, Shiyang Feng, Zijie Guo, Haonan He, Liang He, Xiaohan He, Shuyue Hu, Yusong Hu, Songtao Huang, Yichen Jiang, Hao Li, Xin Li, Dahua Lin, Weihao Lin, Fenghua Ling, Dongrui Liu, Zhuo Liu, Runmin Ma, Chunjiang Mu, Haoyang Peng, Tianshuo Peng, Jinxin Shi, Luohe Shi, Boyuan Sun, Zelin Tan, Shengji Tang, Qianyi Wang, Yiming Wu, Yi Xie, Xiangchao Yan, Jingqi Ye, Peng Ye, Fangchen Yu, Jiakang Yuan, Bihao Zhan, Bo Zhang, Chen Zhang, Shufei Zhang, Shuaiyu Zhang, Wenlong Zhang, Yiqun Zhang, Junpeng Zhao, Zhijie Zhong, Bowen Zhou, Yuhao Zhou. https://arxiv.org/abs/2606.30616.

```bibtex
@article{orig_arxiv_2606_30616,
  title = {Scaling the Horizon, Not the Parameters: Reaching Trillion-Parameter Performance with a 35B Agent},
  author = {Lei Bai and Zongsheng Cao and Yang Chen and Zhiyao Cui and Shangheng Du and Yue Fan and Shiyang Feng and Zijie Guo and Haonan He and Liang He and Xiaohan He and Shuyue Hu and Yusong Hu and Songtao Huang and Yichen Jiang and Hao Li and Xin Li and Dahua Lin and Weihao Lin and Fenghua Ling and Dongrui Liu and Zhuo Liu and Runmin Ma and Chunjiang Mu and Haoyang Peng and Tianshuo Peng and Jinxin Shi and Luohe Shi and Boyuan Sun and Zelin Tan and Shengji Tang and Qianyi Wang and Yiming Wu and Yi Xie and Xiangchao Yan and Jingqi Ye and Peng Ye and Fangchen Yu and Jiakang Yuan and Bihao Zhan and Bo Zhang and Chen Zhang and Shufei Zhang and Shuaiyu Zhang and Wenlong Zhang and Yiqun Zhang and Junpeng Zhao and Zhijie Zhong and Bowen Zhou and Yuhao Zhou},
  year = {2026},
  eprint = {2606.30616},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.30616},
  url = {https://arxiv.org/abs/2606.30616}
}
```
