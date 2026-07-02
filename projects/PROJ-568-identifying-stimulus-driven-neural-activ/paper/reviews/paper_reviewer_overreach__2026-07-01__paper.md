---
action_items:
- id: a010d0bf3708
  severity: writing
  text: The abstract and introduction imply the chapter presents new analysis or primary
    results by using phrases like 'we will consider' and 'examples serve to illustrate.'
    Since this is a tutorial/survey, the language should be adjusted to clearly frame
    these as methodological overviews rather than implying the chapter performs these
    identifications on new data.
- id: 5b03ba8908d1
  severity: writing
  text: Section 41.3.2 claims intracranial recordings are 'ideally suited' for identifying
    stimulus-driven activity. This overstates the case by ignoring that sparse, non-random
    electrode placement makes direct identification in unimplanted regions impossible.
    The text should clarify that 'identification' in those areas is entirely model-dependent
    and speculative, not a direct observation.
- id: 13951a241dbb
  severity: writing
  text: The conclusion claims neural insights elucidate cognition 'in ways that behavior
    alone cannot.' This is a broad generalization unsupported by a specific example
    in the text where iEEG identified a pattern that behavior failed to explain. A
    concrete citation or example is needed to avoid overreach regarding the unique
    explanatory power of these techniques.
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T23:29:26.270351Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript is a comprehensive survey of methods for identifying stimulus-driven neural activity in intracranial recordings. However, there are instances of over-claiming regarding the capabilities of the methods described and the nature of the chapter's contribution.

First, the abstract and introduction use language that suggests the chapter presents a novel application or a primary analysis of data (e.g., "we will consider a variety of... approaches," "examples... serve to illustrate"). Given that the text is a methodological review/tutorial, this phrasing risks over-claiming the chapter's status as a research report. The authors should clarify that the chapter *reviews* these approaches rather than *considers* them as active investigations within the text itself.

Second, in Section 41.3.2, the text asserts that intracranial recordings are "ideally suited" for identifying stimulus-driven patterns. While the high resolution is a strength, this claim overreaches by downplaying the critical limitation of sparse, non-random sampling. The text acknowledges electrode placement varies by clinical need, but it frames the solution (across-patient models) as a straightforward path to "full-brain maps." In reality, the inability to directly observe activity in unimplanted regions means that "identification" of stimulus-driven patterns in those regions is entirely model-dependent and speculative. The text should more honestly state that for unimplanted regions, identification is not direct but inferred, and thus subject to the specific biases of the alignment models (HTFA, Gaussian Processes) used.

Finally, the concluding remarks claim that these neural insights elucidate cognition "in ways that behavior alone cannot." While likely true in specific cases, the chapter does not provide a concrete example where a stimulus-driven pattern was identified *solely* via these methods where behavioral data was ambiguous or absent. Without such an example, this remains a broad, unsupported generalization about the superiority of the reviewed methods over behavioral analysis.
