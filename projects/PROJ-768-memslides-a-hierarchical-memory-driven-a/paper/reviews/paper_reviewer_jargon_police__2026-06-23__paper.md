---
action_items:
- id: e57aa3480787
  severity: writing
  text: "Replace or simplify overloaded terms such as \u201Chierarchical memory framework\u201D\
    , \u201Cpersonalized presentation agents\u201D, and \u201Cmulti\u2011turn localized\
    \ revision\u201D with clearer, more concrete language."
- id: a6b0403b468d
  severity: writing
  text: Define every acronym at first use (e.g., LLM, API, RAG, etc.) and consider
    removing those that are not essential to the core argument.
- id: 8c7861117ece
  severity: writing
  text: "Break up long, dense sentences (e.g., the abstract paragraph and several\
    \ sentences in the Introduction) to improve readability for non\u2011specialist\
    \ readers."
- id: 28495eacce2a
  severity: writing
  text: "Reduce reliance on field\u2011specific buzzwords like \u201Cscoped slide\u2011\
    local revision\u201D, \u201Cexecution contract\u201D, and \u201Cguarded patch\
    \ calls\u201D; replace them with plain descriptions of the process."
- id: db3d34a0ffe9
  severity: writing
  text: "Add brief explanatory footnotes or parenthetical remarks for technical concepts\
    \ such as \u201Ctool\u2011memory injection\u201D, \u201Cworking memory\u201D,\
    \ and \u201Cprofile\u2011memory routing\u201D to aid readers unfamiliar with agent\u2011\
    memory literature."
artifact_hash: d44b33b66588093736bc35436b4297f50da94321f7a3c7c12e6ba0ea57e820cd
artifact_path: projects/PROJ-768-memslides-a-hierarchical-memory-driven-a/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:20:42.144575Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is rich in specialized terminology that, while precise for experts, creates a barrier for a broader audience. Below are concrete examples and suggestions for improvement.

1. **Abstract (lines 1‑12 of `main.tex`)** – Phrases such as “hierarchical memory framework”, “personalized presentation agents”, and “scoped slide‑local revision” are introduced without any lay explanation. Consider re‑phrasing to something like: “We propose MemSlides, a system that stores long‑term user preferences separately from short‑term editing context, allowing the agent to make small, targeted changes to slides rather than rebuilding the whole deck each time.”

2. **Acronym Overuse** – The paper frequently uses abbreviations (LLM, API, RAG, etc.) without defining them at first appearance. For instance, “LLM‑as‑judge” appears in Section 5 (line 45) without prior definition of LLM. Define each acronym the first time it appears, e.g., “large language model (LLM)”.

3. **Introduction (lines 30‑55)** – Sentences are overly long and packed with jargon:  
   - “Recent agentic systems further advance this task by producing complete decks through multi‑modal or tool‑based workflows” (line 34).  
   - “An effective personalized slide generation framework should build and maintain user profiles that capture users’ long‑term preferences … rather than requiring users to repeatedly specify their preferences in every interaction” (lines 38‑41).  
   Break these into two or three shorter sentences and replace “agentic” and “multi‑modal” with plain descriptors like “systems that use multiple tools”.

4. **Figures and Captions** – Captions such as “Overview of \methodname. The framework comprises long‑term memory …” (Figure 1 caption, line 70) repeat the same jargon used in the text. Simplify to: “Diagram of MemSlides showing how long‑term user preferences and short‑term editing context are stored separately.”

5. **Methodology (Section 3, lines 120‑170)** – Terms like “execution contract”, “Plan–Act–Guard pipeline”, and “snapshot rebinding hints” are introduced without intuitive explanation. Replace with a brief description of what the system actually does, e.g., “The system first decides which slide(s) need to be changed (Plan), then applies the change (Act), and finally checks that the change was applied correctly (Guard).”

6. **Memory Terminology** – The paper distinguishes “user profile memory”, “tool memory”, and “working memory” repeatedly (Section 3.2, lines 180‑210). While the distinction is important, the repeated use of the word “memory” can be confusing. Consider using alternative labels such as “user preferences”, “tool experience”, and “session state”.

7. **Evaluation Section (Section 5, lines 250‑300)** – The description of “persona‑alignment judgments” and “diagnostic matched‑pair modify evaluation” relies heavily on domain‑specific metrics (e.g., “Closed‑Loop Completion”, “Strict Verify”). Provide a short, non‑technical summary of what each metric measures, perhaps in a table footnote.

8. **Conclusion and Limitations** – The conclusion restates the same jargon-heavy phrasing used throughout. Re‑write to emphasize the practical benefit: “MemSlides lets users keep their style preferences across multiple slide‑creation sessions and makes small edits faster and more reliable.”

Overall, the paper would benefit from a systematic reduction of jargon, clearer definitions of all acronyms, and shorter, more accessible sentences. These changes will make the contribution understandable to readers outside the immediate sub‑field of agentic memory systems while preserving the technical depth for specialists.
