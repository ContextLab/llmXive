---
action_items:
- id: 3c545f59d133
  severity: writing
  text: The paper addresses safety and ethics primarily through its discussion of
    LLM bias and the assumptions required for the proposed "randomized-direction"
    oracle to function correctly. The authors acknowledge in the Abstract and Limitations
    (Section 6) that real-world LLM APIs may exhibit hidden state, non-stationarity,
    or asymmetric position bias, which could violate the theoretical guarantees of
    their method. While the authors perform a sensitivity analysis on autocorrelation
    (Appendix), they do
artifact_hash: 8b4e5d074a64eaa78e7927259e08b3cc001daf353c2dc417958eda25d90e918a
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:11:49.180909Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses safety and ethics primarily through its discussion of LLM bias and the assumptions required for the proposed "randomized-direction" oracle to function correctly. The authors acknowledge in the Abstract and Limitations (Section 6) that real-world LLM APIs may exhibit hidden state, non-stationarity, or asymmetric position bias, which could violate the theoretical guarantees of their method. While the authors perform a sensitivity analysis on autocorrelation (Appendix), they do not sufficiently discuss the *safety* consequences of these violations in a production RAG setting. If the assumption of symmetric bias fails, the system could systematically demote or promote documents based on non-relevant features (e.g., author gender, political leaning), leading to unfair or harmful retrieval outcomes. The manuscript should explicitly expand the "Limitations" section to include a risk assessment of deploying this method when the underlying LLM exhibits asymmetric bias, particularly in sensitive domains.

Regarding data privacy, the paper utilizes the BEIR and TREC DL benchmarks. While these are standard public datasets, the authors use a third-party API (OpenAI GPT-4-turbo) to process the text. The manuscript does not explicitly state whether the documents were screened for Personally Identifiable Information (PII) or sensitive content before being sent to the API. Given the potential for public datasets to contain inadvertently leaked PII, the authors should confirm that no such data was exposed to the external API or clarify the data usage policy of the benchmark providers in this context.

Finally, the "randomized-direction" oracle is presented as a cost-saving measure that relies on statistical cancellation of bias. The authors should briefly discuss the ethical implications of this trade-off: while it improves efficiency, it introduces a risk that individual ranking decisions are based on a single, potentially biased inference rather than a consensus. In high-stakes applications (e.g., medical or legal retrieval), this reduction in robustness could be a safety concern that warrants a more explicit warning in the text.
