# Automated-review action items — AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distillation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: accept

The manuscript demonstrates a high degree of factual accuracy and rigorous citation practices. My review confirms that the claims made regarding the limitations of consistency distillation (e.g., trajectory drift, degradation with increased steps) are accurately supported by the cited literature (Song et al., 2023; Zheng et al., 2025; Huang et al., 2025) and the internal ablation studies presented in Figures 3, 4, and 5.

The specific performance metrics reported in the Abstract and Section 5 (e.g., VBench scores of 84.05 at 4 NFEs for the 14B causal model) are consistent with the data presented in Table 1 (t2v_comparison.tex) and Table 2 (i2v_comparison.tex). The claim that AnyFlow outperforms Krea-Realtime-14B (83.25) is directly supported by the table data. The statistical significance statement in Section 5, mentioning paired t-tests and Bonferroni correction, is a standard and appropriate claim for the experimental design described, and the authors correctly note that baseline scores were taken from original papers under identical protocols.

Citations to related work, such as MeanFlow (Geng et al., 2025) and TMD (Nie et al., 2026), are used correctly to contextualize the methodological choices (e.g., the shift from Jacobian-vector products to finite difference approximations). The distinction drawn between consistency backward simulation and the proposed flow map backward simulation is accurately attributed to the cited works (Yin et al., 2024; Huang et al., 2025).

