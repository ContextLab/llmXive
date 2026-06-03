---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/251
paper_authors:
  - Dongrui Liu
  - Yu Li
  - Zhonghao Yang
  - Peng Wang
  - Guanxu Chen
  - Yuejin Xie
  - Qinghua Mao
  - Wanying Qu
  - Yanxu Zhu
  - Tianyi Zhou
  - Leitao Yuan
  - Zhijie Zheng
  - Qihao Lin
  - Yimin Wang
  - Haoyu Luo
  - Shuai Shao
  - Chen Qian
  - Qingyu Liu
  - Ling Tang
  - Ruiyang Qin
  - Qihan Ren
  - Junxiao Yang
  - Kun Wang
  - Zhiheng Xi
  - Linfeng Zhang
  - Ranjie Duan
  - Bo Zhang
  - Wenjie Wang
  - Wen Shen
  - Qiaosheng Zhang
  - Yan Teng
  - Chaochao Lu
  - Rui Mei
  - Man Li
  - Jialing Tao
  - Xi Lin
  - Tianhang Zheng
  - Yong Liu
  - Quanshi Zhang
  - Lei Zhu
  - Xingjun Ma
  - Junhua Liu
  - Hui Xue
  - Xiaoxiang Zuo
  - Xiangnan He
  - Chao Shen
  - Xianglong Liu
  - Minlie Huang
  - Jing Shao
  - Xia Hu
---

# AgentDoG 1.5: A Lightweight and Scalable Alignment Framework for AI Agent Safety and Security

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.29801
Paper authors (from arXiv): Dongrui Liu, Yu Li, Zhonghao Yang, Peng Wang, Guanxu Chen, Yuejin Xie, Qinghua Mao, Wanying Qu, Yanxu Zhu, Tianyi Zhou, Leitao Yuan, Zhijie Zheng, Qihao Lin, Yimin Wang, Haoyu Luo, Shuai Shao, Chen Qian, Qingyu Liu, Ling Tang, Ruiyang Qin, Qihan Ren, Junxiao Yang, Kun Wang, Zhiheng Xi, Linfeng Zhang, Ranjie Duan, Bo Zhang, Wenjie Wang, Wen Shen, Qiaosheng Zhang, Yan Teng, Chaochao Lu, Rui Mei, Man Li, Jialing Tao, Xi Lin, Tianhang Zheng, Yong Liu, Quanshi Zhang, Lei Zhu, Xingjun Ma, Junhua Liu, Hui Xue, Xiaoxiang Zuo, Xiangnan He, Chao Shen, Xianglong Liu, Minlie Huang, Jing Shao, Xia Hu

Submitted by: github-actions[bot]

