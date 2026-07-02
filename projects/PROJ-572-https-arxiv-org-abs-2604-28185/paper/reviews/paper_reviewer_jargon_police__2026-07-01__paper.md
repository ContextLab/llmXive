---
action_items:
- id: 3f3b919e0b0a
  severity: science
  text: The manuscript suffers from significant jargon overuse and a failure to define
    acronyms at first use, which creates a barrier for non-specialist readers and
    even researchers from adjacent fields. The paper frequently relies on community-specific
    shorthand and proprietary codenames without explanation. Specifically, the term
    "MM-DiT" is used repeatedly (e.g., Section 1, Section 2.1) without being expanded
    to "Multimodal Diffusion Transformer." Similarly, "VLM," "SFT," "MoE," "VQ," and
    "NFEs" appe
artifact_hash: 95c6cfb0cd885d3a15ec9e77a9e8d06788a35e40acba2d1245cdfd2be8660dc4
artifact_path: projects/PROJ-572-https-arxiv-org-abs-2604-28185/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:34:51.631040Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: full_revision
---

The manuscript suffers from significant jargon overuse and a failure to define acronyms at first use, which creates a barrier for non-specialist readers and even researchers from adjacent fields. The paper frequently relies on community-specific shorthand and proprietary codenames without explanation.

Specifically, the term "MM-DiT" is used repeatedly (e.g., Section 1, Section 2.1) without being expanded to "Multimodal Diffusion Transformer." Similarly, "VLM," "SFT," "MoE," "VQ," and "NFEs" appear without definition. In a survey paper intended to map the "New Era," assuming the reader already knows these acronyms contradicts the goal of providing a comprehensive roadmap.

Furthermore, the use of "Nano Banana" and "GPT-Image" as primary examples in Section 1 is problematic. These appear to be internal codenames or leaked model identifiers rather than public, verifiable model names. Using such terms excludes readers who do not follow specific industry leaks and undermines the paper's academic rigor. These should be replaced with formal model names or descriptive categories (e.g., "closed-source frontier models").

The text also relies on jargon-heavy phrasing such as "atomic mapping," "distillation-friendliness," and "in-the-wild stress testing." These terms should be replaced with plain English equivalents (e.g., "single-pass generation," "compatibility with distillation," "real-world stress testing") to improve clarity. The phrase "atomic mapping" in the title is particularly opaque; "direct generation" or "single-step synthesis" would be more accessible.

Finally, the distinction between "rectified-flow" and general "flow matching" is not clarified, despite being a central technical claim. The paper assumes the reader understands the specific nuances of this variant without providing a brief explanatory clause. A full revision is required to define all acronyms, replace proprietary codenames with public identifiers, and simplify the technical lexicon to ensure the survey is accessible to a broader scientific audience.
