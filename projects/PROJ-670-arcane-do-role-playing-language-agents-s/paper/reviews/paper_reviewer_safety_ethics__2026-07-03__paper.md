---
action_items:
- id: b0d5cb1495fe
  severity: writing
  text: The Limitations section (Sec. 6) acknowledges that 'period-bound social attitudes'
    in 19th/early-20th-century texts may be reproduced. However, the paper lacks a
    concrete mitigation strategy for when RPLAs generate hate speech, slurs, or harmful
    stereotypes inherent to the source material (e.g., in 'Anna Karenina' or 'The
    Underdogs'). Explicitly state how the evaluation protocol handles or filters such
    outputs to prevent the benchmark from inadvertently promoting harmful content.
- id: 28d002a46382
  severity: writing
  text: The dataset construction relies on LLMs to generate 'psychologically impactful
    events' and 'character arcs' (Sec. 3.1). There is no mention of human oversight
    regarding the potential for these LLMs to hallucinate or introduce biased interpretations
    of sensitive psychological traits or traumatic events. Clarify the human-in-the-loop
    validation process for these specific psychological constructs to ensure they
    do not reinforce harmful stereotypes.
- id: ca06a134f46a
  severity: writing
  text: The 'Out-of-World' probes (Sec. 3.2) transpose characters into non-source
    eras. While creative, this risks generating scenarios where characters are placed
    in contexts that could be interpreted as trivializing historical tragedies or
    misrepresenting marginalized groups. The paper should confirm that these probes
    were screened for potential ethical violations or offensive content before evaluation.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:14:46.463647Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses a novel and important area in evaluating Role-Playing Language Agents (RPLAs) by focusing on temporal character consistency. However, from a safety and ethics perspective, there are significant gaps regarding the handling of harmful content inherent in the source material and the generation of new scenarios.

First, the **Limitations section** (Section 6, lines 240-242) briefly notes that "Period-bound social attitudes in source texts may be reproduced." This is a critical safety concern. Many of the 17 novels included (e.g., 19th-century literature) contain explicit racism, sexism, and other forms of hate speech or discriminatory attitudes. The paper does not describe a mechanism to filter, flag, or handle these outputs during the evaluation process. If the benchmark rewards an RPLA for accurately mimicking a character's use of slurs or discriminatory logic, it risks normalizing such behavior. The authors must explicitly state how they mitigate the risk of the benchmark generating or validating harmful content.

Second, the **dataset construction pipeline** (Section 3.1) relies heavily on LLMs to extract "psychologically impactful events" and define "Character Arcs." There is no detailed description of human oversight specifically regarding the *interpretation* of sensitive psychological states or traumatic events. If the LLMs used for construction hallucinate or introduce biased interpretations of mental health or trauma, the resulting benchmark could propagate these biases. The authors should clarify the extent of human validation for these specific psychological constructs to ensure they do not reinforce harmful stereotypes.

Finally, the **Out-of-World probes** (Section 3.2) involve transposing characters into eras or settings not present in the source text. While this tests generalization, it introduces a risk of generating scenarios that could be offensive or trivialize historical tragedies (e.g., placing a character from a war novel in a context that minimizes the conflict). The paper should confirm that these generated probes underwent a safety review to ensure they do not violate ethical norms regarding the depiction of sensitive historical or social issues.

Addressing these points is essential to ensure the benchmark does not inadvertently become a tool for generating or validating harmful content.
