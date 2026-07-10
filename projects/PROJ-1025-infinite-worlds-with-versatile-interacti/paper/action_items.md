# Automated-review action items — Infinite Worlds with Versatile Interactions

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Table 1 claims 'Ours' has 'Infinite' semantic interaction vs 'Few' for Genie 3. Verify if this binary distinction is supported by quantitative data or if it overstates the difference relative to the cited baselines' actual capabilities.
- **[science]** Section 1 and 5 claim 'no visible decay' over an hour-long rollout but provide no quantitative metrics (e.g., FVD, PSNR) to support this. Add a metric or soften the claim to 'qualitatively stable' based on the figure.
- **[science]** The abstract claims a 'guarantee' of 60 fps at 720p, but Section 5 reports no measured FPS or latency. Report the actual throughput or remove the word 'guarantee' to align with the evidence.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption is a sentence fragment ('generates infinite worlds...') rather than a complete descriptive sentence.
- **[writing]** Figure 1: The caption lacks a subject (e.g., 'Our model' or 'The system') to clarify what entity is performing the action.
- **[science]** Figure 4: The 'Cross-Attn Mask' grid shows a lower-triangular pattern for the autoregressive component (rows x0-x2 attending to a0-a2), but the caption states this component attends to 'chunk-wise prompts of lower-triangular pattern'. However, the grid also shows the bidirectional component (rows x0t-x2t) attending to aG and aB, but the caption says it attends to a 'global prompt'. The grid labels aG and aB are not defined in the caption or figure, making it unclear if they represent the global
- **[writing]** Figure 4: The 'Plücker Encoder' box is oriented vertically with text rotated 90 degrees, which is difficult to read and inconsistent with other horizontal text elements in the diagram.
- **[writing]** Figure 6: The text overlaying the video frames is illegible due to low resolution and poor contrast, preventing verification of the 'dynamic interactive floating windows' described in the caption.
- **[writing]** Figure 6: The caption describes a 'tracking-mode interface' with 'event cards,' but the figure lacks a clear UI frame or legend to distinguish the interface elements from the raw video content.
- **[science]** Figure 7: The caption claims 'controllable navigation of diverse protagonists,' but the visual evidence exclusively features an office chair as the protagonist; the 'diverse' aspect is not demonstrated in this specific figure.
- **[writing]** Figure 7: The image contains small, illegible UI icons in the bottom-left corners of the panels that are too blurry to read, obscuring potential control inputs or status indicators.
- **[science]** Figure 10: The caption claims to cover '20 distinct scenarios,' but the figure displays only 19 labeled frames (G01–G18 plus START and FINAL), creating a discrepancy between the text and the visual evidence.
- **[writing]** Figure 10: The timeline arrows in rows B and D point leftward (decreasing time), while rows A and C point rightward (increasing time). This zig-zag layout is not explained in the caption and may confuse the chronological progression of the 'one-hour journey'.
- **[science]** Figure 11: The caption claims 'Qualitative comparisons' but the figure contains no labels, legends, or text identifying which rows correspond to the authors' model versus the baselines, making the comparison impossible to evaluate.
- **[writing]** Figure 11: The caption is generic and does not describe the specific content shown (fire extinguisher and jet ski scenarios), failing to link the visual evidence to the claim of 'stable visual and physical consistency'.
- **[science]** Figure 12: The caption claims 'Qualitative comparisons on causal pretraining' and states the model shows 'stable performance compared with baselines,' but the figure displays three distinct video generation examples (eagle, fire extinguisher, jet ski) comparing MAGI, HY-World 1.5, and Lingbot-World 2.0. There is no visual evidence of 'causal pretraining' (e.g., ablation studies, loss curves, or specific pretraining artifacts) nor a clear baseline comparison demonstrating stability; the figure ap
- **[writing]** Figure 12: The caption is generic ('Our model shows stable performance...') and does not identify which of the three models (MAGI, HY-World 1.5, Lingbot-World 2.0) corresponds to 'Our model' or the 'baselines,' forcing the reader to guess the mapping.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.1 (Formulation): The symbol `κ` is not used, but the symbol `θ` is introduced in Equation 1 without explicit definition of its domain (e.g., 'where θ represents the learnable parameters of the world model'). While standard in ML, explicit definition at first use in the equation block aids adjacent-field readers.
- **[writing]** Section 3.2 (Pre-Training): The term 'Plücker embeddings' is used without a brief gloss (e.g., 'a six-dimensional representation of 3D rays'). While known in computer vision, an adjacent-field PhD in NLP or general ML may not immediately recall the specific geometric encoding.
- **[writing]** Section 3.2: The acronym 'MoBA' (Mixture of Bidirectional and Autoregressive) is introduced and defined, but the text later refers to 'MoBA mask' and 'MoBA' interchangeably. Ensure the first use of the acronym is immediately followed by the full name in the same sentence or clause for clarity.
- **[writing]** Section 4.2 (Agentic Interaction Harness): The term 'SAM-based' is used. While 'Segment Anything Model' is a well-known benchmark, the acronym 'SAM' is not explicitly expanded in the text (it appears in the caption of Fig 2 but not the prose). Expand 'SAM' to 'Segment Anything Model (SAM)' at first use in Section 4.2.
- **[writing]** Section 4.3 (Visual Quality Enhancement): The term 'KV Cache' is used without expansion. While standard in LLM/DiT literature, an adjacent-field reader might not know 'KV' stands for 'Key-Value'. Expand to 'Key-Value (KV) cache' at first use.
- **[writing]** Section 5.1: The phrase 'causal distilled' is used as a compound adjective. While understandable, it is slightly non-standard shorthand. Consider 'causally distilled' or 'distilled causal model' for grammatical precision, though this is a minor stylistic point.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 5.1 claims the model is the 'only system... that sustains high-resolution generation in real time,' but Table 1 lists 'M-G 3.0', 'D-W', 'LingBot-World', and 'HappyOyster' as having the 'Real-time' checkmark. The text's exclusivity claim contradicts the table's data. Either remove the 'only' qualifier or correct the table's 'Real-time' column for the baselines.
- **[writing]** Table 1 claims 'Semantic Interaction' for 'Ours' is 'Infinite,' while the text in Section 1 and 5 describes a 'rich, controllable action space' and 'versatile interactions.' The term 'Infinite' for a discrete set of actions (combat, archery, etc.) is logically imprecise and contradicts the finite nature of the described action vocabulary. Change 'Infinite' to 'Rich' or 'Diverse' to match the text.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims 'unbounded interaction horizon' and Section 1 claims 'infinite worlds,' but evidence is limited to a single hour-long qualitative demo (Fig 5). Replace 'unbounded/infinite' with 'extended (hour-scale)' or provide quantitative metrics proving stability beyond the tested hour.
- **[writing]** Table 1 and Abstract claim 'Infinite' semantic interaction, yet the evaluation (Sec 5) only demonstrates a specific set of actions (combat, archery, etc.) in a curated demo. 'Infinite' implies an unbounded vocabulary or capability never tested; narrow to 'rich and diverse' or 'expanded action space'.
- **[writing]** Abstract states the system 'guarantees rapid response time' for 720p/60fps. 'Guarantees' is a strong engineering claim not supported by the text, which only reports achieved throughput on specific hardware. Change to 'achieves' or 'demonstrates' and specify the hardware configuration.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a generative world model capable of real-time, infinite-horizon video synthesis with interactive control. From a safety and ethics perspective, the work does not exhibit the specific, non-trivial risks that would require mitigation or disclosure beyond standard practice for this subfield.

