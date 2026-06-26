---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/254
paper_authors:
  - Fangtai Wu
  - Hailong Guo
  - Shijie Huang
  - Jiayi Song
  - Yubo Huang
  - Mushui Liu
  - Zhao Wang
  - Yunlong Yu
  - Jiaming Liu
  - Ruihua Huang
---

# CollectionLoRA: Collecting 50 Effects in 1 LoRA via Multi-Teacher On-Policy Distillation

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.25378
Paper authors (from arXiv): Fangtai Wu, Hailong Guo, Shijie Huang, Jiayi Song, Yubo Huang, Mushui Liu, Zhao Wang, Yunlong Yu, Jiaming Liu, Ruihua Huang

Submitted by: github-actions[bot]

(Intake from human-submission issue #254.)

## Rejection rationale (2026-06-26)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[f77aa88aa9c8]** Align the deployment overhead percentage in the Introduction (0.5%) with the Experimental results (2% for 150 LoRAs in Table deploy_cost).
- **[2d00aa1fcc42]** Clarify the VSA metric description in the main text to explicitly reference the two-stage process (BCR check + VSA score) described in the Supplementary Material.
- **[4312541dc2b3]** The submission provides only LaTeX source and figures; no training or inference code, data processing scripts, or environment specifications are included. Add a public code repository containing the full implementation (model definition, data loaders, training loops, evaluation scripts) to enable reproducibility.
- **[65cab962b9fc]** Create a clear `README` that lists all dependencies (e.g., PyTorch version, CUDA/cuDNN, external libraries such as `ai-toolkit`, `qwen-image`, `lightx2v`) and provides step‑by‑step instructions for dataset preparation, model training, and inference.
- **[161300c5b3da]** Modularize the codebase: separate model architecture, LoRA handling, and distillation objectives into distinct Python modules (e.g., `models/`, `training/`, `losses/`). Keep each file under ~200 LOC to avoid truncation issues and improve maintainability.
- **[b24d25dc7cef]** Include a `requirements.txt` or `environment.yml` and, preferably, a Dockerfile or Conda environment file to guarantee that reviewers can recreate the exact software stack.
- **[147ec20a6292]** Add unit and integration tests for critical components (LoRA merging, dual‑stream routing logic, loss calculations). Use a CI configuration (e.g., GitHub Actions) to run tests automatically on each commit.
- **[8470184b364f]** Document random seed handling and any nondeterministic operations (e.g., data augmentation, sampling) to ensure that results can be reproduced within a small variance.
- **[2c429a01ac12]** Provide scripts or notebooks that reproduce all tables and figures (e.g., `scripts/run_experiments.py`, `scripts/generate_plots.py`). Include the exact command lines used for each experiment in the supplementary material.
- **[4af11e46d2d7]** Add a dedicated Data Availability and License section describing the effect dataset (including the referenced Effect.xlsx), its source, licensing terms, and provide a persistent download link (e.g., Zenodo DOI).
- **[6c01638492f8]** Include version identifiers (e.g., dataset version number, SHA‑256 checksums) for all training and evaluation data to enable exact reproducibility.
- **[5fc1689aa51b]** Archive all external code and model URLs (e.g., Qwen‑VL‑Max‑Latest API, ai‑toolkit, lightx2v) in a stable repository or archive service and cite the archived links.
- **[967712483934]** Describe how missing or low‑quality image pairs are handled (e.g., filtering criteria, augmentation, imputation) and report any data cleaning steps.
- **[8857b4202014]** The manuscript repeatedly claims that CollectionLoRA “fundamentally resolves” feature‑interference and semantic‑drift issues, yet quantitative results (e.g., Table 1) still show non‑zero Bad Case Rate (0.087) and a slight drop in DINO score compared to the single‑task teacher. Re‑phrase these statements to reflect reduction rather than complete elimination, or provide additional analysis demonstrating that residual interference is negligible.
- **[3e50c44cf056]** The description of the evaluation protocol (Section 4.1) is ambiguous: it mentions 100 diverse test images per category and a total of 5,000 instructions per model, but the math does not add up (2 categories × 100 images = 200 images). Clarify how the 5,000 instructions are generated (e.g., number of prompts per image) to ensure the experimental setup is logically consistent.
- **[11d7a55f0cd8]** In the definition of the Coarse‑to‑Fine Distillation Objective, the loss ℒ_TA‑FM is written as a simple L2 distance to (y − ε), which differs from the standard flow‑matching formulation used elsewhere (ℒ_FM). Explain why this simplification is valid in the multi‑teacher setting, or adjust the notation to avoid an apparent inconsistency between the two loss definitions.
- **[2472073933ee]** Correct the deployment cost claim in the Introduction. Table deploy_cost.tex shows ~2% overhead for 150 LoRAs, not the claimed 0.5%.
- **[8cb40f003860]** Provide statistical significance testing for the claim of surpassing teacher models. The CLIP difference (0.727 vs 0.726) is negligible without error bars.
- **[771b6d4e12cf]** Quantify the zero-shot composition success rate. Currently supported only by qualitative figures (Fig zip_AB_Test.pdf) without metrics across the 50 effects.
- **[2bd1181c6a9f]** Tone down the claim of "fundamentally resolving" feature interference. A BCR of 8.7% indicates mitigation, not resolution.
- **[3c54e5904981]** Supplementary Material (Appendix 10) describes a user study with 10 evaluators but lacks IRB approval or informed consent statements. Add ethical compliance details.
- **[1adc7408fa88]** Training data provenance is unclear ('internally constructed'). Clarify if portraits contain identifiable individuals and confirm consent was obtained.
- **[b1f34e1ab36e]** No discussion of dual-use risks (e.g., deepfakes, misinformation) or safety mitigations (watermarking, detection) for image editing capabilities.
- **[d0a791810f43]** Quantitative tables (e.g., table/main_result.tex, table/ablation.tex) lack standard deviations or confidence intervals. Claims of 'surpassing' baselines require statistical significance testing (e.g., t-tests) to rule out random variance.
- **[42983b359456]** The claim of 'surpassing independent single-task teachers' (Abstract) is weakly supported by Table table/main_result.tex (CLIP 0.727 vs 0.726). Clarify this trade-off (higher VSA but lower DINO) and avoid overgeneralized superiority claims without statistical backing.
- **[68238604e919]** Evaluation relies on MLLM (Qwen-VL-Max-Latest) for VSA/BCR (Supp). The user study (50 samples) is small for validating MLLM correlation. Provide stronger evidence of metric reliability or increase human evaluation sample size.
- **[cd3adc3cf8c1]** Report confidence intervals or standard deviations for all quantitative metrics (CLIP, DreamSim, VSA, BCR) across multiple runs. Single point estimates without variance measures are insufficient for statistical claims.
- **[bb1a4bb83bff]** Add statistical significance testing (e.g., paired t-tests, bootstrap) when comparing methods. Current tables show differences (e.g., CLIP 0.727 vs 0.703) without indicating if they are statistically significant.
- **[705597d3b65b]** Address multiple-comparisons problem. With 6+ metrics tested across multiple baselines, apply appropriate corrections (e.g., Bonferroni, FDR) or justify why they are not needed.
- **[4d94f7d476dd]** Validate MLLM-based metrics (VSA, BCR). Report inter-rater agreement or calibration against human evaluation. The current reliance on Qwen-VL-Max-Latest without reliability metrics is a statistical weakness.
- **[cb8ade4128a3]** Include variance information for user study results (66.2% preference rate). Report confidence intervals and statistical tests (e.g., chi-square) for preference distributions.
- **[cbce89343bc9]** Remove duplicate package imports (axessibility and booktabs) to avoid redundancy.
- **[32e5b30135fa]** Replace the invalid `figure*` placement option `[h]` with `[t]` or `[!ht]`.
- **[9471adc6a0ab]** Use `\caption{...}` instead of `\captionof{figure}{...}` inside `figure*` environments for consistency.
- **[a7d941110440]** Eliminate excessive manual `space{...}` adjustments throughout the manuscript; rely on the class defaults for spacing.
- **[3a98e34bec7c]** Ensure all figure captions end with a period and follow a uniform style (e.g., no leading `	extbf` unless required).
- **[7ad6dd92ac38]** Check table formatting: avoid overfull hboxes caused by `esizebox{	extwidth}{!}`; consider using `\small` or `ootnotesize` instead.
- **[9fb2cecd9c31]** Verify that every `\label` follows its corresponding `\caption` directly to guarantee correct cross‑references.
- **[b28faea51248]** Remove unused packages (`longtable`, `xltabular`, `pdflscape`, `array`, etc.) to keep the preamble clean.
- **[f6fcb85f1d94]** Standardize citation punctuation and style (e.g., ensure a space before citations and consistent use of `\cite{}` throughout).
- **[9a073b89b6e5]** Confirm that all cross‑references to figures and tables use non‑breaking spaces (`Fig.~ef{...}`) and proper capitalization.
- **[3097de11847c]** Correct numerous grammatical errors and improve sentence flow in the abstract (lines 9‑15).
- **[90542f204e1d]** Standardize terminology and abbreviations (e.g., “LoRA”, “effect LoRA”, “Acceleration LoRA”) for consistency throughout the manuscript (see sections 1, 3, 4).
- **[ac6b3f29fab1]** Rewrite overly long and convoluted sentences, especially in the Introduction (lines 31‑45) and Method (lines 120‑150), to enhance readability.
- **[ae52b136cd8b]** Fix punctuation and spacing issues (missing spaces after commas, inconsistent use of hyphens) that appear in multiple tables and figure captions (e.g., Table 1, Figure 2).
- **[2b2417880753]** Ensure uniform formatting of mathematical expressions and symbols (e.g., proper spacing around ‘=’, consistent use of \(	heta\) vs. theta) across equations in Sections 3 and 4.
- **[b981cc83ec2f]** Remove duplicated package imports (axessibility appears twice) and redundant comments in the preamble to keep the LaTeX source clean.
- **[2abbe59cc039]** Edit figure and table captions for conciseness and grammatical correctness; many captions contain fragment sentences or inconsistent capitalization.
- **[cd1e789dce67]** Proofread the Conclusion (lines 200‑210) to eliminate repetitive phrasing and improve logical flow.
