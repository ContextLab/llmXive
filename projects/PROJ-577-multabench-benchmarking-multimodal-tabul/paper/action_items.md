# Automated-review action items — MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The review focuses strictly on the accuracy of factual claims and the validity of their supporting citations. The manuscript makes several strong claims regarding the state of the art and the properties of existing benchmarks. In the Introduction, the authors state that "ConTextTab set the SOTA for the CARTE benchmark" citing [spinaci_contexttab_2025]. A check of the provided bibliography reveals a potential mismatch or missing entry for this specific citation key (the .bib file lists arazi_tabs

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The right panel (MulTaBench) lacks a visible Y-axis with tick labels, making it impossible to read specific normalized scores or compare magnitudes against the left panel.
- **[writing]** Figure 1: The caption refers to 'Structured' and 'Unstructured' conditions, but the legend uses 'Unimodal Structured' and 'Unimodal Unstructured'; the legend should be updated to match the caption for consistency.
- **[science]** Figure 2: The legend defines 'E2E' (purple) and 'Curation' (star), but the bars for AG-MM, TabSTAR, and ConTextTab are purple without stars, while others are blue/orange with stars. The caption does not explain the criteria for a model to be classified as 'E2E' versus 'Frozen/TAR', nor does it explain why some models lack the 'Curation' star despite being in the benchmark.
- **[writing]** Figure 2: The legend box is positioned over the data bars in panel (a), partially obscuring the error bars and the 'Curation' star for the 'TabST' and 'RealMLP' rows, reducing readability.
- **[science]** Figure 3: The legend defines 'Curation' with a star symbol, but the star appears on the left side of the bars (indicating a specific model variant or condition) rather than as a separate data point or error bar, making the legend definition misleading.
- **[writing]** Figure 3: The caption claims to show 'Normalized scores over MulTaBench' but does not specify the normalization baseline (e.g., 0 = random, 1 = oracle) or the metric used (e.g., R2, MSE), which is essential for interpreting the 'Normalized Score' axis.
- **[science]** Figure 4: The left panel's y-axis is logarithmic (10^3, 10^4), but the bar heights for 'Image Small' and 'Text Small' appear visually inconsistent with the log scale (e.g., the 'Image Small' Frozen bar is near the bottom, but on a log scale starting at 10^2, it should be much higher relative to the 10^3 line).
- **[writing]** Figure 4: The x-axis labels ('Image Small', 'Image Large', etc.) are split across two lines, which is acceptable, but the spacing between the 'Image' and 'Text' groups is not clearly demarcated by the dashed line's position relative to the labels, potentially causing confusion about which category the line separates.
- **[science]** Figure 5: The y-axis labels (LightGBM, CatBoost, etc.) represent tabular learners, but the figure title and caption claim to analyze 'Encoder Scale' (Small vs. Large). The figure actually compares different tabular models using different encoders, rather than analyzing the scale of a single encoder across models, creating a disconnect between the visual data and the stated analysis goal.
- **[writing]** Figure 5: The x-axis label 'Normalized Score' is missing; while the axis ticks are present, the unit/metric name is not explicitly labeled on the axis itself.
- **[science]** Figure 6: The x-axis is labeled 'Normalized Score' and ranges from 0 to 1, but the caption states scores are 'normalized within each model'. This typically implies centering (mean=0) or scaling to a [-1, 1] range, yet the data is strictly positive and bounded by 1, suggesting a different normalization (e.g., min-max) that is not explicitly defined in the caption.
- **[writing]** Figure 6: The y-axis labels (LightGBM, CatBoost, etc.) are positioned to the left of the plot area but lack a clear axis title (e.g., 'Model') to formally identify the categorical variable.
- **[writing]** Figure 7: The legend title 'PCA / mode' is semantically confusing because the entries describe both PCA status ('No PCA') and dimensionality ('30 dims'); the title should be changed to 'Configuration' or 'Method' to accurately reflect the content.
- **[writing]** Figure 7: The x-axis labels ('CatBoost', 'LightGBM') are centered between the two groups of bars, which is acceptable, but the spacing is tight; ensuring the labels are clearly associated with their respective clusters would improve readability.
- **[science]** Figure 8: The image is a raw chest X-ray without any visible attention map overlay (e.g., heatmap or gradient visualization) to support the caption's claim that 'attention shifts from diffused edges to the lung'.
- **[writing]** Figure 8: The caption references 'attention shifts' but the image lacks a legend or color scale to interpret the attention intensity or distribution.
- **[fatal]** Figure 9: The image displays a puppy, but the caption claims 'Attention isolates the cat ears and the dog's eyes.' The image contains no cat, making the caption factually incorrect and the figure's scientific claim unverifiable.
- **[science]** Figure 9: The image is a standard photograph with no visible attention map overlay (e.g., heatmap or saliency mask), failing to visually demonstrate the 'Attention Maps' described in the title and caption.
- **[fatal]** Figure 10: The rendered image is a standard fundus photograph of a retina, but the caption describes 'Attention Maps' comparing 'Frozen' vs 'TAR' methods. The image lacks the necessary visual overlays (e.g., heatmaps) or side-by-side panels to demonstrate the claimed attention shifts.
- **[science]** Figure 10: The caption claims to show 'Frozen attention scatters randomly' and 'TAR converges,' but the image contains no visual indicators (such as color gradients or masks) to represent these attention distributions, making the scientific claim unverifiable from the figure.
- **[science]** Figure 11: The image displays a single photograph of a person without any overlaid attention heatmaps or visualizations. This contradicts the caption's claim that it shows 'Attention Maps' comparing 'Frozen' and 'TAR' conditions, rendering the figure unable to support its scientific claim.
- **[science]** Figure 11: The filename in the caption ('idx31_label1_original.png') suggests a raw input image, but the figure is cited to demonstrate model behavior (attention focus). The figure fails to visualize the actual data (attention weights) described in the text.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and technical shorthand that impede accessibility for a broader machine learning audience. The most critical issue is the introduction of the core concept "Target-Aware Representations" (TAR) in the Abstract without defining the acronym. The term "TAR" is then used repeatedly throughout the paper (e.g., Abstract, Section 1, Section 3, Section 4) without ever being explicitly defined as an acronym in the text, forcing the reader to infer t

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a logically coherent argument for the necessity of Target-Aware Representations (TAR) in Multimodal Tabular Learning (MMTL), supported by a rigorous curation pipeline. The central premise—that frozen embeddings lose task-specific signal—is well-motivated by the theoretical limitations of general-purpose encoders and empirically validated by the curation results. The conclusion that MulTaBench is a necessary benchmark for developing future Multimodal Tabular Foundation Models f

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that MulTaBench is the 'largest image-tabular benchmarking effort to date' (Abstract, Sec 1) is an overreach. The paper acknowledges existing benchmarks like MuG and BAG but lacks a quantitative comparison of dataset counts or total samples to substantiate the 'largest' superlative. Please add a comparative table or explicit count comparison.
- **[writing]** The assertion that 'no existing model has successfully maintained SOTA performance on tabular tasks while learning TAR' (Sec 1) is too absolute. The paper cites TabSTAR's limitations but lacks a direct, controlled experiment comparing a SOTA model with TAR against one without on a unified benchmark. This strong negative claim requires stronger evidence or softer phrasing (e.g., 'current models struggle to...').
- **[writing]** The conclusion that 'TAR significantly outperforms frozen embeddings even at the larger scale' (Sec 5) overgeneralizes from specific encoders (DINO-v3, e5). The paper does not rule out that other architectures might inherently capture task-relevant signals without fine-tuning. Qualify the claim to reflect it holds for the specific family of encoders evaluated.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper includes medical datasets (CheXpert, CBIS-DDSM, Glaucoma) but lacks a specific discussion on the ethical risks of deploying models trained on these benchmarks in clinical settings, particularly regarding false negatives in diagnosis.
- **[writing]** The 'Celeb Attractiveness' dataset relies on crowd-annotated attractiveness labels. The manuscript should explicitly address the ethical implications of using such subjective, potentially biased human annotations for training automated systems.
- **[writing]** While the authors state they use de-identified data, the 'Celeb Attractiveness' and 'PetFinder' datasets contain images of identifiable individuals or animals. A brief statement confirming compliance with the original data licenses regarding public release and potential re-identification risks is needed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The curation pipeline entangles 'Task-awareness' with the specific LoRA finetuning algorithm. Datasets are selected because TAR works, creating a circular bias. Clarify if this property is intrinsic to the data or an artifact of the specific encoder/finetuning strategy used for selection.
- **[science]** Discretizing regression targets into 20 bins for TAR finetuning may distort the signal. Provide evidence that this preserves fine-grained information or compare against direct regression finetuning to rule out this confounding variable.
- **[science]** Non-curation models (e.g., TabICLv2, ConTextTab) show significantly lower win rates (55-76%) than curation models. Discuss whether the benchmark is overfit to the specific inductive biases of the curation models and if generalization claims hold for other architectures.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Clarify the statistical method used to compute the 95% confidence intervals reported in Figures 3, 4, 5, and 6. The text mentions '95% CIs over all runs' but does not specify if these are standard error of the mean (SEM), standard deviation (SD), or bootstrap intervals, nor does it state the distributional assumptions (e.g., normality) used for the calculation.
- **[science]** The curation pipeline (Section 3.2) uses a binary acceptance threshold (delta=0.001) and a consensus rule (3/5 models). The statistical power of this selection process is not discussed. There is a risk of selection bias where datasets with high variance might be rejected or accepted based on random seed fluctuations rather than true signal. A sensitivity analysis or power calculation for the curation threshold is needed.
- **[science]** In Appendix A.1, regression targets are discretized into 20 bins for the TAR fine-tuning step. The paper claims this is 'more stable' but does not provide statistical evidence (e.g., comparison of MSE or R^2) that this discretization preserves the predictive signal better than direct regression fine-tuning. This methodological choice requires justification or an ablation study.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Image-Tabular Curation), the phrase 'from which only 5 meet our criteria (31%), a proportion comparable to the text-tabular subset' is ambiguous. It is unclear if the 31% refers to the 5/16 or the final 20/56. Clarify the denominator to ensure the comparison is mathematically precise.
- **[writing]** In Section 6 (Robustness Analysis), the sentence 'This finding is particularly telling, as ConTextTab has set the SOTA for the CARTE Benchmark, emphasizing that MulTaBench targets a fundamentally different text-tabular problem' is slightly convoluted. Consider splitting this into two sentences to improve flow and emphasize the contrast between the benchmarks.
- **[writing]** In the Appendix (Text-Image-Tabular Datasets), the phrase 'By applying the selection rule independently, we prove that the 3 modalities contribute to the prediction to fulfill the Joint Signal criterion' contains a redundant 'to'. Rephrase to '...contribute to the prediction, thereby fulfilling the Joint Signal criterion' for better readability.
