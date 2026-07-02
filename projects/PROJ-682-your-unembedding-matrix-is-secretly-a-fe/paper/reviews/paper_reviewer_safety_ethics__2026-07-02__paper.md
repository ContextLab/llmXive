---
action_items:
- id: 9fe96178ba3c
  severity: writing
  text: The Acknowledgments section (lines 1045-1050) explicitly states the work is
    supported by Lenovo Group and lists authors from Lenovo. The manuscript must include
    a formal Conflict of Interest (COI) statement clarifying the nature of this funding
    and any potential influence on the research design or results, as required by
    most academic venues.
- id: ce9d875f989e
  severity: writing
  text: The paper proposes a method to filter 'edge spectrum' subspaces to remove
    high-frequency tokens. While intended to improve semantic quality, this mechanism
    could be misused to systematically suppress specific topics, political viewpoints,
    or safety-critical keywords if the 'frequent token' definition is manipulated.
    The authors should add a discussion on the potential for dual-use in censorship
    or bias amplification and propose mitigation strategies.
- id: 5bd8a7cd954c
  severity: writing
  text: The methodology relies on approximating training corpus word frequencies using
    the RedPajama dataset (Section 3.2.1, lines 430-435) because the actual pretraining
    data is undisclosed. The authors should explicitly discuss the ethical implications
    of using a proxy dataset for reverse-engineering model internals, particularly
    if the proxy distribution differs significantly from the actual training data,
    potentially leading to unintended filtering of legitimate semantic content.
artifact_hash: 23484ba7b10cc08665875915717095ae222ff4767aae24d46926097ffc583ae4
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:55:18.814542Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on safety, ethics, and potential dual-use risks associated with the proposed "EmbedFilter" (EmbFilter) method.

The paper presents a novel technique to improve LLM text embeddings by filtering out subspaces associated with high-frequency tokens. While the primary goal is to enhance semantic representation and reduce dimensionality, the mechanism itself introduces specific safety and ethical considerations that require clarification.

First, the **Conflict of Interest (COI)** disclosure is insufficient. The Acknowledgments section (lines 1045-1050) reveals that the work is supported by Lenovo Group, and two authors (Heng Cui, Cong Li) are affiliated with Lenovo. Given that the method involves modifying how models represent text, which could have significant implications for enterprise search and content moderation, a formal COI statement detailing the nature of the funding and any potential commercial interests is necessary to maintain transparency.

Second, the **dual-use potential** of the method warrants discussion. The core mechanism involves identifying and suppressing "high-frequency" tokens to reduce anisotropy. While the authors frame this as removing "uninformative" tokens (e.g., "the", "a"), the definition of "frequent" is relative to the training distribution. A malicious actor could potentially adapt this technique to systematically suppress specific keywords, political viewpoints, or safety-critical terms by manipulating the frequency distribution or the "average token" definition. This could be used for covert censorship or to bias retrieval systems against certain topics. The authors should address this risk in the discussion or conclusion, perhaps by suggesting safeguards or limitations on the method's application.

Third, the **methodological reliance on proxy data** raises ethical questions regarding reproducibility and unintended consequences. The authors approximate the true training distribution using the RedPajama dataset (Section 3.2.1, lines 430-435) because the actual pretraining data is proprietary. If the proxy distribution differs significantly from the actual training data, the "edge spectrum" identified may not accurately represent the model's true biases or frequent tokens. This could lead to the unintended suppression of legitimate semantic content or the failure to remove actual noise, potentially degrading the model's performance or introducing new biases. The authors should explicitly discuss the limitations of using a proxy dataset for this reverse-engineering process and the potential ethical implications of deploying a method based on such approximations.

Finally, the paper does not mention **data privacy** concerns. While the method operates on model weights and public benchmarks, the underlying logic of identifying "average" tokens relies on assumptions about the training data. If the method were adapted to analyze private or sensitive datasets, the reverse-engineering process could potentially leak information about the training distribution. A brief statement on the privacy implications of analyzing model internals in this manner would be prudent.

In summary, while the technical contribution is sound, the manuscript requires minor revisions to address conflicts of interest, potential dual-use risks, and the ethical implications of using proxy data for model interpretation.
