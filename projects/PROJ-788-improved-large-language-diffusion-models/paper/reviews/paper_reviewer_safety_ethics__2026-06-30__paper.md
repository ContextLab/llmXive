---
action_items:
- id: 4d46ca039373
  severity: writing
  text: The paper states the SFT corpus contains 25B tokens but lacks a Data Statement
    detailing the sources, filtering criteria, and potential inclusion of personally
    identifiable information (PII) or copyrighted material. Add a section in the Appendix
    or main text describing data provenance and privacy safeguards to comply with
    standard AI ethics guidelines.
- id: 191649c45eac
  severity: writing
  text: The authors acknowledge 'repetitive reasoning loops' in the Appendix (lines
    430-435) but do not discuss the potential for the model to generate harmful content
    (e.g., self-harm instructions, hate speech) during these loops or in general open-ended
    generation. A brief discussion on safety alignment gaps and mitigation strategies
    for harmful outputs is required.
- id: 565b6efc06d1
  severity: writing
  text: The model weights are released on GitHub (Abstract, line 24). The paper must
    explicitly confirm that the release includes a safety evaluation report or that
    the model has undergone red-teaming to identify and mitigate dual-use risks before
    public distribution.
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T21:45:51.396302Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents iLLaDA, a large-scale diffusion language model, and claims significant performance improvements over prior work. From a safety and ethics perspective, the manuscript currently lacks sufficient transparency regarding data provenance and potential risks associated with the release of the model weights.

First, while the paper mentions a 25B-token instruction corpus for Supervised Fine-Tuning (Section 2.2, lines 135-145), it provides no details on the composition of this dataset. There is no Data Statement or equivalent section describing the sources of the data, the methods used for filtering (e.g., removal of PII, toxic content, or copyrighted text), or the consent mechanisms involved. Given the scale of the model and the public release of weights, this omission prevents a proper assessment of privacy risks and potential copyright infringement. The authors should add a dedicated section in the Appendix or main text detailing data curation and privacy safeguards.

Second, the Appendix (lines 430-435) acknowledges a specific failure mode where the model enters "repetitive reasoning loops." While the authors propose a heuristic to mitigate this, the paper does not address the broader safety implications of such behaviors. Specifically, there is no discussion on whether the model has been evaluated for generating harmful content (e.g., instructions for self-harm, violence, or hate speech) during these loops or in standard open-ended generation. The absence of a safety evaluation or red-teaming report raises concerns about the model's readiness for public release.

Finally, the abstract and conclusion highlight the release of model weights and code. Ethical AI practices require that such releases be accompanied by a clear statement on safety evaluations performed. The authors should explicitly state whether the model has undergone safety testing and if any known limitations regarding dual-use risks have been documented. Without these disclosures, the paper falls short of current best practices for responsible AI research.