The ethical statement and limitations section (Section 6) are appropriately framed, acknowledging the reliance on external datasets and the potential for misuse without overstating the model's current safety capabilities. No unsupported claims or misrepresentations of prior art were found. The paper is scientifically sound in its factual assertions.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The legend defines 'Zero Init Time Emb' as 'Emb(t) + Emb'(t - r)', but the plot shows this method's norm increasing significantly over training iterations. If this were a simple sum of embeddings, it should remain constant or behave differently; the label likely misrepresents the actual method being plotted (perhaps it is the 'distilled' or 'trained' version, not the initialization).
- **[writing]** Figure 1: The legend text for 'Interpolated Time Emb (Ours)' is cut off or poorly formatted, showing 'g · Emb(t) + (1 - g) · Emb'(r)' on a new line without clear alignment, making it hard to associate with the red line.
- **[science]** Figure 2: The green line labeled 'w(t) = Uniform(0, 1)' is plotted as a linearly increasing function (slope 1), which contradicts the definition of a uniform distribution (constant density). Additionally, the caption defines $f(t) = p(t)w(t)$, but the legend labels the curves as $w(t)$, creating a mismatch between the plotted density and the legend's variable name.
- **[science]** Figure 3: The 'Annotations' box defines $f_	heta(z_t, t)$ as 'Consistency Model' and $f_	heta(z_t, t, r)$ as 'Flow Map Model', but the diagram labels in (a) and (b) use inconsistent notation (e.g., $f_	heta(z_{t_1}, t_1)$ vs $f_	heta(z_T, T, t)$) without explicitly mapping them to the defined model types, creating ambiguity about which model is used at each step.
- **[writing]** Figure 3: The 'Annotations' box is visually separated from the main diagrams and lacks a clear border or background distinction, making it easy to overlook; integrating it closer to the relevant panels or using a more prominent visual style would improve clarity.
- **[writing]** Figure 4: The text inside the diagram boxes (e.g., 'Self-Forcing Causal Model v1.0', 'ODE-Int + DMD') is extremely small and illegible, making the specific steps of the pipeline unreadable.
- **[science]** Figure 4: The diagram depicts a 'Self-Forcing' pipeline where the model is discarded (trash can icon) after fine-tuning, which contradicts the caption's claim that the method 'bypasses the complexities of retraining' by implying the model is not adapted for use.
- **[science]** Figure 5: The caption claims the pre-trained model (a) struggles with 'robot arm type' identity preservation, but the images in (a) and (b) show the same robot arm model; the actual difference is the generated motion (arm reaching vs. static), which contradicts the specific 'identity' claim.
- **[science]** Figure 5: The caption claims the pre-trained model (a) struggles with 'trajectory accuracy' for pedestrians, but the pedestrian in (a) moves across the frame similarly to (b); the visible failure in (a) is actually the generation of a large white car artifact, not the pedestrian trajectory.
- **[science]** Figure 6: The caption states that (a) Consistency distillation learns a mapping from $z_t$ to $z_0$, but the 'Forward Consistency Training' panel shows trajectories mapping $z_0$ to $z_T$ (or $z_t$ to $z_T$), which contradicts the text description of the learning objective.
- **[writing]** Figure 6: The 'Re-Noise State' label in panel (a) points to a grey circle, but the caption does not define this symbol or explain the re-noising process visually depicted.
- **[science]** Figure 8: The y-axis 'Vbench Score' scales differ significantly across the three subplots (approx. 82.0-84.1, 75.0-84.5, and 61.0-84.5), yet the plots are presented side-by-side without explicit visual separation or individual axis labels, which risks misleading the reader into comparing absolute values across panels that are not on the same scale.
- **[writing]** Figure 8: The tables at the top of the figure (labeled 'Table 2', 'Table 2-1', 'Table 2-1-1') are not referenced in the figure caption, making their relationship to the line plots below unclear.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized acronyms and domain-specific terminology that are not consistently defined for a broader audience. While the target audience for this paper is likely researchers in generative models, the "jargon police" lens requires that every acronym be explicitly defined at its first occurrence to ensure accessibility. In the Abstract, the sentence "We denote NFEs as Number of Function Evaluations (NFEs) for clarity" is structurally flawed; it uses the acronym bef

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The Ethics Statement (arxiv_anyflow.tex) has a broken sentence: 'To mitigate... strategies: We further note...' interrupts the list of strategies, breaking logical flow.
- **[science]** Section 5 claims paired t-tests were used, but baselines from original papers lack variance data in tables, making the statistical significance claim logically unsupported.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The manuscript makes several strong claims regarding the novelty and performance of AnyFlow that require tighter alignment with the presented evidence to avoid overreach. First, the assertion in the Abstract and Introduction that AnyFlow is the "first any-step video diffusion distillation framework based on flow maps" is a significant claim. While the authors correctly cite the concurrent work TMD (Nie et al., 2026) in Section 2, which also utilizes a flow map formulation for bidirectional video

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Ethics Statement (arxiv_anyflow.tex, lines 38-52) acknowledges deepfake risks but lacks specific mitigation details. The proposed 'robust, imperceptible watermarks' are undefined. Authors must specify the watermarking algorithm (e.g., frequency domain vs. spatial), its robustness against common attacks (compression, cropping), and whether it will be open-sourced or proprietary.
- **[writing]** The manuscript states training data consists of 'publicly available, royalty-free video clips' (arxiv_anyflow.tex, line 48) but provides no citation, dataset name, or link to the specific corpus. To ensure compliance with copyright and privacy regulations, authors must explicitly name the dataset(s) used and confirm the specific license terms (e.g., CC0, CC-BY) that permit commercial use and derivative works.
- **[writing]** The paper mentions downstream fine-tuning on specialized domains like robotics and driving (sections 4 & 5). While the authors note the base model struggles with identity preservation, they do not address the safety risks of fine-tuning on private or sensitive datasets (e.g., facial recognition data, proprietary industrial footage). A brief discussion on data privacy safeguards for downstream users is required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of statistical significance in the main text (Section 5) relies on 'paired t-tests and Bonferroni correction' but does not report the resulting p-values, t-statistics, or effect sizes in any table or figure. Without these metrics, the robustness of the reported improvements (e.g., 84.05 vs 83.73) cannot be independently verified against random seed variance.
- **[science]** The evaluation protocol for the main results (Table 1) cites '200 evaluation prompts' with 'three random seeds' (600 videos total). However, the ablation study (Table 2) and training cost analysis (Table 3) do not specify if the same prompt set and seed count were used. Inconsistent sampling budgets across experiments could confound the comparison of NFE scaling effects.
- **[science]** The paper claims AnyFlow outperforms baselines like rCM and Self-Forcing, but several baselines (e.g., Krea-Realtime-14B, FastVideo) are evaluated using scores 'taken directly from their original papers' rather than re-evaluated under the unified protocol. Differences in prompt sets, VBench versions, or inference seeds between the original papers and this study introduce a confounding variable that weakens the causal claim of superiority.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The manuscript claims statistical significance via paired t-tests with Bonferroni correction (arxiv_anyflow.tex, lines 38-40) but fails to report the resulting p-values, t-statistics, or effect sizes in the text or tables. Without these metrics, the claim of significance cannot be verified.
- **[science]** Table 4 (referenced in arxiv_anyflow.tex, line 36) is described as containing 95% confidence intervals and standard deviations, yet the provided LaTeX source only contains Table 1 (ablation_anyflow), Table 2 (i2v_comparison), Table 3 (paradigm_compare), Table 4 (t2v_comparison), and Table 5 (training_cost). The specific table with the requested variability metrics is missing or mislabeled.
- **[science]** The evaluation protocol mentions 200 prompts with 3 random seeds (600 videos total) in arxiv_anyflow.tex (lines 32-34). However, the statistical power of the paired t-tests across 200 pairs is not discussed, nor is the assumption of normality for the score distributions (VBench scores) justified, which is a prerequisite for the t-test validity.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The Ethics Statement section (lines 48-62) contains a severe structural error: a sentence fragment ('To mitigate these risks, we propose the following strategies:') is immediately followed by an unrelated sentence ('We further note that AnyFlow builds upon...') before the actual list of strategies begins. This breaks the logical flow and confuses the reader.
- **[writing]** In the Abstract (line 1), the definition of NFEs ('We denote NFEs as...') is placed awkwardly as the very first sentence, interrupting the standard abstract flow. It should be moved to the first instance of the acronym in the main text or integrated more smoothly.
- **[writing]** In Section 3 (Preliminary), the subsection header 'Differential Derivation Equation.' (line 134) contains a period that is grammatically incorrect for a section title and disrupts the visual hierarchy. It should be removed.
