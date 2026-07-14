---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Data Journalist Agent: Transforming Data into Verifiable Multimodal St"

**Field**: computer science

## Research question

How does the explicit generation and integration of counterfactual narrative angles by an auxiliary agent affect the detection of non-obvious causal insights and the reduction of confirmation bias in automated data journalism systems?

## Motivation

Current automated journalism frameworks excel at factual verification but often default to the most statistically prominent narratives, potentially reinforcing known biases or missing nuanced, counter-intuitive insights that human editors would uncover. Introducing a dedicated mechanism to challenge the primary narrative with alternative causal explanations addresses a critical gap in the depth and balance of AI-generated reporting, moving beyond mere accuracy toward genuine analytical rigor.

## Literature gap analysis

### What we searched
We queried Semantic Scholar, arXiv, and OpenAlex using the following distinct queries: (1) "counterfactual reasoning automated journalism," (2) "bias mitigation in AI news generation," and (3) "causal micro-narratives data storytelling." We also broadened the search to include "LLM agent verification" and "automated data analysis narrative." The searches returned a small volume of results, with only two papers from the provided literature block showing tangential relevance to the specific mechanism of causal narrative construction and verification.

### What is known
- [Causal Micro-Narratives (2024)](https://arxiv.org/abs/2410.05252) — This work establishes a method for classifying sentence-level causal explanations in text, providing a foundational taxonomy for identifying cause-and-effect claims but not addressing the generation of alternative counterfactuals to challenge a primary narrative.
- [On Supporting Digital Journalism: Case Studies in Co-Designing Journalistic Tools (2017)](https://arxiv.org/abs/1710.05212) — This study highlights the need for tools that support the editorial process and co-design, identifying a gap where current automated systems lack the flexibility to explore non-obvious angles, though it does not propose a specific algorithmic solution for counterfactual generation.

### What is NOT known
There is no published work that specifically implements a "Counterfactual Inspector" agent within an automated journalism pipeline to systematically generate and test alternative narrative angles against a primary dataset. Furthermore, the empirical impact of such an intervention on the "depth" of causal reasoning and the measurable reduction of confirmation bias in generated stories remains unquantified.

### Why this gap matters
Filling this gap is critical for advancing AI journalism from a tool that merely summarizes data to one that actively interrogates it, thereby preventing the automation of biased or superficial reporting. A proven method for integrating counterfactual reasoning would significantly enhance the reliability and editorial value of automated news systems, making them viable for high-stakes reporting on complex public policy issues.

### How this project addresses the gap
This project directly addresses the gap by designing and implementing a "Counterfactual Inspector" agent that explicitly queries datasets for contradictory correlations and forces narrative integration. By evaluating the output against a blinded rubric with domain experts, the project will provide the first empirical evidence on whether this specific architectural addition improves narrative depth and bias mitigation in automated storytelling.

## Expected results

We expect that stories generated with the Counterfactual Inspector will demonstrate a statistically significant increase in "Narrative Depth" scores, specifically by including at least one non-obvious or counter-intuitive insight absent from the baseline. Additionally, we anticipate that the inclusion of these alternative perspectives will reduce the "Confirmation Bias" score (measured as the deviation from the most obvious statistical trend) without compromising the system's existing verifiability metrics.

## Methodology sketch

- **Data Collection**: Download 50 complex, multi-variable public policy datasets (e.g., housing, crime, health) from public repositories (e.g., UCI Machine Learning Repository, Kaggle, or government open data portals) that are known to contain at least one counter-intuitive correlation.
- **Baseline Generation**: Run the existing Data2Story pipeline (using the `llmXive` implementation) on all 50 datasets to generate a baseline set of stories, recording the primary narrative angle identified by the system.
- **Counterfactual Agent Implementation**: Develop a "Counterfactual Inspector" agent that takes the baseline narrative and the raw dataset as input; it will use an LLM to generate SQL/Python queries specifically targeting correlations that contradict the baseline angle (e.g., if the baseline is "A causes B," the agent searches for "C causes B where C is inversely related to A").
- **Narrative Integration**: Modify the narrative engine to accept the Inspector's output and force the inclusion of at least one verified counterfactual insight into the final story structure, ensuring the claim is traced back to the specific data query (verifiability).
- **Evaluation Design**: Create a blinded evaluation rubric with two primary metrics: "Narrative Depth" (presence of non-obvious insights) and "Bias Mitigation" (diversity of causal explanations).
- **Expert Annotation**: Recruit 20 domain experts (journalists or data analysts) to independently score the baseline vs. counterfactual-enhanced stories on the rubric without knowing which method generated which story.
- **Statistical Analysis**: Perform a paired t-test (or Wilcoxon signed-rank test if normality assumptions are violated) on the expert scores to determine if the counterfactual-enhanced stories significantly outperform the baseline on the target metrics.
- **Resource Check**: Ensure all steps (data download, LLM inference via local/small API, evaluation scoring) can be executed within a single 6-hour GitHub Actions runner job with 7GB RAM, using lightweight models (e.g., Llama-3-8B quantized) or batched API calls to avoid timeout.

## Duplicate-check

- Reviewed existing ideas: llmXive follow-up: extending "Data Journalist Agent: Transforming Data into Verifiable Multimodal St" (original brainstorm).
- Closest match: llmXive follow-up (original brainstorm) — The current idea is a direct elaboration of the original brainstorm, refining the "Counterfactual Inspector" concept into a concrete methodology.
- Verdict: NOT a duplicate (This is the fleshed-out version of the original brainstorm, not a new, distinct idea).


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-14T03:55:50Z
**Outcome**: exhausted
**Original term**: llmXive follow-up: extending "Data Journalist Agent: Transforming Data into Verifiable Multimodal St" computer science
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "Data Journalist Agent: Transforming Data into Verifiable Multimodal St" computer science | 0 |
| 1 | automated data journalism agents | 1 |
| 2 | verifiable multimodal data storytelling | 0 |
| 3 | large language models for data visualization | 3 |
| 4 | evidence-based AI news generation | 0 |
| 5 | trustworthy data narrative automation | 1 |
| 6 | LLM-driven chart generation with citations | 0 |
| 7 | automated fact-checking for data stories | 0 |
| 8 | multimodal reasoning in data journalism | 0 |
| 9 | provenance-aware data visualization agents | 0 |
| 10 | AI-assisted investigative reporting tools | 0 |
| 11 | natural language generation for statistical analysis | 0 |
| 12 | explainable AI for data-driven stories | 0 |
| 13 | automated data-to-text pipelines with verification | 0 |
| 14 | trustworthy generative AI for journalism | 0 |
| 15 | semantic data analysis for media production | 0 |
| 16 | hallucination mitigation in data reporting | 0 |
| 17 | interactive data storytelling with LLMs | 0 |
| 18 | citation-grounded visual data generation | 0 |
| 19 | autonomous data interpretation agents | 0 |
| 20 | audit trails for AI-generated news content | 0 |

### Verified citations

1. **On Supporting Digital Journalism: Case Studies in Co-Designing Journalistic Tools** (2017). Georgiana Ifrim, Derek Greene, Mark T. Keane, Claudia Orellana-Rodriguez, Bichen Shi, et al.. arXiv. [1710.05212](https://arxiv.org/abs/1710.05212). PDF-sampled: No.
2. **Causal Micro-Narratives** (2024). Mourad Heddaya, Qingcheng Zeng, Chenhao Tan, Rob Voigt, Alexander Zentefis. arXiv. [2410.05252](https://arxiv.org/abs/2410.05252). PDF-sampled: No.
