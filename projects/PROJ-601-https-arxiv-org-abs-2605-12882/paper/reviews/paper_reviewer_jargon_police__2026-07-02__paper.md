---
action_items:
- id: b03399f1066e
  severity: science
  text: The manuscript is heavily laden with domain-specific jargon and unexplained
    acronyms that significantly hinder accessibility for non-specialist readers, including
    those in law, medicine, or general policy who are the intended beneficiaries of
    "trustworthy document intelligence." First, the abstract and introduction introduce
    MLLMs (Multimodal Large Language Models) and Doc-VQA (Document Visual Question
    Answering) without fully expanding them or providing a brief, plain-language definition.
    "Doc-
artifact_hash: 567bb319ad9aec08be02c875d29027d6ab5aa636652eb3a41f2a0b1e3b7ef794
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:18:48.780988Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: full_revision
---

The manuscript is heavily laden with domain-specific jargon and unexplained acronyms that significantly hinder accessibility for non-specialist readers, including those in law, medicine, or general policy who are the intended beneficiaries of "trustworthy document intelligence."

First, the abstract and introduction introduce **MLLMs** (Multimodal Large Language Models) and **Doc-VQA** (Document Visual Question Answering) without fully expanding them or providing a brief, plain-language definition. "Doc-VQA" is particularly opaque; it should be introduced as "a type of task where models answer questions about documents using both text and images." Similarly, **SAA** (Strict Attributed Accuracy) is introduced in the abstract without its full name, and the acronym is used repeatedly before the definition is clearly established.

The paper frequently uses technical terms without explanation. For instance, **"element-level bounding-box citations"** (Abstract, Introduction) is dense; it could be simplified to "precise visual markers (bounding boxes) around specific text or image elements." The term **"masking ablation"** (Abstract) is a machine learning technique that should be described as "a process where specific evidence sections are hidden to test if the model still answers correctly."

Throughout the text, terms like **"synergizing"** (Section 3), **"instrumentation"** (Abstract), **"granularity"** (Section 1, 3), **"black-box reasoning"** (Section 1), **"faithfulness"** (Section 1), **"traceability"** (Section 1), and **"hallucination"** (Section 1) are used. While standard in AI research, they are jargon to a broader audience. "Synergizing" should be "combining"; "instrumentation" should be "tools"; "granularity" should be "level of detail"; "black-box" should be "reasoning that cannot be seen"; "faithfulness" should be "accuracy"; "traceability" should be "ability to track back to the source"; and "hallucination" should be "making up information" in initial mentions.

The evaluation section introduces **IoU** (Intersection over Union) without definition, and uses **SAA**, **Rec.**, **Rel.**, and **Ans.** as variables without consistently spelling them out in the text or tables. The appendix introduces **SFT** (Supervised Fine-Tuning), **agentic frameworks**, **vector search**, **context window capacities**, **rejection sampling**, **trajectory**, **token limits**, **position embedding constraints**, **non-parametric statistical test**, **Likert scale**, **BBox**, **OCR**, **PDF**, **LLM**, **VQA**, **RAG**, **F1-score**, **Page_recall**, **Page_acc**, **Recall_min**, **Recall_EM**, **Prec_min**, **F1_min**. Many of these are either undefined or defined too late.

The paper also uses **"distilled"** (Section 3) in the context of template generation, which is jargon for "simplified" or "extracted." **"Coarse-grained"** and **"fine-grained"** are used repeatedly without clear definitions for a general audience. **"Agentic frameworks"** should be "systems that use tools." **"Vector search"** should be "search based on meaning." **"Context window capacities"** should be "memory limits for input text." **"Rejection sampling"** should be "selecting only the best examples." **"Trajectory"** should be "sequence of steps." **"Token limits"** should be "limits on the amount of text the model can process." **"Position embedding constraints"** should be "limitations on how the model understands the order of words." **"Non-parametric statistical test"** should be "a statistical test that does not assume a specific data distribution." **"Likert scale"** should be "a 5-point rating scale."

The tables and figures also suffer from this issue, using abbreviations like **SAA**, **Ans.**, **Rel.**, **Rec.**, **Page.**, **Prec.**, **F1**, **Recall_min**, **Recall_EM**, **Prec_min**, **F1_min** without clear legends or definitions in the captions. The prompts in the appendix use terms like **"element-level"**, **"bbox"**, **"OCR"**, **"PDF"**, **"LLM"**, **"VQA"**, **"RAG"**, **"SFT"**, **"IoU"**, **"F1-score"**, **"Page_recall"**, **"Page_acc"**, **"Recall_min"**, **"Recall_EM"**, **"Prec_min"**, **"F1_min"** without defining them for the model or the reader.

To make this paper accessible to its intended audience, all acronyms must be defined at first use, and technical jargon must be replaced with plain language or clearly explained. The current level of jargon creates a significant barrier to entry for non-specialists.
