# Automated-review action items — Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation from Diverse Inputs

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 'substantially outperforms... agentic baseline' without specifying 'controlled comparison' (same backbone). Table 1 shows the gap shrinks if comparing against PaperBanana (w/ Nano Banana Pro). Clarify the baseline definition in the abstract to avoid ambiguity.
- **[writing]** Section 3.1 claims the VLM metric 'tracks human preference' based on a study with Cohen's kappa=0.58. This indicates 'moderate' agreement, not strong validation. Temper the claim to reflect the moderate agreement level accurately.
- **[writing]** Section 4.1 states 'No baseline surpasses Crafter in any column'. While true for the specific rows shown, the comparison mixes backbones (Nano Banana 2 vs Pro) in the full table. Ensure the text explicitly limits this claim to the 'controlled comparison' setting to prevent misinterpretation.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption states 'Given context and Docs', but the diagram explicitly labels the input as 'Input Context' (speech bubble) and 'Document' (paper icon), creating a minor terminology mismatch.
- **[writing]** Figure 1: The caption mentions 'seeds $S_0$', but the diagram labels the central scroll simply as 'S' without the subscript '0', which may cause confusion regarding the iteration state.
- **[writing]** Figure 2: The caption contains LaTeX placeholders (e.g., '$a^*$', '$v$', '()') and incomplete sentences (e.g., 'verifies the cleaned canvas ()') that are not resolved by the visual content, making the text difficult to read.
- **[writing]** Figure 2: The caption describes a 'VLM designer D' and 'image editor E', but the figure labels these roles as 'Vision-Language Designer Agent' and 'Image-Editing Executor' without explicitly mapping them to the variables D and E used in the text.
- **[science]** Figure 3: The caption states 'Each column shows one task,' but the image displays four distinct columns labeled (a) Text-to-image, (b) Mask-completion, (c) Key-element, and (d) Sketch. The caption fails to define or describe these specific task categories, making the figure's content ambiguous without external context.
- **[writing]** Figure 3: The placeholder text 'Representative \ samples' in the caption contains a LaTeX formatting error (missing command name), which should be corrected to 'Representative Crafter samples' or similar for clarity.
- **[writing]** Figure 4: The column headers ('Conditioning input', 'PaperBanana', 'AutoFigure', 'Ours', 'Ground truth') are not defined in the caption, which only states 'Qualitative comparison across different input conditions'.
- **[writing]** Figure 4: The row labels ('Text-to-image', 'Mask completion', 'Key-element composition', 'Sketch conditioned') are not defined in the caption, making the specific input conditions ambiguous.
- **[science]** Figure 5: The caption claims to show 'three reference-conditioned task constructions' and 'three graduate-level annotators,' but the image displays only a single interface instance with no evidence of the three distinct task types or the multi-annotator workflow described.
- **[writing]** Figure 5: The image is a raw screenshot of an annotation tool UI (including 'Close region picker', sliders, and 'Apply edits to disk' buttons) rather than a polished figure illustrating the 'task constructions' or 'drawing tools' mentioned in the caption.
- **[writing]** Figure 7: The caption contains missing text for the column headers ('Columns: input raster, , , \ (green frame)'), failing to name the 'Edit-Banana' and 'AutoFigure-Edit' systems shown in the image.
- **[writing]** Figure 7: The caption states 'Per-panel numbers are three-VLM judge means' but does not define the scale or units (e.g., 0-10) for these scores.
- **[science]** Figure 8: The 'Ours' column (red frame) displays a fully rendered, high-quality diagram with detailed text and arrows, which directly contradicts the caption's claim that this figure represents 'failure cases' (specifically 'dropped panels', 'mismatched infill', and 'literal skeleton'). The visual content of the 'Ours' column does not match the failure modes described in the caption or the labels on the left.
- **[science]** Figure 8: The 'Conditioning input' column contains a text block describing a 'multi-dimensional task structure' and 'experimental procedure', but the corresponding 'Ours' and 'Ground truth' columns display schematic diagrams of neural network architectures (transformers/attention blocks) rather than the 'multi-dimensional task structure' described in the input.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology from the multi-agent systems and computer vision literature, which creates a barrier for non-specialist readers. The central concept of a "harness" is introduced in the Abstract and Introduction without a clear, plain-English definition, forcing the reader to infer its meaning from context. Similarly, terms like "directive diagnostics," "typed edits," and "convergence judge" are used frequently but lack immediate clarification. While these

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 5.1 claims PaperBanana's gain shrinks from 22.60 to 8.10 points. Table 1 shows scores of 33.73 and 28.00, a difference of 5.73. The text's numerical claim contradicts the table data. Verify calculations.
- **[writing]** Section 5.2 states 'Readability suffers the most' when plan exploration is removed. Table 2 shows Faithfulness drops 9.76 points vs Readability's 9.47. The text contradicts the table data.
- **[writing]** Section 3.3 claims sketch/key-element tasks are 'entirely from academic figures' (70 total). Table 1 lists 140 academic figures. The text omits how the remaining 70 academic figures are distributed, creating ambiguity in the dataset composition logic.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of being the 'first end-to-end generation-to-editing pipeline' (Abstract) overreaches given prior work like AutoFigure-Edit and Edit-Banana. Qualify as 'first harness-based' or 'state-of-the-art'.
- **[writing]** The assertion that the architecture generalizes 'without architectural changes' (Abstract) is unsupported outside the scientific domain. The agents are implicitly tuned for scientific figures; remove the absolute claim or limit scope to scientific figures.
- **[writing]** The Conclusion's expectation that the pattern extends to 'domains beyond scientific figures' is speculative and unsupported by data. Rephrase as a future direction or hypothesis.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The human evaluation section (Appendix Human Evaluation) states annotators were compensated at $25/hour but does not specify the total hours worked, total payment per annotator, or the ethical approval (IRB) status for this human-subject research. Explicitly state the IRB exemption/approval number or confirm the study was deemed exempt by the authors' institution.
- **[writing]** The benchmark construction (Section 4.1) involves scraping figures from arXiv, conference posters, and blogs. While likely fair use for research, the paper should explicitly address data privacy and copyright considerations, confirming that no personally identifiable information (PII) was extracted from the source figures and that the dataset usage complies with the source platforms' terms of service.
- **[writing]** The system relies on closed-source, proprietary models (Gemini, GPT) for both generation and evaluation (Section 5, Appendix A). The paper should briefly discuss the potential for bias in these proprietary models affecting the evaluation scores and the lack of transparency in the evaluation pipeline as a safety/ethics limitation.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The human evaluation study (Appendix, Section 'Human Evaluation') reports a Cohen's kappa of 0.58 on only 60 samples. This sample size is statistically underpowered to validate the VLM judge as a reliable proxy for the full 279-sample benchmark. The authors must either expand the human study to a statistically significant size (e.g., >200 samples) or provide a power analysis justifying the current N.
- **[science]** Table 1 reports a 0.00% win-rate for open-source baselines (GLM-Image, Qwen-Image) on the 279-sample CrafterBench. This absolute failure across all dimensions suggests a potential evaluation protocol mismatch (e.g., the VLM judge failing to parse open-source outputs) rather than a genuine performance gap. The authors must provide qualitative examples or error logs explaining why these models scored zero to rule out a systematic evaluation artifact.
- **[science]** The ablation study (Table 2) removes mechanisms one at a time but does not report variance (standard deviation) or statistical significance tests (e.g., paired t-tests) for the performance drops. Given the small benchmark size (n=279) and the stochastic nature of LLM-based generation, the authors must demonstrate that the observed drops (e.g., 5.04 to 8.90 points) are statistically significant and not due to random seed variance.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The VLM-as-judge evaluation lacks statistical rigor. The paper reports mean win-rates and Cohen's kappa (0.58) but omits confidence intervals, standard errors, or significance tests (e.g., paired t-tests or Wilcoxon signed-rank) to validate that the observed margins (e.g., +16.61 points) are not due to random variance in the judge's scoring.
- **[science]** The ablation study (Table 2) reports point drops (e.g., -8.90) without statistical validation. Given the small sample size (n=292 for PaperBananaBench), the authors must report whether these differences are statistically significant to support the claim that 'every mechanism contributes independently'.
- **[science]** The human evaluation (Appendix) uses a small sample (N=60) to validate the VLM judge. The reported agreement (72%) and kappa (0.58) lack confidence intervals. A binomial proportion confidence interval is required to assess the reliability of this proxy metric.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct the typo 'viusal' to 'visual' in the Introduction, second paragraph, where the text discusses researchers iterating from rough sketches.
- **[writing]** Fix the grammatical error 'Evaluation method for scientific figure generation remains as narrow as systems it measures' in Section 2. Change to 'Evaluation methods... remain as narrow as the systems they measure'.
- **[writing]** Resolve the subject-verb agreement error in Section 5.2: 'Together, both ablations confirms that...' should be 'confirm that...'.
- **[writing]** Standardize the capitalization of 'CraftBench' in Table 1 caption and Section 5.1 to match the consistent usage of 'CrafterBench' elsewhere in the paper.
