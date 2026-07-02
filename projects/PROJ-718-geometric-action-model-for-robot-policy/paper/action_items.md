# Automated-review action items — Geometric Action Model for Robot Policy Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The '55x faster' claim (Abstract, Intro) compares GAM with CUDA Graphs (6.9ms) against baselines without it. Clarify that this speedup includes deployment optimizations not applied to baselines, or re-evaluate baselines with the same settings for a fair architectural comparison.
- **[writing]** The '9.7%p' camera perturbation gain (Intro) compares GAM to Cosmos-Policy (73.4%) but ignores $\pi_{0.5}$ (72.0%). Specify that the gain is relative to the best WAM baseline or clarify the comparison scope to avoid implying a universal lead over all foundation models.
- **[writing]** The '784K trajectories' claim (Sec 4.1) lacks explicit confirmation in the appendix. State the exact filtered dataset count or link the 784K figure to the specific OXE/MimicGen/RoboCasa365 split to ensure reproducibility of the data scale.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The bar chart values (e.g., 18.0 for MimicGen) contradict the pie chart legend (18% for MimicGen) and the caption's claim that the bar chart shows 'percentage'. The sum of bar values is ~100, implying the bars show raw counts (in 10Ks) rather than percentages, creating a direct conflict with the caption and the pie chart's percentage labels.
- **[writing]** Figure 2: The caption 'LIBERO-Spatial: bowl from table center to plate' is too brief and does not explain the four rows (Current RGB, Current Depth, GT Future, Pred Future) or the time steps (T=0 to T=10) shown in the figure.
- **[science]** Figure 2: The 'Current RGB' row shows a top-down view of the scene, while the 'Current Depth' and future rows show a side-view depth map; this perspective shift is not explained in the caption and may confuse readers about the spatial relationship between views.
- **[writing]** Figure 4: The x-axis of the 'Inference Latency' scatter plot is reversed (500 to 5), which is non-standard and potentially confusing.
- **[writing]** Figure 4: The x-axis label for the bar chart is misspelled as 'Pertrubed Camera' instead of 'Perturbed Camera'.
- **[writing]** Figure 4: The title 'Geometric Foundation Model' is misspelled as 'Geometric Foundation Model' (missing 'r' in Geometric) in the top left.
- **[writing]** Figure 7: The sub-figure labels (a) and (b) in the right column are not defined in the caption, which only describes the general setup and ID vs. OOD camera setup without mapping these labels to specific camera views.
- **[writing]** Figure 7: The terms 'In-distribution' and 'Out-of-distribution' are used as labels for the robot end-effector views on the left, but the caption does not explicitly define what constitutes the in-distribution versus out-of-distribution setup.
- **[science]** Figure 9: The caption describes 'Attention visualizations of action tokens,' but the figure displays a grid of robot manipulation frames with heatmaps overlaid on the scene. It is unclear if these heatmaps represent attention over action tokens or spatial attention over the image; the visualization does not match the description of token-level attention.
- **[writing]** Figure 9: The figure lacks a legend or colorbar to interpret the heatmap intensity (e.g., attention weight or probability), making the visualizations unquantifiable.
- **[writing]** Figure 9: The row labels ('Layer 13', 'Layer 26', etc.) and column labels ('t=1', 't=3', etc.) are present, but there is no explicit legend defining what the specific colors in the heatmaps represent.
- **[science]** Figure 10: The caption states that light bars represent in-domain and dark bars represent out-of-domain settings, but the bar chart legend identifies the colors as 'Ours', '$\pi_{0.5}$', and 'Spatial Forcing'. This creates a direct contradiction where the visual encoding (color) conflicts with the textual description of the experimental conditions.
- **[science]** Figure 10: The 'Stack milk and cube' task shows a 100% success rate for 'Ours' (80+20), yet the 'Pick and Place' task (a prerequisite skill) shows a lower success rate for the same method. The stacked bars imply a breakdown of success types (e.g., ID vs OOD) but the caption's definition of the bars does not align with the stacked nature of the data visualization.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and mathematical shorthand that hinder accessibility for a broader robotics or computer science audience. First, the Abstract introduces three major acronyms—VLA (vision-language-action models), WAM (video world-action models), and GAM (Geometric Action Model)—without defining them. While GAM is defined, VLA and WAM are used immediately. The Introduction defines VLA and WAM but repeats the acronym GAM without re-defining it in the context

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Speed Claims and Deployment Variables: The introduction and analysis sections claim GAM is "55x faster" than diffusion-based baselines. This figure is derived from the deployment setting in Appendix Table 1 (6.9ms for GAM with CUDA Graphs vs. 382.4ms for Cosmos). The logical gap lies in attributing this massive speedup primarily to the *architecture* (single-pass vs. diffusion) while the comparison includes a significant *deployment* variable (CUDA Graphs enabled for GAM but not baselines). The
- **[writing]** Ablation Interpretation: In Section 4.3 (Ablation Study), the authors state that removing the future-prediction losses ($\mathcal{L}_{\text{depth}}$ or $\mathcal{L}_{\text{feat}}$) has "minimal impact" on robustness when pretraining is used. Yet, they immediately argue that these losses are crucial for robustness when pretraining is *not* used. While this is a valid observation about the interaction between pretraining and auxiliary losses, the phrasing "minimal impact" followed by "substantiall

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim of being '55x faster' (Introduction, Sec 4.2) relies on a specific deployment configuration (CUDA Graphs) for GAM that is not applied to baselines. The text states baselines use 'official PyTorch' paths without CUDA Graphs, while GAM uses them. This comparison is unfair and overstates the speed advantage. The authors must either apply CUDA Graphs to all baselines or rephrase the claim to reflect the specific optimization used.
- **[writing]** The claim that GAM is 'more accurate' (Abstract, Introduction) is an overgeneralization. Table 1 shows GAM is not the most accurate on the standard LIBERO benchmark (Orig. SR 97.6% vs Cosmos-Policy 98.5% and pi0.5 96.9% is close, but Cosmos is higher). GAM is only 'more accurate' on specific perturbation settings (e.g., Camera). The text should qualify 'more accurate' to 'more robust under perturbations' or 'more accurate in OOD settings'.
- **[writing]** The statement that GAM is 'lighter' (Abstract, Introduction) is ambiguous. While the total parameter count (1.4B) is lower than some baselines (e.g., 7B OpenVLA), it is comparable to or higher than others (e.g., 2B Cosmos, 3.3B pi0.5). The claim should be qualified to 'fewer trainable parameters' (which is true, ~983M vs 3.3B+) rather than 'lighter' in a general sense, as the frozen backbone still contributes to the model size.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The real-world experiments section (Appendix A.3) describes collecting teleoperated demonstrations but lacks explicit confirmation of informed consent from human operators and IRB approval status. Given the use of human data for training, a statement on ethical clearance and consent procedures is required.
- **[writing]** The paper claims a 55x speedup and 145Hz control rate. While efficiency is positive, the authors must explicitly address safety implications of high-frequency open-loop execution (Section 4.1) in the absence of real-time safety monitors or collision avoidance layers, particularly for contact-rich tasks.
- **[writing]** The training data includes Open-X Embodiment (Appendix A.1). The authors should clarify if this dataset contains any personally identifiable information (PII) or sensitive data and confirm that their usage complies with the original dataset licenses and privacy policies.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of '55x faster' inference (Sec 4.2) relies on a specific deployment configuration (CUDA Graphs) for GAM that is not applied to baselines. Table A.5 shows the gap narrows to ~1.7x (17.5ms vs 29.2ms) without CUDA Graphs. The main text must clarify this asymmetry to avoid overstating the speed advantage.
- **[science]** Real-world robustness claims (Sec 4.2) are based on only 20 trials per task (10 ID, 10 OOD). This sample size is insufficient to robustly claim 'substantial' outperformance over baselines given the high variance typical in real-robot manipulation. Please report confidence intervals or conduct a statistical significance test (e.g., bootstrap) to support the conclusion.
- **[science]** The ablation study in Table 3 suggests removing L_depth and L_feat has 'minimal impact' on robustness (Plus SR 89.0% vs 89.7%). However, the text claims these losses 'substantially improve robustness' when pretraining is absent. The manuscript should explicitly reconcile these findings: does the benefit of geometric prediction losses depend entirely on the absence of pretraining, or is the effect masked by the strong backbone in the main setting?

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard deviations for success rates in Table 1 and Table 3. With N=500 rollouts per suite, the margin of error is ~2%, yet no uncertainty metrics are provided to assess the statistical significance of the reported 9.7%p gain.
- **[science]** Clarify the statistical test used to claim 'consistently outperforms' in Section 4.2. Given the binary nature of success/failure, specify if a McNemar's test or bootstrap procedure was used to validate the differences against baselines like pi_0.5.
- **[science]** In the ablation study (Table 3), the claim that removing L_depth has 'minimal impact' lacks statistical validation. Provide p-values or effect sizes to confirm the difference between 89.7% and 89.5% is not due to random variance.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Appendix A (Experimental Settings), the text states '64 NVIDIA GH200 GPUs witch batch size of 1024'. The word 'witch' is a typo and should be corrected to 'with'.
- **[writing]** In Appendix A (Generated Future Depth Maps), the sentence reads 'GAM predicts the and future depth maps'. The word 'the' appears to be a typo or an extra word that disrupts the sentence flow; it should likely be removed or the sentence rephrased to 'GAM predicts future depth maps'.
- **[writing]** In Section 3 (Related Work), the phrase 'align intermediate VLA features with geometric foundation model' lacks an article. It should read 'with a geometric foundation model' or 'with geometric foundation models' for grammatical correctness.
