# Automated-review action items — Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero-Shot Compositional Action Recognition

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.2 cites Fig 3 for a cosine similarity of 0.92, but Fig 3 shows FSP/FCP curves. The value is in supplementary Fig S1. Update the citation to the correct figure or move the analysis to the main text.
- **[writing]** Section 5.2 claims Jung et al. has the lowest unseen accuracy among CLIP baselines, but Table 1 shows AIM (39.19%) is lower than Jung (53.55%). Qualify the claim to 'lowest among compositional baselines' or correct the comparison set.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The caption is explicitly '(no caption)', providing no context for the plot's axes, data series, or scientific claim.
- **[science]** Figure 1: The Y-axis is labeled 'Cosine Similarity' but the values for the 'RCORE' series drop to -0.79, which is inconsistent with standard cosine similarity ranges ([-1, 1]) unless specific normalization is applied, yet no explanation is provided.
- **[writing]** Figure 1: The legend labels 'C2C (Baseline)' and 'RCORE (Ours)' are undefined; the caption does not explain what these acronyms stand for or the experimental setup.
- **[writing]** Figure 2: The figure has no caption text (only the filename), making it impossible to understand the context, dataset, or specific metrics being plotted.
- **[writing]** Figure 2: The legend is placed inside the plot area, obscuring the data points and trend lines for the 'False Co-occurrence Prediction' and 'Unseen Accuracy' series.
- **[science]** Figure 2: The left y-axis (Accuracy) and right y-axis (False Prediction Ratio) share the same numerical scale range (0-50 vs 30-70 roughly), but the visual alignment of the ticks is ambiguous, potentially misleading the reader about the relative magnitude of the 'False Seen Prediction' vs 'Seen Accuracy'.
- **[writing]** Figure 3: The figure lacks a descriptive caption; it is labeled '(no caption)' and only provides a filename, making the specific context of the 'diagnosis' unclear.
- **[writing]** Figure 3: The legend entry 'False Co-occurrence Prediction' is not explicitly defined in the caption, leaving the distinction between 'False Seen' and 'False Co-occurrence' ambiguous to the reader.
- **[writing]** Figure 4: The provided caption is empty ('no caption'), making it impossible to verify if the legends, symbols, or data series (e.g., 'Verb @ Seen Comp.', 'Random Accuracy') match the authors' intended description.
- **[writing]** Figure 4: The heatmap legends (e.g., 'Present/Absent', 'Seen/Unseen') are placed directly above the plots without clear visual separation or titles, which may confuse readers regarding which legend applies to which specific grid.
- **[writing]** Figure 5: The caption is missing; the provided text '(no caption)' prevents verification of the figure's content, context, or the meaning of the visual elements.
- **[science]** Figure 5: The image displays a video frame sequence with a time axis and a text label '(Take, Cup)', but without a caption, it is unclear what specific scientific claim or data this visual evidence supports.
- **[writing]** Figure 6: The x-axis labels are rotated but still overlap significantly, making the text difficult to read; consider increasing spacing or reducing the number of labels.
- **[writing]** Figure 6: The caption is empty ('no caption'), providing no context for the data shown or its relevance to the paper's claims.
- **[writing]** Figure 7: The caption is missing; the provided text '(no caption)' does not describe the plot's content, methods, or significance.
- **[writing]** Figure 7: The legend uses undefined acronyms ('C2C', 'RCORE', 'FSP', 'FCP') without explanation in the caption or figure text.
- **[writing]** Figure 8: The caption is empty ('no caption'), providing no explanation for the complex architecture diagrams, variable definitions (e.g., $L_{TORC}$, $L_{CPR}$), or the relationship between the three panels.
- **[writing]** Figure 8: The text '1 - lambda' in panel (b) is rendered in a standard serif font, while the surrounding mathematical notation uses a sans-serif font, creating visual inconsistency.
- **[writing]** Figure 9: The figure lacks a descriptive caption; the provided metadata '(no caption)' fails to explain the 'Training Data', 'Closed-world Evaluation', and 'Open-world Evaluation' panels or the specific meaning of the hatched, solid, and 'X' marked cells.
- **[writing]** Figure 9: The legend for the 'Training Data' panel is incomplete, showing only 'Train Pairs' while omitting definitions for the empty white cells which represent unobserved pairs.
- **[writing]** Figure 11: The caption is missing; the figure contains two complex heatmaps defining 'Training Set' vs 'Test Set' splits but lacks any text description to explain the experimental setup or the significance of the 'Present/Absent' and 'Seen/Unseen' labels.
- **[science]** Figure 11: The 'Test Set' heatmap uses a 'Seen' (orange) vs 'Unseen' (blue) legend, but the diagonal cells are colored 'Seen' while the off-diagonals are 'Unseen'. This implies a specific compositional split (e.g., seen actions on seen objects), but without a caption, the exact definition of the 'Unseen' condition (e.g., unseen action-object pairs vs. unseen objects) is ambiguous.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Abstract & Section 1: The acronym 'ZS-CAR' is used before being defined. Define 'Zero-Shot Compositional Action Recognition (ZS-CAR)' at its first occurrence in the Abstract or Introduction.
- **[writing]** Section 1 & 3: The acronyms 'FSP' and 'FCP' are used in the Introduction and Section 3 without prior expansion. Define 'False Seen Prediction (FSP)' and 'False Co-occurrence Prediction (FCP)' at their first occurrence in Section 3.2.
- **[writing]** Section 1 & 4: The acronyms 'CPR' and 'TORC' are introduced in the Introduction and used in Section 4 without expansion. Define 'Co-occurrence Prior Regularization (CPR)' and 'Temporal Order Regularization for Composition (TORC)' at their first occurrence in Section 4.
- **[writing]** Section 3.2: The symbol 'Dcg' (or $\Delta_{	ext{CG}}$) is used in the text and equations. Ensure 'Compositional Gap ($\Delta_{	ext{CG}}$)' is explicitly defined with the symbol before Equation 2.
- **[writing]** Section 5.1: The abbreviation 'H.M.' is used in the text and tables without definition. Define 'Harmonic Mean (H.M.)' at its first occurrence in Section 5.1.
- **[writing]** Section 5.1: The dataset names 'Sth-com' and 'EK100-com' are used as shorthand. Define 'Sth-com (Something-Something V2 compositional benchmark)' and 'EK100-com (EPIC-KITCHENS-100 compositional benchmark)' at their first occurrence.

