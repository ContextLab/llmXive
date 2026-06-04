---
action_items: []
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T13:23:27.228963Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.5
verdict: accept
---

**Overreach Review Feedback**

This survey chapter maintains appropriate methodological scope throughout. The paper reviews multiple approaches (GLMs, MVPA, RSA, hierarchical models, Gaussian processes, alignment methods, ISC/ISFC) without over-claiming the superiority of any single method.

**Strengths regarding overreach:**
- Limitations are honestly stated: electrode coverage is acknowledged as "poor compared to fMRI" (Section: Modality-specific challenges, Fig.~\ref{fig:electrodes})
- Patient population constraints are explicitly noted: "neurosurgical patients with serious neurological symptoms" with potential "brain abnormalities" affecting generalizability (Summary section)
- The paper appropriately qualifies claims: "Cognitive neuroscience is still decades away from being able to link neural and stimulus features at high levels of detail"

**Minor concerns:**
- The statement "intracranial recordings are ideally suited to studying stimulus-driven neural activity patterns" (Section: Invasive approaches) could be slightly softened given the acknowledged coverage limitations
- The claim that "with n = 5023 electrodes from m = 53 patients, data from most of the brain is possible" (Fig.~\ref{fig:electrodes} caption) may overstate spatial completeness given the sparse, clinically-driven electrode placement

However, these are minor qualifications within an otherwise appropriately scoped survey. The paper does not make unsupported claims about methodological capabilities or generalizability beyond what the evidence supports. No new overreach issues introduced compared to the prior review bar.

**Verdict rationale:** No significant over-claiming detected. Limitations are transparently acknowledged. Scope matches the survey chapter format.
