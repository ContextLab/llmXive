---
action_items:
- id: b4ebc1bd27ca
  severity: writing
  text: Abstract/Intro claim NatureBench is 'the first' to combine paper-sourced tasks,
    science, and optimization. Table 1 shows MLS-Bench also targets 'method invention'
    on research problems. Narrow the claim to 'first to use published SOTA anchors
    from Nature-family papers' to match the evidence.
- id: e57ff710c6ce
  severity: writing
  text: Abstract contrasts 'methodological translation' with 'genuine scientific invention,'
    but Section 5.1 only measures 'domain-reasoned alternatives' (8.3%) and 'method-aligned
    solutions' (9.0%). Rephrase to 'rather than proposing novel domain-specific methods'
    to avoid implying a measured category that doesn't exist.
- id: ec50fd5807f3
  severity: writing
  text: Conclusion states failures are 'not by task misunderstanding' (citing 3.1%).
    However, 'wrong method choice' (45.1%) can stem from misunderstanding. Soften
    to 'Failures are dominated by method selection and execution depth, with task
    misunderstanding being a minor factor' to match the data's granularity.
artifact_hash: a6c4bf4c6300b132fd82818749a0c8d087f9c694f2c1e50110083271605915a9
artifact_path: projects/PROJ-783-naturebench-can-coding-agents-match-the/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T00:32:19.496741Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a rigorous benchmarking framework, but several central claims in the abstract and conclusion slightly overreach the specific definitions and measurements provided in the results section.

First, the claim of being "the first" to combine paper-sourced tasks, scientific domains, and optimization-oriented evaluation (Abstract; Introduction) is not fully supported by Table 1. The table lists MLS-Bench, which evaluates "method invention" on "ML research problems" using "human baselines." While NatureBench is distinct in using *Nature-family* papers and *published SOTA* anchors, the broader claim of being the first to combine these three axes ignores the existence of MLS-Bench. The claim should be narrowed to specify the unique contribution: e.g., "the first to evaluate discovery on tasks distilled specifically from Nature-family papers using published SOTA as the anchor."

Second, the abstract and conclusion draw a sharp binary between "methodological translation" and "genuine scientific invention." Section 5.1 quantifies success modes as "supervised proxy prediction" (45.5%) versus "domain-reasoned alternatives" (8.3%) and "method-aligned solutions" (9.0%). The paper does not explicitly define or measure "genuine scientific invention" as a separate category from "method-aligned" work. By framing the results as a failure of "invention" versus a success of "translation," the rhetoric implies a capability gap that the data does not explicitly isolate. The text should be rephrased to reflect the measured categories: "agents succeed primarily by reducing scientific tasks to standard ML pipelines rather than by proposing novel domain-specific methods."

Finally, the conclusion states that failures are "not by task misunderstanding," citing the 3.1% "Understanding-layer" failure rate. However, the dominant "Method-layer" failures (61.1%) include "wrong method choice," which can sometimes stem from a misunderstanding of the task's scientific constraints. The absolute exclusion of task misunderstanding as a significant factor is slightly too strong given that the "Method-layer" category is broad. A more precise phrasing would be: "Failures are dominated by method selection and execution depth, with task misunderstanding accounting for a small fraction of cases."

These are primarily rhetorical refinements to ensure the scope of the claims matches the granularity of the evidence presented.
