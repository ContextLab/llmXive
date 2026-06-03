---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/252
paper_authors:
  - Qiuyue Wang
  - Mingsheng Li
  - Jian Guan
  - Jinhui Ye
  - Sicheng Xie
  - Yitao Liu
  - Junhao Chen
  - Zhixuan Liang
  - Jie Zhang
  - Xintong Hu
  - Xuhong Huang
  - Pei Lin
  - Junyang Lin
  - Dayiheng Liu
  - Shuai Bai
  - Jingren Zhou
  - Jiazhao Zhang
  - Haoqi Yuan
  - Gengze Zhou
  - Hang Yin
  - Ye Wang
  - Yiyang Huang
  - Zixing Lei
  - Wujian Peng
  - Delin Chen
  - Yingming Zheng
  - Jingyang Fan
  - Xianwei Zhuang
  - Xin Zhou
  - Haoyang Li
  - Anzhe Chen
  - Tong Zhang
  - Xuejing Liu
  - Yuchong Sun
  - Ruizhe Chen
  - Zhaohai Li
  - Chenxu Lü
  - Zhibo Yang
  - Tao Yu
  - Xionghui Chen
---

# Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.30280
Paper authors (from arXiv): Qiuyue Wang, Mingsheng Li, Jian Guan, Jinhui Ye, Sicheng Xie, Yitao Liu, Junhao Chen, Zhixuan Liang, Jie Zhang, Xintong Hu, Xuhong Huang, Pei Lin, Junyang Lin, Dayiheng Liu, Shuai Bai, Jingren Zhou, Jiazhao Zhang, Haoqi Yuan, Gengze Zhou, Hang Yin, Ye Wang, Yiyang Huang, Zixing Lei, Wujian Peng, Delin Chen, Yingming Zheng, Jingyang Fan, Xianwei Zhuang, Xin Zhou, Haoyang Li, Anzhe Chen, Tong Zhang, Xuejing Liu, Yuchong Sun, Ruizhe Chen, Zhaohai Li, Chenxu Lü, Zhibo Yang, Tao Yu, Xionghui Chen

Submitted by: github-actions[bot]

