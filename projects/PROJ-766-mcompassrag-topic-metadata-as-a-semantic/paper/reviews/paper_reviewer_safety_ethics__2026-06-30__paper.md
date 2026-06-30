---
action_items:
- id: e0e292eb47cf
  severity: writing
  text: The paper presents MCompassRAG, a retrieval framework that leverages topic
    metadata to improve efficiency and accuracy. From a safety and ethics perspective,
    the reliance on Large Language Models (LLMs) for training data synthesis and teacher
    distillation introduces specific risks that are currently under-discussed. First,
    in Section 4.3 (Training with LLM-Teacher Distillation), the authors describe
    using GPT-4o to generate 20,000 synthetic query-chunk pairs and to assign relevance
    labels. While
artifact_hash: 5e7163c1713464843d620f2c37705ca96ededa7c235cfa3e5a0986f0a19b0aa7
artifact_path: projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T15:12:40.359686Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents MCompassRAG, a retrieval framework that leverages topic metadata to improve efficiency and accuracy. From a safety and ethics perspective, the reliance on Large Language Models (LLMs) for training data synthesis and teacher distillation introduces specific risks that are currently under-discussed.

First, in **Section 4.3 (Training with LLM-Teacher Distillation)**, the authors describe using GPT-4o to generate 20,000 synthetic query-chunk pairs and to assign relevance labels. While the prompts are provided in the appendix, they lack explicit instructions or constraints regarding safety, bias, or the handling of sensitive information. In domains like **LegalBench-RAG** and **Dragonball** (which includes medical and financial data), an LLM teacher could inadvertently generate synthetic queries that contain harmful stereotypes, hallucinate legal precedents, or misrepresent medical advice. If the student model is distilled from these potentially flawed or biased synthetic labels, it may inherit and amplify these errors. The authors should explicitly state whether safety filters were applied to the synthetic data or if the prompts included specific instructions to avoid generating harmful content.

Second, the use of **third-party APIs** (OpenRouter for GPT-4o and Qwen models) raises **data privacy and compliance concerns**. The paper does not clarify how the benchmark data (some of which may be proprietary or contain sensitive personal information) is handled when sent to external API providers. For instance, sending legal contracts or medical records to OpenAI's servers may violate the terms of service of the benchmark datasets or data protection regulations like GDPR or HIPAA. The authors must include a statement confirming that the data usage complies with all relevant licenses and that no sensitive data was exposed to third-party models in violation of privacy norms.

Finally, while the **Limitations** section mentions the dependency on topic model quality, it omits a discussion on **algorithmic bias**. Topic models trained on general corpora (like WikiWeb2M) can encode societal biases. If the topic centroids reflect biased associations, the retrieval system might systematically rank evidence related to certain demographics lower or misinterpret queries from marginalized groups. A brief acknowledgment of this risk and a plan for future bias auditing would strengthen the ethical rigor of the work.

These issues do not invalidate the technical contributions but require clarification to ensure the system is deployed responsibly.
