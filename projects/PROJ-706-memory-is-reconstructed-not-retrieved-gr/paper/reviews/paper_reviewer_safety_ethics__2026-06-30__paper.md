---
action_items:
- id: 3dad0ac2a7be
  severity: writing
  text: The paper lacks explicit IRB or ethical approval statements regarding the
    use of human conversation data in the LoCoMo and LongMemEval benchmarks. Section
    5.1 mentions these datasets but does not clarify if the data was anonymized, if
    consent was obtained for secondary research use, or if the data contains PII.
    A statement confirming compliance with data privacy standards and the removal
    of sensitive personal information is required.
- id: 75043a90d906
  severity: writing
  text: The 'Impact Statement' (Section 1) dismisses privacy concerns as generic.
    However, MRAgent's active reconstruction may infer sensitive user details (e.g.,
    health, finance) not explicitly queried. The authors must expand this section
    to discuss specific mitigation strategies for privacy leakage and the risks of
    'over-reconstruction' of sensitive user profiles.
- id: b81d2b1cfa18
  severity: writing
  text: The system prompt in the Appendix (Section 7) instructs extracting 'personal_sentences'
    and 'personal_information' without mentioning safeguards against sensitive attributes
    (e.g., medical history) or user opt-out mechanisms. The paper should address how
    the system handles sensitive data categories and implements data minimization
    or user-controlled deletion.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:26:37.211442Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses the critical area of long-term memory in LLM agents, a domain with significant implications for user privacy and data governance. While the technical contribution is notable, the manuscript currently lacks sufficient detail regarding the ethical handling of the data used for training and evaluation, as well as the specific risks associated with the proposed "active reconstruction" mechanism.

First, regarding data privacy and consent: The experiments rely on the LoCoMo and LongMemEval benchmarks (Section 5.1), which consist of extended human-LLM dialogues. The paper does not state whether these datasets were collected with explicit informed consent for research purposes, nor does it confirm if Personally Identifiable Information (PII) was rigorously anonymized prior to use. Given the sensitive nature of long-term conversational data, the authors must include a statement confirming that the data usage complies with relevant ethical guidelines (e.g., IRB approval or equivalent institutional review) and that appropriate de-identification measures were taken.

Second, the "Impact Statement" (Section 1) is insufficiently cautious. The authors state that privacy concerns "are not specific to our method," which underestimates the unique risks of active reconstruction. Unlike passive retrieval, MRAgent infers new cues and associations, potentially reconstructing sensitive user profiles or inferring private details (e.g., health status, financial struggles) that were never explicitly stated but are implied by the graph traversal. The authors should expand this section to discuss the risk of "hallucinated privacy" or the exposure of latent sensitive attributes and propose specific mitigation strategies, such as sensitivity filters or user-controlled memory scopes.

Finally, the system prompts in the Appendix (Section 7) explicitly instruct the model to extract "personal_sentences" and "personal_information." There is no discussion of how the system handles sensitive categories of data or whether it allows users to opt-out of specific types of memory storage. The paper should address these governance gaps, detailing how the system prevents the storage of sensitive PII and how users can manage or delete their reconstructed memory graphs.
