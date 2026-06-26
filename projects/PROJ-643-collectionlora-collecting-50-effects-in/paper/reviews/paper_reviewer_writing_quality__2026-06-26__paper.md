---
action_items:
- id: 3097de11847c
  severity: writing
  text: "Correct numerous grammatical errors and improve sentence flow in the abstract\
    \ (lines\u202F9\u201115)."
- id: 90542f204e1d
  severity: writing
  text: "Standardize terminology and abbreviations (e.g., \u201CLoRA\u201D, \u201C\
    effect LoRA\u201D, \u201CAcceleration LoRA\u201D) for consistency throughout the\
    \ manuscript (see sections\u202F1,\u202F3,\u202F4)."
- id: ac6b3f29fab1
  severity: writing
  text: "Rewrite overly long and convoluted sentences, especially in the Introduction\
    \ (lines\u202F31\u201145) and Method (lines\u202F120\u2011150), to enhance readability."
- id: ae52b136cd8b
  severity: writing
  text: "Fix punctuation and spacing issues (missing spaces after commas, inconsistent\
    \ use of hyphens) that appear in multiple tables and figure captions (e.g., Table\u202F\
    1, Figure\u202F2)."
- id: 2b2417880753
  severity: writing
  text: "Ensure uniform formatting of mathematical expressions and symbols (e.g.,\
    \ proper spacing around \u2018=\u2019, consistent use of \\(\theta\\) vs. theta)\
    \ across equations in Sections\u202F3 and\u202F4."
- id: b981cc83ec2f
  severity: writing
  text: Remove duplicated package imports (axessibility appears twice) and redundant
    comments in the preamble to keep the LaTeX source clean.
- id: 2abbe59cc039
  severity: writing
  text: Edit figure and table captions for conciseness and grammatical correctness;
    many captions contain fragment sentences or inconsistent capitalization.
- id: cd1e789dce67
  severity: writing
  text: "Proofread the Conclusion (lines\u202F200\u2011210) to eliminate repetitive\
    \ phrasing and improve logical flow."
artifact_hash: 2a1b4c65ebf4844ee4cfea5a1931c70997d4322d1755391c095bba4101b76763
artifact_path: projects/PROJ-643-collectionlora-collecting-50-effects-in/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T10:34:24.368721Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript is generally well‑structured, but the writing quality hampers clarity and readability. Below are the most salient issues, illustrated with concrete locations in the source.

**Abstract (lines 9‑15).** The opening paragraph mixes several ideas in a single run‑on sentence: “Customized image editing aims to equip … using limited paired data, typically via Low‑Rank Adaptation (LoRA). As the number of desired effects grows, storing and dynamically loading numerous these effect LoRAs significantly increases deployment overhead.” The phrase “numerous these effect LoRAs” is ungrammatical, and the sentence would benefit from being split into two shorter statements. Moreover, the bolded claim “We propose CollectionLoRA …” is embedded in the middle of a long paragraph, breaking the logical flow. Re‑ordering the sentences to first state the problem, then the contribution, and finally the results would improve comprehension.

**Introduction (lines 31‑45).** Several sentences are excessively long and contain nested commas, making them hard to parse. For example: “However, scaling this paradigm in practice exposes three bottlenecks as illustrated in Fig. 1(a): (i) Storage costs. Deploying all effect LoRAs imposes substantial storage overhead on individual devices.” The colon after “bottlenecks” should be followed by a list, but the current formatting interleaves periods and commas, confusing the reader. Breaking the list into bullet points (as is already done) and removing the introductory clause would be clearer.

**Method (lines 120‑150).** The description of Probabilistic Dual‑Stream Routing contains redundant phrasing: “Specifically, the framework samples a random probability p ∼ U(0,1) at each training step and dynamically executes the following routing logic based on a preset switching rate p_switch.” The word “specifically” is unnecessary, and the sentence could be shortened to “At each step we sample p ∼ U(0,1) and route to the effect or general stream according to p_switch.” Similar redundancy appears in the description of Asymmetric Orthogonal Prompting (“This automated process removes the need for manual prompt engineering.”) – the phrase “automated process” already implies that manual engineering is unnecessary.

**Equations and notation.** Throughout Sections 3 and 4 the notation is inconsistent. Equation (1) uses \(\Delta\theta_{effect}^{i}\) while later the text refers to “effect LoRA” without the delta symbol. In Equation (4) the term “\(\mathcal{L}_{\text{TA-FM}}\)” is introduced without a preceding article (“the”). Consistent spacing around operators (e.g., “=”, “+”) and uniform use of math mode for symbols would improve typographic quality.

**Redundant package imports.** The preamble loads the `axessibility` package twice (lines 22 and 30). This duplication is unnecessary and may cause warnings during compilation. Removing the second instance cleans the source.

**Figure and table captions.** Many captions are phrased as fragments rather than complete sentences, and some contain inconsistent capitalization (“Evaluation of subject consistency metrics.” vs. “Qualitative comparison of CollectionLoRA against baseline methods.”). Captions should start with a capital letter and end with a period, and they should be concise yet self‑contained. For instance, Figure 5’s caption could be revised to: “Comparison of subject‑consistency metrics: DINO often assigns high scores to failed generations, whereas VSA penalizes semantic failures with a zero score.”

**Conclusion (lines 200‑210).** The conclusion repeats the three component names verbatim from earlier sections, leading to redundancy. A more effective conclusion would summarise the empirical impact (“Our experiments show a 30 % reduction in Bad Case Rate while preserving few‑step generation”) and then briefly restate the broader significance.

**General style.** The manuscript alternates between British‑style spelling (“optimisation”) and American spelling (“optimization”). Choose one style and apply it consistently. Additionally, there are occasional missing spaces after commas (e.g., “CLIP:0.727, DreamSim:0.425”) and inconsistent use of hyphens in compound adjectives (“few‑step” vs. “few step”).

**Overall recommendation.** The paper’s scientific contributions are promising, but the current writing hampers the reader’s ability to follow the narrative. Addressing the grammatical errors, simplifying long sentences, standardising terminology, and polishing captions will substantially improve readability and professionalism. Once these revisions are made, the manuscript will be much clearer and more suitable for publication.
