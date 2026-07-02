---
action_items:
- id: 1ee098d69887
  severity: writing
  text: The paper presents a systematic study of long-context continued pre-training
    for LVLMs, focusing on data curation and training design. From a safety and ethics
    perspective, several areas require clarification and potential revision. First,
    the construction of the document pool (Sec 4.1) involves 1.5 million PDFs from
    "multiple sources," including academic papers, books, and technical manuals. The
    paper lacks sufficient detail on the legal and ethical basis for collecting and
    using this data. Spe
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:41:00.802498Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a systematic study of long-context continued pre-training for LVLMs, focusing on data curation and training design. From a safety and ethics perspective, several areas require clarification and potential revision.

First, the construction of the document pool (Sec 4.1) involves 1.5 million PDFs from "multiple sources," including academic papers, books, and technical manuals. The paper lacks sufficient detail on the legal and ethical basis for collecting and using this data. Specifically, it is unclear whether these documents are in the public domain, open-licensed, or if their use falls under fair use for research. There is a significant risk of copyright infringement if the data includes copyrighted material without proper authorization. The authors should provide a clear statement on data provenance, licensing, and any steps taken to ensure compliance with copyright laws. Additionally, if any of the documents contain personally identifiable information (PII) or sensitive data, the authors must describe how this data was handled to protect privacy.

Second, the data synthesis pipeline relies on an OCR expert model to parse documents and generate QA pairs (Sec 4.1, 4.2). While the authors mention a manual verification step for a small sample of generated QA pairs (App 7.3), there is no discussion of the potential biases or errors introduced by the OCR model. OCR models can introduce errors, especially with complex layouts or low-quality images, which could propagate into the training data and affect the model's performance. Furthermore, the use of an AI model to generate training data raises concerns about the quality and reliability of the generated content. The authors should address these potential issues and consider implementing more robust quality control measures, such as larger-scale human verification or automated error detection.

Third, the evaluation methodology relies heavily on LLM-based judging for scoring answers (App 7.1). While this approach can handle semantically equivalent answers, it introduces the risk of bias in the judge model. The paper does not discuss how the judge model was selected or trained, nor does it address the potential for data contamination if the judge model was trained on similar data as the evaluated model. The authors should provide more details on the evaluation protocol and consider using multiple judges or human evaluation to mitigate these risks.

Finally, the paper mentions using webpages from OBELICS for multimodal needle retrieval (App 7.4). The authors should clarify if any PII or sensitive data was present in these webpages and how it was handled to ensure privacy compliance. Additionally, the use of webpages raises concerns about the potential for the model to learn and reproduce harmful or biased content present on the web. The authors should discuss any steps taken to filter or mitigate such content.

In summary, while the paper makes a valuable contribution to the field of long-context LVLMs, it requires revisions to address the ethical and safety concerns related to data collection, synthesis, and evaluation. The authors should provide more transparency and detail on these aspects to ensure the responsible development and deployment of their models.
