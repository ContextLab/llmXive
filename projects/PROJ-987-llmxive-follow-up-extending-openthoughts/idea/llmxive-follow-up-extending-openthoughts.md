---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "OpenThoughts-Agent: Data Recipes for Agentic Models"

## Summary of the prior work
The OpenThoughts-Agent paper establishes a comprehensive, open data curation pipeline for training agentic language models, systematically ablationing over 100 variables across task generation, mixing, and trajectory filtering to maximize generalization across diverse benchmarks. By fine-tuning Qwen3-32B on 100K curated examples, the authors demonstrate that diverse task sources and multi-turn execution traces significantly outperform single-benchmark or single-source datasets, achieving state-of-the-art performance on SWE-Bench and Terminal-Bench. The work emphasizes that data quality and diversity are more critical than sheer volume, providing a reproducible recipe for building broadly capable agents.

## Proposed extension
**Research Question:** Does the "diversity penalty" observed in agentic SFT (where mixing too many task sources dilutes performance on specific domains) correlate with the *semantic overlap* of the underlying task instructions, and can a lightweight, CPU-tractable clustering algorithm identify an optimal "diversity sweet spot" that maximizes cross-benchmark transfer without requiring expensive GPU-based ablation runs?

**Why it matters:** The original paper found that mixing the Top 4-8 sources worked best but noted diminishing returns and potential domain dilution; a CPU-tractable method to predict this optimal mix based on instruction embeddings would democratize data curation for researchers without massive compute budgets, allowing them to pre-screen data mixes before training.

## Methodology sketch
*   **Data:** Extract the 100K task instructions from the OpenThoughts-Agent release and the 100K trajectories, specifically isolating the prompt text for each task.
*   **Procedure:** 
    1.  Use a CPU-efficient, distilled sentence transformer (e.g., `all-MiniLM-L6-v2`) to generate embeddings for all task instructions.
    2.  Apply hierarchical clustering or HDBSCAN to map the semantic similarity of the 95 original task generation strategies identified in the paper.
    3.  Construct a "similarity graph" where nodes are task sources and edge weights represent semantic overlap.
    4.  Simulate mixing strategies by selecting subsets of sources based on varying graph density thresholds (e.g., "maximally diverse" vs. "maximally cohesive" mixes) and compute a theoretical "diversity score" for each mix without running any model training.
    5.  Validate the hypothesis by comparing these predicted diversity scores against the *actual* benchmark scores reported in the original paper's ablation tables for the corresponding mixes.
*   **Expected Result:** We expect to find a non-linear relationship where mixes with moderate semantic overlap (a "Goldilocks" zone) yield the highest benchmark averages, while highly clustered (low diversity) or highly scattered (high noise) mixes underperform. The resulting clustering metric should strongly correlate ($r > 0.8$) with the observed performance gains, providing a CPU-only heuristic for future data curation.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **OpenThoughts-Agent: Data Recipes for Agentic Models** — Negin Raoof, Richard Zhuang, Marianna Nezhurina, Etash Guha, Atula Tejaswi, Ryan Marten, Charlie F. Ruan, Tyler Griggs, Alexander Glenn Shaw, Hritik Bansal, E. Kelly Buchanan, Artem Gazizov, Reinhard Heckel, Chinmay Hegde, Sankalp Jajee, Daanish Khazi, Emmanouil Koukoumidis, Xiangyi Li, Hange Liu, Shlok Natarajan, Harsh Raj, Nicholas Roberts, Ethan Shen, Nishad Singhi, Michael Siu, Ashima Suvarna, Hanwen Xing, Patrick Yubeaton, Robert Zhang, Leon Liangyu Chen, Xiaokun Chen, Steven Dillmann, Saadia Gabriel, Xunyi Jiang, Anurag Kashyap, Boxuan Li, Yein Park, Minh Pham, Sujay Sanghavi, Lin Shi, Ke Sun, Yixin Wang, Zhiwei Xu, Erica Zhang, Siyan Zhao, Wanjia Zhao, Jenia Jitsev, Alex Dimakis, Benjamin Feuer, Ludwig Schmidt. https://arxiv.org/abs/2606.24855.

```bibtex
@article{orig_arxiv_2606_24855,
  title = {OpenThoughts-Agent: Data Recipes for Agentic Models},
  author = {Negin Raoof and Richard Zhuang and Marianna Nezhurina and Etash Guha and Atula Tejaswi and Ryan Marten and Charlie F. Ruan and Tyler Griggs and Alexander Glenn Shaw and Hritik Bansal and E. Kelly Buchanan and Artem Gazizov and Reinhard Heckel and Chinmay Hegde and Sankalp Jajee and Daanish Khazi and Emmanouil Koukoumidis and Xiangyi Li and Hange Liu and Shlok Natarajan and Harsh Raj and Nicholas Roberts and Ethan Shen and Nishad Singhi and Michael Siu and Ashima Suvarna and Hanwen Xing and Patrick Yubeaton and Robert Zhang and Leon Liangyu Chen and Xiaokun Chen and Steven Dillmann and Saadia Gabriel and Xunyi Jiang and Anurag Kashyap and Boxuan Li and Yein Park and Minh Pham and Sujay Sanghavi and Lin Shi and Ke Sun and Yixin Wang and Zhiwei Xu and Erica Zhang and Siyan Zhao and Wanjia Zhao and Jenia Jitsev and Alex Dimakis and Benjamin Feuer and Ludwig Schmidt},
  year = {2026},
  eprint = {2606.24855},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.24855},
  url = {https://arxiv.org/abs/2606.24855}
}
```
