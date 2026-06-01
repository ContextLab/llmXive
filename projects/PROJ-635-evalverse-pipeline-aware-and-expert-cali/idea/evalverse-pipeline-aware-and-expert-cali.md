---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/241
paper_authors:
  - Songlin Yang
  - Haobin Zhong
  - Ruilin Zhang
  - Xiaotong Zhao
  - Shuai Li
  - Kai Zheng
  - Xuyi Yang
  - Zhe Wang
  - Zhenchen Tang
  - Yang Li
  - Bohai Gu
  - Zhengwei Peng
  - Yidan Huang
  - Mengzhou Luo
  - Yihang Bo
  - Dalu Feng
  - Yujia Zhang
  - Juntao Ma
  - Ruiqi Wang
  - Lvmin Zhang
  - Yuwei Guo
  - Frank Guan
  - Maneesh Agrawala
  - Hongbo Fu
  - Alan Zhao
  - Anyi Rao
---

# EvalVerse: Pipeline-Aware and Expert-Calibrated Benchmarking for Professional Cinematic Video Generation

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.23271
Paper authors (from arXiv): Songlin Yang, Haobin Zhong, Ruilin Zhang, Xiaotong Zhao, Shuai Li, Kai Zheng, Xuyi Yang, Zhe Wang, Zhenchen Tang, Yang Li, Bohai Gu, Zhengwei Peng, Yidan Huang, Mengzhou Luo, Yihang Bo, Dalu Feng, Yujia Zhang, Juntao Ma, Ruiqi Wang, Lvmin Zhang, Yuwei Guo, Frank Guan, Maneesh Agrawala, Hongbo Fu, Alan Zhao, Anyi Rao

Submitted by: github-actions[bot]