(Intake from human-submission issue #251.)

## Rejection rationale (2026-06-03)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[0bf5bb62ad2c]** Section 4.2.1 claims AgentDoG-0.8B achieves 75.7% accuracy on R-Judge, but Table 1 does not include the 0.8B variant. Add this row to the table or remove the specific claim from the text to ensure verifiability.
- **[4962d9ffec04]** Inconsistent model naming: Text refers to 'AgentDoG-4B-U' (Sec 4.2.1) while Table 1 uses 'AgentDoG 1.5-4B-U'. Standardize nomenclature across the manuscript to avoid confusion regarding model versions.
- **[fdd692d80a0f]** Verify that all cited 2025-2026 works (e.g., GPT-5.4, Gemini-3.1-Pro) are included in the bibliography with complete metadata. Ensure these references are accessible to reviewers for external validation.
- **[a16a7f72bd0d]** The code repository is not provided in the ingestion context. Please include the GitHub repository contents (training scripts, data pipelines, tests) to enable a code quality review.
- **[08b1ff1009dc]** Claims regarding reproducibility and lightweight deployment (Section 5) cannot be verified without access to the Dockerfile, requirements.txt, and evaluation harness scripts.
- **[5de489bde417]** Explicitly state the license (e.g., MIT, Apache 2.0) for all released models and datasets in the Abstract or Introduction.
- **[d893ab8ce185]** Provide a datasheet or detailed provenance description for the ~1k training samples, including source distribution and filtering thresholds.
- **[c3fae74bccd9]** Add version tags or commit hashes for external datasets (e.g., ATBench) to ensure long-term reproducibility and prevent link rot.
- **[9308c85cabbd]** Add accessible alt text (e.g., \\alttext) to all figures for screen reader compatibility.
- **[1f05ee256fa2]** Convert raster images (PNG/JPG) to vector formats (PDF/SVG) for print legibility.
- **[3cdcedae8d0c]** Remove unused figure assets (e.g., pipeline_v*.pdf) to reduce clutter and confusion.
- **[79112679611e]** Ensure TikZ source code is fully included for reproducibility and axis verification.
- **[7610cf69efe2]** Define acronyms SFT, RL, and MCP in the Abstract. SFT and RL appear in the first paragraph without expansion, and MCP servers are mentioned without defining the protocol.
- **[e8eb17af63a3]** Define the term ATBench at first use in the Abstract or Introduction. Currently it appears as a proper noun without expansion (e.g., Agent Tool Bench).
- **[4a9bf1da512d]** Define XAI (Explainable AI) in Section 5 title or first paragraph. The term is used as a standalone acronym.
- **[db5bafa1cdfe]** Define MoE (Mixture of Experts) in Figure 3 caption or related text. The caption references MoE models without defining the architecture type.
- **[cbf843ab90b2]** Simplify the phrase 'influence-function purification' in Section 4.1. This is dense statistical jargon that may exclude non-specialist readers; consider 'data selection using influence functions' or similar.
- **[695469983a9a]** Qualify the 'state-of-the-art' claim in the Conclusion to specify 'among open-source guard models', as Table 1 shows GPT-5.4 outperforms AgentDoG-4B on R-Judge and ATBench.
- **[c3f99761e1c4]** Remove or substantiate the specific claim of '1/100 memory overhead of SWE-Bench' in the Introduction, as no comparative data for SWE-Bench is provided in the paper.
- **[aa60b3abbcb6]** Adjust the 'Extensive experimental results' claim in the Abstract to reflect the scale of the benchmarks (e.g., R-Judge n=569), avoiding overstatement of statistical robustness.
- **[5e7c40c1c894]** Clarify the access policy for the released dataset containing harmful trajectories (Abstract). Explicitly state if redaction or licensing restrictions apply to prevent misuse of attack vectors (e.g., prompt injection payloads in Appendix e001).
- **[323087103fa7]** Add a discussion on the adversarial robustness of AgentDoG itself. Can the guardrail be bypassed via prompt injection? (Section 5).
- **[8919dfe4cc2c]** Include a statement on ethical guidelines followed for synthetic data generation, even if IRB is not required (Section 4).
- **[97eb2d92c82f]** Report standard deviations or confidence intervals for all metrics in Tables 1-4 to establish statistical significance.
- **[a4c04de6c991]** Provide an ablation study on training data size (e.g., 1k vs 10k) to justify the claim that 1k samples are sufficient for SOTA performance.
- **[03ceae9178f2]** Verify baseline models (GPT-5.4, Gemini-3) are publicly available or provide independent evaluation logs, as 2026-dated baselines hinder reproducibility.
- **[2a01ab19f378]** Report statistical significance (p-values, confidence intervals, or bootstrap uncertainty) for all benchmark comparisons. Single-run point estimates without variance measures are insufficient for claiming SOTA performance.
- **[ba0f9a6c1274]** Address multiple comparisons problem. The paper compares 15+ models across 6+ benchmarks without correction (e.g., Bonferroni, FDR). This inflates Type I error rates for claimed improvements.
- **[9a0c37e7ac37]** Provide run-to-run variance. All results appear to be single-seed runs. Report mean ± std across ≥3 random seeds for all training-based claims, especially for the 1k-sample training regime.
- **[cb6b7b15ad3f]** Justify small sample sizes in guardrail evaluation (e.g., 16 trajectories for ClawSafety, 35 for CIK-Bench in Table 5). Report confidence intervals for these percentages (e.g., 25.00% from 4/16 has ~95% CI of ~8-49% using Wilson interval).
- **[60b06747ac99]** Define missing colors (lightred, HardBlue, injred, defgreen, occustom, codcustom) in preamble to prevent compilation errors.
- **[1f0bca32d375]** Define missing commands (\ocnote, \codnote, \occustomcell) or replace with standard text to ensure LaTeX hygiene.
- **[0e6ef88acca9]** Reorder sections so Introduction precedes Related Work and Conclusion; Evaluation currently appears after Conclusion in e003.
- **[525348d28fd9]** Resolve duplicate label 'tab:main_results' defined in both e000 and e003 to avoid cross-reference errors.
- **[9828f76bdcb5]** Remove \section{Authors} from body (e003) as author info is already in preamble; fix \footnotetext without \footnotemark in e003.
- **[28c170b96791]** Section ordering is incoherent: Introduction (e002) appears after Evaluation (e002) and Conclusion (e003) appears before a second Evaluation section (e003). Reorder to standard flow.
- **[75a8ceedc975]** Duplicate label 'tab:main_results' found in e000 and e003. This will cause LaTeX reference errors and broken cross-references.
- **[6e0a25ce5d84]** Grammar error: 'We hypothesize this primarily to two reasons' (e002) should be 'for two reasons'.
- **[63c88bbd65dc]** Grammar error: 'Temperature set to 0' (e002) lacks a verb. Use 'Temperature was set to 0'.
- **[b22d74f755fa]** Informal phrasing: 'results not reported' (e002) should be 'thus, results were not reported'.
