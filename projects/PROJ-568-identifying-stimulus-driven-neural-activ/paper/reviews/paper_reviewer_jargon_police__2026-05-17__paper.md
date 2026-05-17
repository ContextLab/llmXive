---
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T15:12:46.179305Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This manuscript is a comprehensive survey, yet it frequently employs specialized terminology and abbreviations that may exclude non-specialist readers. The primary concern lies in the density of acronyms, particularly within the Abstract. Terms such as GLMs, MVPA, RSA, ISC, and ISFC are listed without expansion (Abstract, lines 30-45). While these are standard in computational neuroscience, a book chapter intended for broader cognitive neuroscience audiences should define them upon first mention, even in the summary, to ensure immediate clarity.

Throughout the text, standard abbreviations for "Figure" and "Section" are used consistently (e.g., "Fig.~\ref{fig:spacetime}", "Section~\ref{sec:activity}"). While common in LaTeX documents, spelling out "Figure" and "Section" improves accessibility for readers less familiar with technical typesetting conventions. Additionally, Latin abbreviations appear frequently (e.g., "i.e.", "e.g.", "etc."). Replacing these with plain English equivalents ("that is", "for example", "and so on") would reduce cognitive load for non-native speakers and general readers, aligning with the goal of a broad educational resource.

Specific technical terms in figure captions require clarification. In the caption for Figure 5 (Building across-patient models using Gaussian process regression), the term "MNI152 space" is used without definition (lines ~1350). This refers to a standard coordinate space, but without explanation, it excludes readers unfamiliar with neuroimaging standards. Similarly, "k-means cluster" is mentioned without briefly contextualizing the algorithm.

Finally, some mathematical notation is introduced without sufficient verbal scaffolding. For instance, the GLM definition introduces $\mathbf{Y}$, $\mathbf{X}$, and $\beta$ formally (Section "Generalized linear models and multivariate pattern analysis"). While necessary for precision, a brief sentence explaining these variables in plain text before the equation would aid comprehension. Addressing these jargon and abbreviation issues will ensure the chapter remains accessible to the intended interdisciplinary audience without sacrificing technical accuracy.