(Intake from human-submission issue #241.)

## Rejection rationale (2026-06-01)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[efa2360247d8]** Add dataset statistics (total number of test pairs, distribution across dimensions, annotation time/cost per sample) to enable reproducibility of the benchmark construction.
- **[d6a0e43742b7]** Correct or flag statistical results where p-values exceed 0.05 threshold (e.g., Soundscape p=0.1498, Rhythm p=0.0886) as non-significant in correlation table captions.
- **[76b98fe441f7]** Finalize bibliography file - current sample-base.bib appears truncated; verify all cited works have complete entries and remove future-dated references (2026) unless justified.
- **[14edc7929c6f]** Uncomment and include the Human Evaluation Protocol section that is currently commented out in the LaTeX source (lines ~470-520).
- **[14532f9283d6]** Provide explicit code/data release statement with repository URL and license information in the conclusion or appendix.
- **[90c23b14874e]** Citation mismatch: Bib entry 'seedance2' is titled 'Sora2 Video Model' (OpenAI), but text claims 'Seedance 2.0' (Line 278). Correct the citation or the model name to ensure factual accuracy.
- **[3be5c00c48a9]** Statistical overstatement: Table 2 (Line 768) reports p-values > 0.05 for Sound Design (Vocal: 0.1667, Soundscape: 0.1498), yet text claims 'consistently high correlation' and 'robustly aligns' (Line 745). Qualify claims for non-significant dimensions.
- **[8da7eede30df]** Version inconsistency: Bib entry 'gemini' lists 'Gemini 3 Pro' (Line 838), but text specifies 'Gemini 3.1 Pro' (Line 212). Ensure citation details match the text exactly.
- **[471b95d8c32b]** No code artifacts (implementation, tests, dependencies) included in submission; reproducibility cannot be verified. Provide repository link or supplementary code package with requirements.txt, setup.py, and evaluation scripts.
- **[dc0c9cf8a771]** Paper claims 'full reproducibility' but provides no implementation details for VLM fine-tuning pipeline, operator extraction suite, or dataset curation engine. Add code snippets or appendix with architecture diagrams.
- **[7886bdf3c5bd]** Evaluation metrics and correlation tables require code verification. Include unit tests for taxonomy scoring functions and integration tests for end-to-end evaluation pipeline.
- **[f933d0cb0315]** Specify the provenance and copyright status of the 'professional database' used for test pair construction (Section 4, lines 375-400). Current description is vague regarding source and licensing.
- **[3d76b7bedcac]** Include a direct URL to the code and dataset repository. The Supplementary Material section referencing reproducibility details is currently commented out (lines 1340-1345).
- **[ebf1231f6e06]** Provide a formal license statement (e.g., CC-BY, MIT) for the benchmark dataset to ensure legal redistribution and usage.
- **[061b6bf010ac]** Expand caption for fig:taxonomy to explicitly list the 3 stages, 7 aspects, and 18 dimensions for accessibility and self-containment.
- **[bdd512018cad]** Add axis labels and metric descriptions to captions for fig:main_dim_overview, fig:human_evaluation_t2v, and fig:human_evaluation_r2v.
- **[c36727605a19]** Verify color palettes in result figures are colorblind-friendly and distinguishable in grayscale print.
- **[fc75979aacc7]** Define all acronyms at first use (CoT, SFT, VLM, SRCC, PLCC, OOD, MLP, DiT, I2V, V2V, RLHF, GRPO, FVD). Currently, several appear without definition, excluding non-specialist readers.
- **[37ee4543fbd3]** Replace or explain film-industry jargon in Taxonomy section (e.g., "180-degree rule", "volumetric sculpting", "chromaticity", "bokeh"). Provide plain-language glossary or inline definitions.
- **[08c66f56421c]** Simplify technical formulations in Machine Evaluation Suite (Sec. 5). Equations and terms like "perception prior", "Context-Aware Gating", and "Bradley-Terry ranking loss" need plain-English explanations before mathematical notation.
- **[91bd36876730]** Ensure consistent acronym definition. "Chain-of-Thought" appears as "CoT" before full definition in some sections. Define once, then use consistently.
- **[2e5cc23ee851]** Tab. 4 reports p-values > 0.05 for Vocal (0.0513) and Soundscape (0.0513), contradicting the caption's claim of 'consistently high correlation' and 'robust alignment' for these dimensions.
- **[688992fbdfaf]** Fig. 1 claims 196 granular rationales, yet Sec. 6.1 admits dimensions are 'replaced' if beyond VLM perception. Clarify if final scores reflect the full taxonomy or a subset.
- **[a275b2b8929a]** Sec. 6.2 attributes high alignment on abstract dimensions to SFT. Without an ablation (CoT-only vs. SFT), this causal claim is unsupported by the presented evidence.
- **[b4dac2917a50]** Add IRB approval statement and details on informed consent/compensation for human annotators in Section 6.1.
- **[1a4b1ab48313]** Clarify copyright licensing and usage rights for the professional film database used in Dataset Curation (Section 5).
- **[36d66d64597e]** Include a Broader Impact or Safety section discussing dual-use risks (e.g., deepfakes) and mitigation strategies.
- **[e4209d108da0]** Report exact number of human-annotated video samples (N) and Inter-Annotator Agreement (IAA) metrics (e.g., Krippendorff's alpha) for the 34 experts in Section 5.1 to validate ground truth reliability.
- **[0280c9b5fa69]** Provide confidence intervals for correlation coefficients in Table 7 and address statistical power concerns given N=11 models for the human-machine alignment analysis.
- **[c1b4facf31db]** Include an ablation study isolating the contribution of CoT reasoning versus SFT knowledge injection to validate the causal claim of the calibration mechanism in Section 6.
- **[9d439f51b4ae]** Remove all Chinese comments (e.g., lines 60, 110, 350) and redundant package declarations (e.g., duplicate booktabs/etoc) to ensure clean compilation.
- **[51a779f1bc99]** Correct grammatical errors in the Abstract: change 'broaden' to 'broadens' and 'evaluator agent' to 'evaluator agents' for subject-verb agreement.
- **[4369bf14f364]** Fix LaTeX label formatting: remove spaces in references like 'sec: vlm fine_tuning' (Section 5) to prevent compilation warnings.
- **[b1aff10f39f5]** Remove duplicate or commented-out sections (e.g., duplicate Related Work and Table definitions) to avoid confusion and label conflicts.
