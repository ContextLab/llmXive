---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/340
paper_authors:
  - Jianing Zhang
  - Chenhao Zheng
  - Yajun Yang
  - Max Argus
  - Rustin Soraki
  - Winson Han
  - Taira Anderson
  - Chun-Liang Li
  - Shuo Liu
  - Jiafei Duan
  - Zhongzheng Ren
  - Jieyu Zhang
  - Ranjay Krishna
---

# MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.18558
Paper authors (from arXiv): Jianing Zhang, Chenhao Zheng, Yajun Yang, Max Argus, Rustin Soraki, Winson Han, Taira Anderson, Chun-Liang Li, Shuo Liu, Jiafei Duan, Zhongzheng Ren, Jieyu Zhang, Ranjay Krishna

Submitted by: github-actions[bot]

(Intake from human-submission issue #340.)

## Rejection rationale (2026-06-24)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[0d46097e65b3]** Several citations (e.g., nvidia2025cosmos, bruce2024genie, soraki2026objectforesightpredictingfuture3d) refer to works dated in the future (2025, 2026). Verify that these references correspond to publicly available preprints or published papers; otherwise the claim of outperforming these baselines is unsupported.
- **[d004a0e52801]** The claim that MolmoMotion‑1M is the largest action‑described, object‑grounded 3D point trajectory dataset is made without external citation. Provide a brief comparative table or citation to prior datasets to substantiate this claim.
- **[a04c8937eb10]** Provide a public code repository containing the full training, inference, and data‑annotation pipelines (e.g., MolmoMotion‑1M generation, model architecture, and downstream transfer scripts).
- **[2f52934bad4c]** Refactor large monolithic source files (e.g., the 600+‑line model implementation in the appendix) into smaller, logically‑grouped modules (data loading, model definition, training loop, evaluation) to stay within typical token limits and improve readability.
- **[b1c2e34f8d1b]** Add a clear dependency manifest (requirements.txt or environment.yml) with exact version pins for all third‑party libraries (e.g., Molmo2, ViPE, AllTracker, SAM 3, DiT).
- **[4f58d6a86dd9]** Include reproducibility instructions: data download scripts, preprocessing steps, random seed settings, and hardware requirements for each experiment (pretraining, fine‑tuning, robotics transfer, video generation).
- **[79ac030b5a86]** Supply a suite of unit and integration tests for critical components (e.g., 3D lifting, trajectory filtering, flow‑matching loss) and CI configuration to ensure they run automatically.
- **[1e62054cd774]** Document the expected input/output formats for each module (e.g., JSON/YAML spec for query points, coordinate serialization, prompt format) and provide example files.
- **[772e91aa3330]** Add an explicit licensing statement for the MolmoMotion-1M dataset and the PointMotionBench benchmark (e.g., CC‑BY, Apache 2.0) and include the same license in the HuggingFace repository README.
- **[57077c4423be]** Provide a clear provenance description for the source videos used in MolmoMotion-1M, including copyright status, any required permissions, and how copyrighted material is handled.
- **[bfd67d3bd8ac]** Document the handling of missing or occluded points in the annotation pipeline (e.g., percentage of frames/points filtered, imputation strategy) and report these statistics in the paper or appendix.
- **[85ed82fec44e]** Introduce version identifiers (e.g., v1.0, git tags) for both the dataset releases and the codebase, and reference them in the manuscript to ensure reproducibility.
- **[899b704b7e1e]** Add persistent identifiers (DOIs or permanent URLs) for the external resources (HuggingFace collections, GitHub repo, technical website) to mitigate future link rot.
- **[9f1473981a5f]** Add explicit axis labels (including units, e.g., meters for trajectory plots) to all quantitative figures such as Fig. 4 (verb diversity), Fig. 5 (object diversity), Fig. 7 (pick‑and‑place success), and Fig. 8 (DROID L2 error).
- **[9b7fa6030df8]** Indicate the log‑scale nature of the bar charts (Fig. 4, Fig. 5) directly on the y‑axis or in the caption to avoid misinterpretation.
- **[2813fa615879]** Replace or supplement current color palettes with a color‑blind‑friendly scheme (e.g., using ColorBrewer palettes) for all multi‑color plots, especially the bar charts and the qualitative trajectory visualizations (Fig. 6, Fig. 10).
- **[5c41439c1880]** Provide concise alt‑text descriptions for each figure (e.g., “Fig 1: schematic of goal‑conditioned 3D point motion forecasting pipeline”) to improve accessibility for readers using screen readers.
- **[a665bf0d49e3]** Increase line thickness and marker size in 3D trajectory visualizations (Fig. 6, Fig. 10, Fig. 12) so that details remain legible when printed at typical journal column widths.
- **[7509f2ca33da]** Ensure that all figures are saved at a minimum of 300 dpi resolution and that vector graphics (PDF) are used for line‑drawings to maintain clarity in print.
- **[50535905ef8f]** Verify that figure captions fully describe the content, including what each color or symbol represents, and reference any abbreviations used within the figure.
- **[9827a682409a]** Define all acronyms on first use (e.g., VLM, LM, AR, FM, RoPE, DiT, LLM, MAD, MSE, bf16, fp32, FSDP2, CLIP, VBench).
- **[a46031fc67a5]** Replace or explain highly technical jargon such as “autoregressive coordinate prediction”, “flow‑matching‑based trajectory generation”, “anchor‑relative coordinate parameterization”, “cross‑attention”, “self‑attention”, “tokenization”, “context window”, “gradient‑accumulation micro‑batches”, etc., with clearer language or brief parenthetical explanations.
- **[a500d77fe43b]** Add a concise plain‑English description of the “flow‑matching” objective and its inference procedure, avoiding dense mathematical notation for readers unfamiliar with diffusion‑style training.
- **[131fddfeec2d]** Explain domain‑specific tools (AllTracker, ViPE, SAM 3, SAM 2) when first mentioned, indicating they are point‑tracking, depth‑estimation, or segmentation systems.
- **[542a0dd95b02]** Simplify the description of the data‑annotation pipeline (Section 3.2) by breaking long sentences into bullet points and avoiding nested technical terms that obscure the overall process.
- **[16938990f3ae]** The paper claims that expressing future coordinates in a world frame anchored at the camera at time t₀ makes predictions independent of future camera motion. This is logically inconsistent because if the camera moves after t₀, the anchored world frame will no longer align with the true world, breaking the claimed view‑stability. Clarify the assumption that the camera is static after t₀ or modify the formulation to handle moving cameras.
- **[691f2060df5f]** The statement that flow‑matching is better suited for capturing motion uncertainty is not substantiated with any uncertainty‑focused evaluation (e.g., multimodal metrics or diversity scores). Provide experiments that demonstrate the advantage of the stochastic model, or temper the claim.
- **[2f26ea108dc7]** In the abstract and introduction, the paper asserts that MolmoMotion “significantly outperforms all existing motion prediction baselines” without qualifying that the comparison is limited to the specific metrics and datasets presented. Add a precise qualifier (e.g., “on the PointMotionBench benchmark under ADE/FDE/PWT metrics”) to avoid overgeneralization.
- **[12e1a9633113]** Temper the claim that the learned 3D motion prior “transfers well” to downstream robotics; the current evidence is limited to simulation and a small finetuning study on DROID without closed‑loop real‑world robot experiments.
- **[17487b1181be]** Clarify that the performance advantage over baselines is demonstrated on the specific benchmark (enchmarkname{}) and does not necessarily generalize to all possible 3D motion forecasting tasks or datasets.
- **[8d32a33adc13]** Provide a more precise justification for the statement that MolmoMotion‑1M is “the largest” corpus of its kind, possibly by citing comparable datasets or acknowledging the lack of a formal size comparison.
- **[7d5a9d2d305a]** Add a discussion of failure cases or scenarios where the model’s predictions are inaccurate (e.g., highly deformable objects, severe occlusions), and explain how these limitations affect downstream applications.
- **[71bdecff420e]** Include quantitative ablations that isolate the contribution of language conditioning versus visual cues on the benchmark, to support the claim that language instructions substantially improve forecasting.
- **[9f6227d3c399]** Add a dedicated Ethics & Safety section that discusses consent for the source videos, privacy safeguards for any identifiable humans, and the potential dual‑use of 3D motion forecasting (e.g., surveillance, weaponizable robot planning).
- **[8221c18fe9ba]** Provide a clear data‑usage statement confirming that all internet videos used in MolmoMotion‑1M were publicly available under licenses that permit redistribution and that any personal data was removed or blurred; if not, obtain appropriate permissions or exclude such clips.
- **[eff5071234bf]** Document any IRB or equivalent ethical review that was performed for the annotation pipeline, especially when human subjects appear in the source videos, and describe steps taken to anonymize or de‑identify individuals.
- **[8c661df541d4]** Consider adding a usage‑policy clause in the model’s repository (e.g., on HuggingFace) that restricts deployment in high‑risk domains without additional safety evaluation.
- **[ae2dca22f43a]** Quantify the noise introduced by the automatic 3‑D annotation pipeline (e.g., by reporting per‑clip error distributions or a validation set with ground‑truth motion captured by a motion‑capture system) and assess how this noise propagates to the benchmark results.
- **[d873230b3697]** Provide statistical significance testing (e.g., paired bootstrap or permutation tests) for the reported improvements over baselines on the PointMotionBench benchmark, including confidence intervals for ADE/FDE/PWT.
- **[a033a12873cc]** Add an additional held‑out evaluation set that is sourced from a completely different domain (e.g., indoor robotics videos not seen in the pre‑training corpora) to demonstrate that the model’s performance generalizes beyond the three benchmark sources.
- **[e8e9dd854676]** Report the variance across multiple random seeds for the training of both the autoregressive and flow‑matching variants, to show that the observed gains are robust to initialization and data shuffling.
- **[ec52775a93ed]** Include an ablation that directly compares trajectories obtained from the automatic pipeline against manually annotated trajectories on a small subset, to validate that the pipeline does not systematically bias motion direction or magnitude.
- **[5fd129431e2b]** Clarify the exact split of training/validation/test clips in PointMotionBench (e.g., number of clips per category and per motion type) and provide a table of per‑category performance to rule out that gains are driven by a few easy categories.
- **[dd1bf379e512]** Document the random seed and any nondeterministic operations (e.g., K‑means clustering for query point selection) used during data generation and model training to enable exact replication.
- **[9e8d57503fbe]** Provide measures of variability (e.g., standard deviation, confidence intervals) for all reported metrics (ADE, FDE, PWT, robot success rates, video quality scores) and perform appropriate statistical significance tests when comparing models.
- **[1f4dd308d6a5]** Describe the random seed handling, data split procedures, and any hyper‑parameter search strategy to ensure reproducibility of the experiments.
- **[87349a679341]** Address the multiple‑comparisons problem arising from evaluating many baselines across three datasets; apply corrections (e.g., Bonferroni, Holm) or clearly justify why they are unnecessary.
- **[86bf740a5215]** Clarify the best‑of‑5 evaluation protocol: specify whether metrics are averaged over the five runs per sample and report the distribution of those runs.
- **[5124f84e55d2]** Release the code and exact training/evaluation scripts (including versioned dependencies) to allow independent verification of the statistical results.
- **[d2a98cc28814]** Abstract contains a grammatical slip (e.g., “is able to accurately predicts” in line 1 of sections/0_abstract.tex). Revise to “is able to accurately predict”.
- **[52090c60d0ba]** Several sentences are overly long and hard to follow, especially in the Introduction (lines 12‑20 of sections/1_introduction.tex). Break them into shorter clauses and add commas for readability.
- **[3e1f6c930b46]** Inconsistent hyphenation of “goal‑conditioned” vs “goal-conditioned” throughout the manuscript (e.g., sections/1_introduction.tex vs sections/3_method.tex). Standardize the term.
- **[1103ab4e4555]** Figure captions sometimes repeat information already in the main text (e.g., Fig. 1 caption repeats the task description). Make captions concise and focus on what the figure illustrates.
- **[75e15d58cd96]** The “Limitations” section (sections/6_conclusion.tex) contains a run‑on sentence and a missing article (“the model’s understanding of fine‑grained structure”). Rewrite for clarity.
- **[cbc5c2380714]** Citation formatting is inconsistent; some citations lack a space before the opening bracket (e.g., “\cite{gibson2014ecological}” vs “\cite{gibson2014ecological}”). Ensure uniform LaTeX citation style.
- **[dfd1b4823735]** The transition between the method description and the data pipeline (Sec. 3 → Sec. 4) is abrupt. Add a brief bridging paragraph to guide the reader.
- **[18b8f4fc5fd4]** Use parallel structure when listing model variants (e.g., “autoregressive variant” vs “flow‑matching variant” in Table 1). Align phrasing for consistency.
- **[00923e86916c]** Some abbreviations are introduced without definition (e.g., “PWT” in Table 1). Define them at first use in the main text.
- **[c85f66fa1fb2]** The conclusion mixes future work with limitations; separate these into distinct paragraphs for better logical flow.