The data pipeline (Section 2) relies on a mix of self-collected egocentric videos, synthetic data from game engines (Unreal Engine), and large-scale web videos. The paper cites standard public datasets (e.g., Ego4D, EPIC-Kitchens) and does not claim to use private, sensitive, or non-public human-subject data requiring IRB approval. The use of web-scraped video is a common practice in the field; while the paper does not detail the specific licensing of every web source, it does not release a raw scraped dataset that would violate redistribution terms, nor does it claim to have bypassed specific Terms of Service in a way that creates a unique liability for this specific release. The synthetic data component further mitigates concerns regarding human consent.

The system's capabilities (combat, spell-casting, environmental manipulation) are framed within a simulated, generative context. While the "agentic harness" allows for autonomous behavior, the paper does not describe a system designed for real-world deception, surveillance, or the generation of actionable cyber/physical exploits. The "combat" and "shooting" actions are visual simulations within a generated world, not instructions for real-world harm. The paper does not provide operational details for generating harmful content (e.g., biological agents, specific malware) nor does it claim to have discovered a vulnerability in a live system that requires responsible disclosure.

There is no evidence of Personally Identifiable Information (PII) being released in the dataset or figures. The authors acknowledge limitations regarding long-term memory and physical consistency, but these are technical constraints rather than safety failures. As this is a third-party preprint, the absence of a formal "Broader Impacts" statement is noted but does not constitute a fatal flaw given the low-risk nature of the methodology and the standard norms for video generation papers. The work is a standard contribution to the field of generative world models with no foreseeable, unmitigated safety risks identified in the text.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The paper presents a compelling system for infinite-horizon interactive world modeling, but the evidentiary support for its central quantitative claims is currently insufficient to rule out alternative explanations such as cherry-picked demonstrations or baseline under-tuning. The most significant gap lies in the comparison of generation duration. Table 1 and Section 5.1 assert that the proposed model achieves "Hours (Infinite)" generation while competitors are limited to "Minutes." This is a ma

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The paper presents a system for infinite-horizon interactive world modeling but lacks the statistical rigor required to validate its quantitative claims. Section 5.1 asserts that the proposed model "matches or exceeds" baselines and is the "only system" to achieve real-time, infinite generation. These claims are supported exclusively by qualitative figures (Fig. 1, Fig. 4) and a single hour-long demo, with no reported numerical metrics (e.g., FVD, PSIM, throughput in fps) or measures of uncertai

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and readable, with a clear logical flow from problem statement to method and results. The abstract effectively summarizes the four key upgrades. However, there are several specific areas where the prose can be tightened to improve clarity and consistency. First, there is a terminological inconsistency in Section 2. The introduction lists "multi-granularity annotation" as the third stage, but the corresponding subsection is titled "Multi-dimensional Video An
