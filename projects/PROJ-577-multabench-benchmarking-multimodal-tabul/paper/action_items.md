# Automated-review action items — MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that 'ConTextTab set the SOTA for the CARTE benchmark' (Section 2, Related Work) is not supported by the provided bibliography. The citation \cite{spinaci_contexttab_2025} is missing from neurips2026.bib. Without this source, the specific performance claim on CARTE cannot be verified.
- **[writing]** The paper claims MulTaBench is the 'largest image-tabular benchmarking effort to date' (Abstract, Section 1). While the authors cite \cite{lu_mug_2023} and \cite{tang_bag_2024} as smaller predecessors, the bibliography lacks entries for these specific benchmark papers (only generic or unrelated entries exist for similar years). The claim of 'largest' requires explicit citation of the competing benchmarks' sizes to be verifiable.
- **[writing]** In Section 3, the paper states that 'TAR consistently outperforms frozen embeddings across all new models' (Figure 4 caption). However, Table 1 in the Appendix (tab:win_rate) shows TabICLv2 has a win rate of only 55.0% for Image tasks. The text 'consistently outperforms' is an overstatement given that the model wins in only slightly more than half the cases, which is not statistically 'consistent' in a strong sense.
- **[writing]** The claim that 'ConTextTab... struggles on MulTaBench' (Section 2) is supported by Figure 4, but the specific comparison to CARTE performance relies on the missing \cite{spinaci_contexttab_2025} citation. The argument that MulTaBench targets a 'fundamentally different' problem is plausible but the specific evidence linking ConTextTab's CARTE success to its MulTaBench failure is weakened by the missing reference.

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[science]** The paper claims to release code and data (S1, S5) but provides no repository structure, dependency list (requirements.txt/pyproject.toml), or reproducibility script (e.g., run_curation.sh). Without a manifest of dependencies (specific versions of PyTorch, LoRA, DINOv3, e5, LightGBM, etc.) and a clear entry point, the benchmark cannot be reproduced from scratch.
- **[science]** The curation pipeline involves fine-tuning encoders (LoRA) and running 5 tabular learners across 40 datasets with 5 seeds. The paper mentions 'cost-effectiveness' but lacks a documented workflow for parallelization, checkpointing, or resuming interrupted runs. A missing or non-atomic checkpointing strategy risks data loss and makes the 32K token output budget for implementation tasks unmanageable if the code is monolithic.
- **[science]** The appendix details hyperparameters (LR, batch size, LoRA rank) but does not specify the random seed management strategy for the entire pipeline (data loading, model init, training). Reproducibility requires a single seed controller or a documented seed propagation mechanism across all 5 learners and 5 seeds per dataset.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[science]** The paper presents a significant benchmarking effort, MulTaBench, but raises critical concerns regarding data provenance, version control, and the handling of missing data that threaten the reproducibility of the results. First, the provenance and link rot issue is severe. While the authors propose uploading the benchmark to Kaggle to address the "fragility of external image links" (Section 4, Appendix A.2), the manuscript currently relies on a mix of unstable URLs (Figshare, various Kaggle data

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1 (curation_pipeline.pdf) lacks axis labels and units. The flowchart is clear, but the caption does not specify the performance metric (AUC/R2) or the threshold values used for the 'Joint Signal' and 'Task-awareness' gates. Add a small inset or legend defining the decision boundaries.
- **[writing]** Figure 2 (curation_example.pdf) and Figure 3 (text_pool_joint_tar.pdf) use normalized scores without explicitly stating the normalization range or the baseline used for min-max scaling in the axis labels. The y-axis should be labeled 'Normalized Score (0-1)' or similar to ensure print legibility and clarity.
- **[writing]** Figure 5 (attention_main.pdf) and the appendix attention maps (e.g., fig:attn_chexpert_appendix) are critical for the 'Task-awareness' claim but lack scale bars or resolution indicators. The 'Frozen' vs 'Target-Aware' heatmaps are small; ensure the colorbar is distinct and the legend clearly maps colors to attention weights (0-1) for print reproduction.
- **[writing]** Figure 4 (leaderboard.pdf) and Figures 6-8 (encoder_scale, pca) use error bars (95% CI). The caption must explicitly state if the error bars represent standard deviation or standard error of the mean, and the y-axis label should clarify 'Normalized Score' to avoid ambiguity with raw metrics.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The paper suffers from significant jargon overuse, creating a barrier for readers outside the immediate sub-field of tabular foundation models. The most critical issue is the introduction and repeated use of the coined term "Target-Aware Representations (TAR)" without a clear, plain-English definition at the point of first introduction in the Abstract and Section 1. This term is central to the paper's contribution but is presented as a given concept rather than a defined property. In Section 1,

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent argument for the necessity of Target-Aware Representations (TAR) in Multimodal Tabular Learning (MMTL), supported by a rigorous curation pipeline. However, there are minor logical inconsistencies between the stated definitions and the formal criteria, as well as slight overgeneralizations in the causal claims regarding model capacity. First, there is a discrepancy in the definition of "Joint Signal." In Section 3.1, the text states that joint performance must exceed

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims that extend beyond the immediate scope of the provided evidence, particularly regarding the uniqueness of the benchmark and the absolute necessity of the proposed method. First, the claim in the Abstract and Introduction that MulTaBench constitutes the "largest image-tabular benchmarking effort to date" is an overreach. While the paper introduces 20 image-tabular datasets, Section 3.2 ("Image-Tabular Curation") acknowledges that existing benchmarks like MuG and BAG

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper includes medical datasets (CheXpert, CBIS-DDSM, Glaucoma) and social data (Hateful Meme, Toxicity). While the authors claim data is de-identified, the Checklist (Item 11) and Section 7 lack a specific discussion on potential harms if these models are deployed in high-stakes settings (e.g., misdiagnosis, biased hiring). Explicitly address negative societal impacts and mitigation strategies as required by NeurIPS ethics guidelines.
- **[writing]** The 'Hateful Meme' and 'Jigsaw Toxicity' datasets often contain user-generated content that may include personally identifiable information (PII) or sensitive attributes not fully scrubbed. The paper must explicitly state the specific de-identification protocols used for these datasets and confirm compliance with the original data providers' terms of service regarding secondary research use.
- **[writing]** The curation pipeline involves fine-tuning encoders on the target variable (Section 3.2). For datasets involving sensitive attributes (e.g., gender in 'Celeb Attractiveness', race in 'Jigsaw'), the paper should discuss whether the Target-Aware Representations (TAR) might inadvertently learn and amplify biases present in the labels, and if any fairness audits were conducted.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The curation pipeline uses a fixed threshold (delta=0.001) for acceptance. The paper must report the distribution of gains (Delta_Joint and Delta_Awareness) across the 56 text and 16 image candidates to demonstrate that the 0.001 threshold is not arbitrary and that the selected datasets are not just marginally passing. Without this distribution, the robustness of the benchmark selection is unclear.
- **[science]** The regression target discretization (20 bins) for TAR finetuning is a significant methodological choice that alters the learning objective. The paper must provide evidence (e.g., a sensitivity analysis or ablation) showing that this discretization does not artificially inflate the TAR gains compared to a direct regression finetuning baseline, or explain why the discretization is necessary for stability without introducing bias.
- **[science]** The claim that TAR gains generalize across 'several tabular learners' relies on 5 curation models and 7 additional models. However, the additional models (e.g., TabICLv2, ConTextTab) show significantly lower win rates (55-73%) compared to GBDTs (80-93%). The paper should explicitly discuss this variance and whether the 'generalization' claim holds for all model families or is primarily driven by GBDTs and specific TFMs.
- **[science]** The curation process involves subsampling up to 10,000 examples. For datasets with N < 10,000 (e.g., CS:GO Skins, N=956), the full set is used, but for larger ones, a subset is used. The paper must clarify if the 5 random seeds account for the subsampling variance and if the performance gains are consistent across different random subsamples, or if the results are sensitive to the specific 10k subset chosen.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The paper reports 95% confidence intervals (CIs) for performance metrics (e.g., Fig 4, Fig 5) but fails to specify the statistical method used for their calculation (e.g., bootstrap, t-distribution, or standard error of the mean). Given the use of 5 random seeds, the method for aggregating variance across seeds and datasets must be explicitly defined to ensure reproducibility.
- **[science]** The curation pipeline (Sec 3.2) applies a binary acceptance threshold (delta=0.001) to model performance gains. The paper does not report statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) to verify that these gains are distinguishable from random noise, raising concerns about the robustness of the dataset selection criteria.
- **[science]** In Appendix A.1, regression targets are discretized into 20 bins for the TAR finetuning step. The paper does not provide a statistical justification for this specific bin count or analyze how this discretization affects the variance and bias of the final regression metrics compared to direct regression finetuning.
- **[science]** The 'No PCA' ablation (Appendix A.4) excludes datasets with >5 text features and limits analysis to two learners. The paper does not discuss the statistical power of this reduced sample or whether the exclusion criteria introduce selection bias that invalidates the generalizability of the 'no artifact' claim.

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** Figure/Caption Consistency: The Acknowledgments section includes two grant logos (ERC and ELLIOT) embedded via minipages without a figure environment or caption. NeurIPS requires all figures to be numbered and captioned. Either remove these images or convert them to a proper figure environment with a caption (e.g., "Figure X: Funding sources").
- **[writing]** Table Formatting: In Appendix Table 1 (tab:multabench_datasets), the sample size column uses comma-separated numbers (e.g., "1,696"), which may cause rendering inconsistencies in the final PDF. Standard LaTeX tables typically avoid commas in numbers unless explicitly formatted. Consider using a consistent number format (e.g., "1696" or a custom macro for thousands separators).
- **[writing]** Figure Referencing: The appendix contains wide figures (figure*) that are referenced in the text. Ensure that the figure numbering sequence is correct and that the text references match the actual figure labels. For example, Figure 2 and Figure 3 in the appendix should be properly numbered and referenced as "Figure 2" and "Figure 3" in the text, not as "Figure 1" or "Figure 2" if they are the first figures in the appendix.
- **[writing]** Caption Placement: In Section 5, Figure 4 (fig:leaderboard) is a wide figure with the caption placed below the image. Verify that this placement is consistent with NeurIPS style guidelines, which typically require captions to be placed below figures. These issues are minor and can be resolved with straightforward edits to the LaTeX source. The overall structure and formatting of the paper are excellent, and these adjustments will ensure full compliance with NeurIPS submission requirements.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5, the phrase 'assuring that the image representations are central' should be corrected to 'ensuring' for better academic tone and precision.
- **[writing]** In Section 6, the sentence 'We note that GBDTs exhibit the most substantial gains' is slightly informal. Consider rephrasing to 'We observe that GBDTs exhibit the most substantial gains' or 'Our analysis indicates that GBDTs exhibit...'.
- **[writing]** In Section 7, the phrase 'differing ourselves from existing MMTL benchmarks' is awkward. Suggest 'distinguishing our work from existing MMTL benchmarks' or 'setting our work apart from existing MMTL benchmarks'.
- **[writing]** In the Appendix, Section 'Text-Tabular Curation', the phrase 'datasets which were unavailable due to improper hosting' is slightly vague. Consider 'datasets that were inaccessible due to hosting issues' for clarity.
- **[writing]** Throughout the paper, ensure consistent capitalization of 'Target-Aware Representations' (TAR). While often capitalized, check if it should be lowercase when not at the start of a sentence or in specific contexts like 'target-aware representations'.