(Intake from human-submission issue #252.)

## Rejection rationale (2026-06-03)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[2c4fd819aaa8]** Verify all bibliography citations have valid publication dates and DOIs; remove or correct any references with future-dated years (2025-2026)
- **[bf1fb5bf579e]** Provide evidence that Qwen3.5-4B backbone exists and is publicly documented with proper citation
- **[e6977627ad82]** Ensure all benchmark results (LIBERO, DOMINO, VLN-CE) can be independently reproduced with shared code and model weights
- **[e4cc8923c4ad]** Clarify whether arXiv ID 2605.30280 corresponds to actual submission date or is a placeholder
- **[28f41b5d194f]** Remove or replace citations to works that do not exist or are dated in the future (e.g., qwen2.5vl, team2025gemini, bai2025qwen3, black2024pi0, black2025pi05, intelligence2026pi). Claims that rely on these references are currently unsupported.
- **[033f1721d848]** Verify that all cited sources actually contain the statements they are used to support. For example, the citation to \citep{Qwen2-VL} should be checked to ensure it backs the claim about state‑of‑the‑art vision‑language performance.
- **[d636a0ea5d1a]** Adjust language that overstates evidence. Phrases like “state‑of‑the‑art performance” or “significantly outperforms” should be qualified with explicit comparative numbers and citations to the relevant benchmark results.
- **[db9b2bb389e2]** Provide proper citations for benchmark results reported in tables (e.g., LIBERO, Simpler‑WidowX, RoboTwin‑Easy/Hard, R2R, RxR). If the numbers are from the authors' own experiments, cite the corresponding section or appendix rather than external papers.
- **[6072cc91546d]** Clarify the source of the “97.9 % on LIBERO” and similar numbers—are they reproduced from prior work or obtained in this study? Add a footnote or reference to the experimental protocol.
- **[dbe12dedad32]** Ensure that any claim about “zero‑shot” performance on DOMINO is backed by a citation to the DOMINO benchmark paper and that the reported numbers are directly comparable (same evaluation protocol).
- **[2a152b595c76]** Include a direct link to the public code repository (e.g., GitHub) in the Abstract or Introduction to enable reproducibility.
- **[a9b823280e29]** Add a reproducibility appendix or section detailing exact hyperparameters, random seeds, and compute infrastructure specifications.
- **[06930ae2d424]** Specify the software stack (e.g., PyTorch version, CUDA version) and provide dependency files (requirements.txt) in the repository.
- **[7ecf0d476405]** Provide a comprehensive table listing the license type and version for every dataset used in the pretraining mixture (e.g., Ego4D, EPIC-KITCHENS, BridgeData).
- **[8ed31b917c02]** Replace unstable blog post URLs (e.g., RoboInF blog) with persistent identifiers (DOIs) or archived versions to prevent link rot.
- **[30aa186ff10c]** Include a data card or datasheet for the Qwen-VLA pretraining corpus detailing composition, filtering criteria, and known biases.
- **[e6d3dd6caf01]** Add explicit \cref{fig:overview}, \cref{fig:recipe}, and \cref{fig:task_overview} references in the main text to ensure consistent cross-referencing and discoverability.
- **[46400100bc1b]** Replace figures/realgrid_4x4.jpg with a vector format (PDF/EPS) to ensure resolution independence and legibility in print.
- **[fd38b1a3a7ed]** Verify axis labels, tick marks, and legends in figures/vl_abl.pdf meet the conference template's minimum font size requirement (typically 10pt).
- **[eea618a51431]** Define 'DiT' as 'Diffusion Transformer' at first use in Section 2.2.
- **[a3387b40ca21]** Define 'AdaLN' and 'RoPE' at first use in Section 2.2.
- **[890367de1a39]** Expand 'SE(3)' to 'Special Euclidean group' in Section 2.2.1 for non-specialists.
- **[2c34e5fbaf76]** Define 'VQA' and 'DoF' at first use in Sections 4.1.1 and 4.2.2 respectively.
- **[54ec21dd07e9]** Temper the claim of 'zero-shot success rate on DOMINO dynamic manipulation' (Abstract, Sec 5.1.4). Clarify if pretraining data included dynamic object interactions, as the text states 'without any dynamic-manipulation fine-tuning' but does not explicitly detail dynamic priors in the data section.
- **[4a71ab20f1d7]** Qualify the 'across robot embodiments' generalization claim (Abstract, Intro). Real-world validation is limited to ALOHA; emphasize that cross-embodiment claims rely heavily on simulation data to avoid overclaiming physical hardware robustness.
- **[85e689d5c80c]** Avoid relying solely on average OOD success (76.9%) to characterize robustness (Abstract, Table 3). Highlight the lower Position Generalization score (53.8%) to provide a balanced view of limitations.
- **[79f91be6d00e]** Report number of trials, seeds, and variance (std dev/confidence intervals) for all success rate metrics in Tables 1-5.
- **[c66a5f856105]** Clarify the exact evaluation protocol for real-world ALOHA tasks (e.g., N trials per task, randomization details).
- **[4b613c84b756]** Justify the comparison between zero-shot Qwen-VLA and fine-tuned baselines in DOMINO (Table 5) regarding task sampling and seeds.
- **[6c8c784ad918]** Provide measures of variability (e.g., standard deviations, confidence intervals) for all reported success rates in Tables 1‑5 and any other quantitative results.
- **[2be3464c8b42]** Perform and report statistical significance tests (e.g., paired t‑tests, Wilcoxon signed‑rank tests) when comparing Qwen‑VLA variants against baselines to substantiate claims of superiority.
- **[6e1acb80a1ab]** Address multiple‑comparison issues arising from evaluating on many benchmarks (LIBERO, RoboCasa‑GR1, Simpler‑WidowX, RoboTwin, R2R, RxR, DOMINO, OOD tasks). Apply appropriate corrections (e.g., Bonferroni, Holm) or clearly state that each metric is considered independently.
- **[e6dd659cfb96]** Report the number of random seeds used for each experiment and include seed values; provide variance across seeds to demonstrate robustness.
- **[89c47031e0e6]** Detail the hyper‑parameter search strategy for PPO (learning rates, clipping ε, GAE λ) and include sensitivity analyses to show that performance is not contingent on a single lucky configuration.
- **[d84d3910b895]** Include a reproducibility checklist: exact dataset splits, preprocessing pipelines, and versioned code for the DiT action decoder and RLinf framework.
- **[15f6963392ed]** Remove duplicate package imports (booktabs, array, enumitem, makecell, graphicx, longtable, wrapfig, pifont, fontenc, inputenc) to prevent compilation warnings.
- **[f1f9827969f2]** Add missing \\end{document} and \\bibliography{colm2024_conference} commands to ensure the document compiles and references render.
- **[0dd29171164b]** Standardize figure placement specifiers (e.g., use [htbp] consistently) and reduce reliance on \\resizebox for tables to maintain font consistency.
- **[4606707ec9a5]** Remove the corrupted text string '($} 	extlangle image	extrangle 	exttt{<|}	extit{tag}	exttt{ end|>}' found in the Experiments section under 'Projection design for heterogeneous embodiments'. This breaks readability and appears to be a rendering artifact or placeholder.
- **[b544a89fe90c]** Ensure consistent spelling throughout (e.g., 'generalize' vs 'generalise', 'initialized' vs 'initialised', 'summarizes' vs 'summarises'). The paper currently mixes British and American English.
- **[66a0e8185965]** Remove inline LaTeX comments (e.g., '% This mixture is designed...') from the main text body before final submission to ensure clean compilation and reading.
- **[78c5db2b8b43]** Consolidate redundant package imports (e.g., 'booktabs', 'enumitem', 'array', 'graphicx' are imported multiple times) to improve code hygiene.