## paper_reviewer_logical_consistency — verdict: accept

The paper presents a logically coherent argument structure. The diagnosis of "object-driven shortcuts" in Section 3 is consistently linked to the proposed solution components (CPR and TORC) in Section 4, and the experimental results in Section 5 directly address the specific failure modes identified earlier.

Specifically, the definition of the "Compositional Gap" ($\Delta_{\text{CG}}$) in Section 3.2 (Eq. 2) is applied consistently in the results tables (e.g., Table 1, Table 3) and the ablation studies. The logic that a negative $\Delta_{\text{CG}}$ indicates a failure to model compositionality beyond independent parts is maintained throughout the text.

The causal claims regarding the proposed method's efficacy are supported by the ablation studies (Table 4), which isolate the contributions of CPR and TORC. The text correctly interprets the ablation data: for instance, the claim that TORC yields the largest gain in verb generalization aligns with the data in Table 4(b), where removing TORC causes a significant drop in `verb@unseen-comp`.

There are no contradictions between the abstract, introduction, and conclusion regarding the scope of the results. The distinction between "seen" and "unseen" compositions is rigorously maintained in definitions, metrics, and result reporting. The argument that the open-world evaluation protocol is necessary to expose shortcut behaviors is logically sound and consistently applied in the comparison with baselines.

No logical gaps, non-sequiturs, or internal contradictions were found. The reasoning holds together as a valid argument.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper presents a strong diagnostic framework for object-driven shortcuts in Zero-Shot Compositional Action Recognition (ZS-CAR) and proposes a method (RCORE) that empirically reduces these shortcuts on two specific benchmarks. However, the rhetoric occasionally exceeds the scope of the demonstrated evidence, particularly in the strength of the claims made in the contributions list and conclusion. First, the contributions section (Introduction) claims the authors "prove that our approach miti

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a methodological contribution to computer vision (Zero-Shot Compositional Action Recognition) focused on mitigating "object-driven shortcuts" in model training. The work involves training models on existing public video datasets (Something-Something V2, EPIC-KITCHENS-100) and introducing a new benchmark split (EK100-com) derived from these public sources.

From a safety and ethics perspective, the research is low-risk:
1.  **Data Provenance:** The datasets used (Sth-com, EK100) are derived from public benchmarks with established licenses. The paper does not scrape new data from social media or private sources, nor does it release any raw video data containing Personally Identifiable Information (PII). The "EK100-com" is a re-splitting of existing public data, not a new collection of human subjects.
2.  **Dual-Use:** The proposed method (RCORE) aims to improve the temporal reasoning of action recognition models. While improved action recognition could theoretically be used in surveillance, the paper does not introduce capabilities that meaningfully lower the barrier to harmful surveillance or deception compared to existing state-of-the-art models. The method is a regularization technique for training, not a tool for generating deceptive content or exploiting vulnerabilities.
3.  **Human Subjects:** The research does not involve direct interaction with human subjects, surveys, or the collection of private behavioral data. The use of public video datasets for algorithmic training does not require IRB approval in this context, and no such statement is missing.
4.  **Bias/Fairness:** The paper explicitly addresses a form of bias (co-occurrence priors leading to shortcut learning) and proposes a method to mitigate it. It does not introduce new biases against identifiable demographic groups.

There are no missing disclosures, unmitigated risks, or ethical violations specific to this work. The paper is a standard algorithmic improvement study with no foreseeable non-trivial safety risks that require mitigation or disclosure beyond what is standard for the field.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling diagnosis of object-driven shortcuts in Zero-Shot Compositional Action Recognition (ZS-CAR) and proposes a method (RCORE) to mitigate them. The experimental design is generally sound, utilizing two datasets (Sth-com, EK100-com) and multiple backbones. However, the evidentiary strength of the reported improvements is weakened by a lack of statistical robustness and incomplete isolation of the proposed components' effects. First, the primary results in Tables 1 and

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Section 5 and Tables 1-4 report single point estimates (e.g., '34% vs 30%') without uncertainty measures (SD/SE/CI) across seeds. Deep learning results require variance reporting to distinguish signal from noise. Report mean ± SD over ≥3 seeds or explicitly state results are from a single run.
- **[writing]** The paper claims 'significantly improves' (e.g., Sec 5.2) without reporting p-values or hypothesis tests. Statistical significance requires a formal test (e.g., paired t-test) and alpha level. Either run the test and report p-values or rephrase claims to describe magnitude (e.g., 'improves by X points') without invoking significance.
- **[writing]** Ablation studies in Sec 5.3 compare multiple configurations without correcting for multiple comparisons. Highlighting the 'best' configuration among many tests inflates false-positive risk. Apply a correction (e.g., Bonferroni) or explicitly acknowledge the uncorrected nature of these comparisons.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the argument flows logically from the diagnosis of the problem to the proposed solution. However, there are several instances where sentence construction impedes immediate comprehension, forcing the reader to re-parse or guess the intended structure. In Section 3.2, the description of the bias-controlled experiment is buried in a long, complex sentence that delays the main action. Similarly, in Section 4, the introduction of the backbone adapters is mud
