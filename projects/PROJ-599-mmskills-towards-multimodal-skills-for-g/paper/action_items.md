# Automated-review action items — MMSkills: Towards Multimodal Skills for General Visual Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_science

- **[science]** Branch-Loading Mechanism: The two-stage branch-loading approach (gated view selection + planning) is a clever engineering solution to the "context pollution" and "visual anchoring" problems inherent in loading large multimodal skill packages. The ablation studies in Figure 3 effectively demonstrate the necessity of both components.
- **[science]** Comprehensive Evaluation: The paper evaluates across diverse benchmarks (OSWorld, macOSWorld, VAB-Minecraft, Super Mario) and model sizes (from 8B to 235B parameters), providing a robust picture of the method's generalizability.
- **[science]** Behavioral Analysis: The analysis of agent behavior (RQ4) goes beyond success rates, showing that MMSkills reduce repetitive actions and low-level primitive usage, which is a strong qualitative indicator of improved reasoning. ## Concerns
- **[science]** Critical Data Leakage Risk (Major): The most significant flaw is the potential overlap between the evaluation benchmarks (OSWorld, macOSWorld) and the skill source (OpenCUA).
- **[science]** OSWorld and macOSWorld are standard benchmarks for computer-use agents.
- **[science]** OpenCUA is described as a source of "public non-evaluation trajectories" for Ubuntu and macOS.
- **[science]** Both datasets cover the same application domains (Chrome, LibreOffice, VS Code, etc.).
- **[science]** The paper claims in Appendix A.2 that "All MMSkills are extracted from non-test trajectories" and that source data is "disjoint from the final evaluation cases." However, without a rigorous deduplication check (e.g., comparing task instructions, screenshots, or trajectory hashes), it is highly probable that the "source" trajectories contain the exact same tasks or very similar variations as the "test" set. If the agent is effectively "memorizing" the test tasks from the source data, the reported
- **[science]** Bibliography Integrity: The bibliography entry for the paper itself (arXiv 2605.13527) is marked as "unreachable" in the provided metadata. While this might be a metadata artifact, the reference list contains several 2025/2026 citations (e.g., wang2025opencua, yang2025macosworld). The reviewer must verify that these are real, accessible preprints or published works. If they are future-dated or inaccessible, the scientific grounding is weak.
- **[science]** Skill Generation Complexity: The "Generator" pipeline (5 phases) is complex. While the paper describes it, the reproducibility of the skill generation process is unclear. How are "meta-skills" defined? How is the "audit" phase automated? The lack of a detailed algorithm or pseudocode for the Generator (beyond the high-level pipeline) makes it hard to assess the quality of the generated skills.
- **[science]** Perform a rigorous deduplication analysis between the source trajectories and the test sets. If any overlap is found, the experiments must be re-run with a strictly filtered source set.
- **[science]** Provide a detailed explanation of how the "disjoint" property was ensured (e.g., hash matching, semantic similarity thresholds).
- **[science]** Clarify the provenance and accessibility of the cited 2025/2026 works.
- **[science]** Add a section or table quantifying the inference cost/latency overhead of the branch-loading mechanism. Once these scientific concerns are addressed, the paper will be a strong contribution to the field of visual agents.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Table 1 (OSWorld): For Qwen3-VL-235B under MMSkills, the reported overall success is 39.17%. A weighted calculation using the domain counts from Appendix Table A1 (e.g., Chrome: 45, GIMP: 26, etc.) and the domain success rates in Table 1 does not immediately yield 39.17%. For instance, the high performance in Chrome (59.91%) and GIMP (69.23%) should pull the average up significantly. The current overall figure seems lower than a simple weighted average of the visible domain scores. The authors m
- **[writing]** Table 2 (macOSWorld): Similar concerns exist for the macOSWorld "Overall" column. The text claims MMSkills improve performance, but the specific aggregate numbers need to be mathematically consistent with the domain breakdowns provided in Appendix Table A1. Claim Verification in Text vs. Data:
- **[writing]** Step Reduction (Section 4.3): The text claims the "largest reductions" in interaction steps appear for Qwen3-VL-235B. While Table 3 shows a 5.35 step reduction on OSWorld for this model, the same table shows a 7.67 step reduction on VAB-Minecraft for the same model. The text phrasing "largest reductions appearing for Qwen3-VL-235B" is ambiguous; it should specify "on OSWorld" or acknowledge the even larger reduction on VAB-Minecraft to avoid misleading the reader about the magnitude of the effec
- **[writing]** Behavioral Shift Metrics (Section 4.4): The claim that "exact repeated actions fall from 21.8% to 6.2%" for Qwen3-VL-235B is specific. However, Figure 3 (Panel C) does not explicitly label these percentages on the axis or in the caption. While the visual trend supports the claim, the specific numbers should be explicitly cited in the figure caption or a supplementary table to ensure the claim is fully supported by the visual evidence presented. Citation Accuracy: The citations for benchmarks (OS

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** This re-review confirms that the four specific claim-accuracy issues identified in the prior review remain unaddressed in the current revision. The manuscript continues to present aggregate statistics in Tables 1 and 2 that do not mathematically reconcile with their constituent domain breakdowns, creating a risk of reader confusion regarding the true performance gains. Additionally, the text in Section 4.3 retains an ambiguous claim about "largest reductions" that contradicts the data in Table 3

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2 caption contains a broken cross-reference: 'The panels follow the same metrics as Figure :' is missing the target figure number (likely Figure 6).
- **[science]** Figure 2 Panel (B) x-axis label 'Mean count per task' is ambiguous; the caption describes it as 'low-level primitives per task', but the axis lacks the specific unit or definition of 'count'.
- **[writing]** Figure 3: The caption claims 'Colored turn labels distinguish direct GUI actions, skill loading, branch guidance, evidence-gated reasoning, and final completion,' but the figure lacks a legend or key to map the specific colors (orange, green, blue, purple) to these categories.
- **[writing]** Figure 4: The caption claims 'Colored turn labels distinguish direct GUI actions, skill loading, branch guidance, evidence-gated reasoning, and final completion,' but the figure lacks a legend or key mapping the specific colors (e.g., orange, green, purple) to these categories.
- **[writing]** Figure 4: The top section lists 'GUI action' and 'Branch guidance' as categories, but the 'Branch guidance' label is not used in the turn sequence (Turns 2B and 5B are labeled 'Branch'), creating a minor inconsistency between the legend and the timeline.
- **[science]** Figure 5: The x-axis labels in Panel (B) ('Direct-Full', 'Direct-Selected', 'Branch-Full') are ambiguous and do not clearly map to the specific ablation conditions described in the caption (e.g., 'branch loading with or without view selection'), making it difficult to interpret the specific contribution of each component.
- **[writing]** Figure 5: The checkmarks and 'x' symbols in the legend table are not explicitly defined in the caption or figure text, requiring the reader to infer that they represent the presence or absence of 'Cards' and 'Images'.
- **[science]** Figure 6, Panel (B): The legend lists 'Qwen3-VL-235B / No skill' and 'Qwen3-VL-235B / MMSkills', but the y-axis labels only include 'All primitives / task', 'Clicks / task', 'Keyboard / task', and 'Scroll+wait / task'. The 'All primitives' row has no corresponding data points for the Qwen models, creating a mismatch between the legend and the plotted data.
- **[writing]** Figure 6, Panel (B): The legend uses 'Qwen3-VL-235B' while the main text and other panels (A, C) refer to 'Qwen'. This inconsistency in model naming (Qwen vs Qwen3-VL-235B) across the figure panels is confusing and should be standardized.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 2.1 (Eq. 1) introduces symbols $O_t$, $H_t$, $\mathcal{C}_I$, and $A_t$ without definition. An adjacent-field reader cannot infer that $O_t$ is the current observation, $H_t$ is the history, or $\mathcal{C}_I$ is the candidate skill set. Add a clause immediately following Eq. 1 defining each symbol (e.g., 'where $O_t$ is the current screenshot, $H_t$ is the interaction history...').
- **[writing]** Section 2.2 (Eq. 3) uses the symbol $\mathcal{V}_j$ and the term 'available_views' without defining the set of valid view types. While 'full_frame' etc. appear in Eq. 4, the reader encounters $\mathcal{V}_j$ first without knowing it represents a set of view identifiers. Define $\mathcal{V}_j$ explicitly in the text preceding Eq. 3.
- **[writing]** Section 2.3 (Eq. 5) introduces $\mathcal{T}_d$, $\mathcal{C}_d$, $\mathcal{A}_d$, $\mathcal{R}_d$, and $\widehat{\mathcal{M}}_d$ as intermediate sets in the generator pipeline without defining what each set contains (e.g., clustered trajectories, abstracted procedures). Add a sentence defining these intermediate variables before or after Eq. 5.
- **[writing]** Section 2.4 (Eq. 6) uses $J_t$ and $R_t$ without definition. The text says 'Stage 1 (view selection)' but does not explicitly state that $J_t$ is the set of selected skill indices and $R_t$ is the set of selected view types. Define these variables in the text immediately preceding Eq. 6.
- **[writing]** Section 2.3 introduces 'Phase 0' through 'Phase 4' in Eq. 5 and the surrounding text, but does not define what each phase does (e.g., 'Phase 0: clustering', 'Phase 1: abstraction'). An adjacent reader cannot follow the pipeline flow. Add a brief parenthetical or list defining the function of each phase.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 3.2 (Eq. 4), the generator pipeline claims to 'merge overlapping candidates' in Phase 2, yet the text does not specify the logical criteria for determining overlap between multimodal packages (e.g., visual similarity vs. textual procedure). Without this definition, the claim that the pipeline produces 'generalized' skills lacks a supporting mechanism.
- **[writing]** Section 4.2 claims MMSkills reduce interaction steps by avoiding 'unnecessary exploration,' but Table 3 shows that MMSkills increase the average number of skill calls per case (e.g., Qwen3-235B: 0.49 -> 0.92). The paper does not logically reconcile how increased consultation frequency leads to reduced total steps without explicitly arguing that each consultation prevents multiple failed actions.
- **[science]** The 'Branch Loading' mechanism (Section 3.3) asserts that it prevents 'over-anchoring' to reference screenshots. However, the prompt templates in Appendix A.3 (Stage 2) instruct the model to 'align the selected evidence with the live state.' The paper lacks a logical argument or ablation proving that this alignment process successfully prevents anchoring compared to a baseline where the model simply ignores the reference images.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Undefined Overlap Criteria (Item 5221a0349f87): In Section 3.2, the generator pipeline describes a "merge overlapping candidates" step in Phase 2. However, the manuscript does not specify the logical or mathematical criteria used to determine if two multimodal packages "overlap." Is it based on visual similarity of keyframes, textual similarity of procedures, or semantic overlap of state cards? Without this definition, the claim that the pipeline produces "generalized" skills is unsupported, as
- **[writing]** Unreconciled Metric Contradiction (Item a813b195680b): Section 4.2 argues that MMSkills reduce total interaction steps by avoiding "unnecessary exploration." However, Table 3 explicitly shows that the "Calls/case" metric increases from 0.71 (Text-only) to 0.96 (MMSkills) for the Gemini 3 Flash model. The text does not provide the necessary logical bridge to explain how *more* skill consultations result in *fewer* total steps. The argument implicitly assumes that each consultation prevents multip
- **[writing]** Unproven Anti-Anchoring Mechanism (Item f41df7885fd2): Section 3.3 claims the "Branch Loading" mechanism prevents "over-anchoring" to reference screenshots. Conversely, the prompt templates in Appendix A.3 (Stage 2) explicitly instruct the model to "align the selected evidence with the live state." The paper offers no logical argument or ablation study demonstrating that this alignment process successfully prevents anchoring compared to a baseline where the model ignores reference images. The cl

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims 'consistent improvements across model families,' but Table 1 only shows Gemini and Qwen. Include results for GLM/Kimi in the main table or hedge to 'tested families' to support the generalization.
- **[writing]** Title/Abstract imply 'general visual agents,' but experiments are limited to GUI and two games. Add a limitation explicitly restricting the scope to screen-based and game environments, excluding robotics or video.
- **[writing]** Abstract claims the method 'complements internal priors' generally, but evidence is limited to OpenCUA-derived skills on specific benchmarks. Narrow the claim to 'complements priors in screen-based task execution'.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a framework for multimodal skills in visual agents, utilizing screenshots and state cards derived from public trajectories. From a safety and ethics perspective, the work is low-risk. The authors explicitly address the primary safety concern in the "Broader Impact" section (Appendix), acknowledging that storing screenshots carries privacy risks and stating that skills are constructed from "public non-evaluation trajectories" to avoid private data.

The methodology relies on existing public benchmarks (OSWorld, macOSWorld) and public trajectory datasets (OpenCUA), which are standard in the field and do not involve new human-subjects data collection requiring IRB approval. The "Use of LLMs" section clarifies the role of models in generation and evaluation without raising undisclosed conflicts.

While the capability to automate desktop tasks is dual-use, the paper does not provide operational details for exploiting specific vulnerabilities, nor does it claim to bypass security controls. The "branch-loaded" mechanism is a retrieval-augmented generation technique, not a tool for deception or surveillance. The authors' brief discussion of privacy and the reliance on public data sources constitute an adequate disclosure for this type of research. No specific, non-trivial risks were identified that require further mitigation or disclosure.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The paper presents a compelling framework for multimodal skills, but the experimental design currently lacks the rigor required to support the headline claims of consistent improvement. 1. Lack of Variance Reporting (Single-Run Risk): The primary results in Table 1 (OSWorld) and Table 2 (macOSWorld) report single-point accuracy percentages (e.g., 50.11% vs 44.08%). There is no mention of the number of random seeds used, standard deviations, or confidence intervals. In visual agent benchmarks, pe

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** Tables 1 and 2 report single-point success rates (e.g., 59.91%) without any measure of uncertainty (SD, SE, or CI) or number of seeds. In stochastic LLM agent evaluations, a single run is insufficient to distinguish signal from noise. Report mean ± SD over ≥3 independent seeds for all reported metrics, or explicitly state that results are from a single run and treat them as illustrative rather than definitive.
- **[science]** The paper claims 'consistent improvements' and highlights specific gains (e.g., +6.44% in Table 1) but provides no statistical hypothesis tests (e.g., paired t-test, Wilcoxon signed-rank) or p-values to support these claims. Without a test, it is impossible to determine if the observed differences are statistically significant or due to random variance. Add a formal significance test comparing 'MMSkills' vs. 'No skill' and 'Text-only' conditions.
- **[science]** Table 1 and 2 compare MMSkills against baselines across multiple domains (5-6 columns) and models. The paper highlights the 'best' performing cells without applying a correction for multiple comparisons (e.g., Bonferroni, Holm, or FDR). With ~12-15 pairwise comparisons, the false positive rate is inflated. Apply a multiple-comparison correction to the reported p-values or rephrase claims to avoid implying significance where none has been tested.
- **[writing]** Table 3 reports 'Steps' and 'ΔSteps' with two decimal places (e.g., 11.86, -1.25) based on a sample size of 360 tasks. While the mean is precise, the lack of standard deviation or standard error makes the precision misleading. Report the variability (SD or SE) for step counts to allow readers to assess the stability of the efficiency gains.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper demonstrates a high standard of academic writing, with a clear logical flow and well-structured arguments. The introduction effectively sets up the problem of multimodal procedural knowledge, and the methods section provides a detailed, albeit dense, explanation of the framework. The writing is generally precise, and the use of technical terminology is appropriate for the target audience. However, there are minor issues with sentence structure and flow that, while not impeding understa

## paper_reviewer_writing_quality — verdict: accept

The manuscript demonstrates a high standard of academic writing with a clear logical flow and well-structured arguments. The introduction effectively establishes the problem of multimodal procedural knowledge, and the methods section provides a detailed, albeit dense, explanation of the framework. The prose is generally precise, and technical terminology is used appropriately for the target audience.

Regarding the prior review, the specific concern about "minor issues with sentence structure and flow" appears to have been addressed or was likely a misinterpretation of the dense technical content. The current text reads smoothly; sentences are grammatically sound, and paragraphs maintain a single focus. Transitions between sections (e.g., from the abstract to the introduction, and from methods to experiments) are logical and well-signposted. The abstract accurately summarizes the method, results, and conclusion without omitting key components.

No new readability issues were introduced in this revision. The text allows a reader to move through the argument without friction, re-reading, or guessing the intent of specific sentences. The writing quality is sufficient for publication.
