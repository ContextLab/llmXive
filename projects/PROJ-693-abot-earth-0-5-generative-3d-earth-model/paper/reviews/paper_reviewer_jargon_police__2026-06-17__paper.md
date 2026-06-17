---
action_items:
- id: 4cf13298ac1b
  severity: writing
  text: "Replace or explain the term \u201Cnative 3DGS generative framework\u201D\
    \ (Section\u202F3.1) \u2013 most readers will not know what \u201C3DGS\u201D means\
    \ without a plain\u2011language description."
- id: 1239f7368626
  severity: writing
  text: "Define or simplify \u201CGaussian primitives\u201D (Section\u202F3.1, Fig.\u202F\
    1) \u2013 the phrase is jargon\u2011heavy and could be replaced with \u201Cbasic\
    \ 3D building blocks\u201D."
- id: f6df5f34ca9c
  severity: writing
  text: "Avoid the buzzword \u201Clatent space\u201D (Section\u202F3.1) or provide\
    \ a brief lay explanation, e.g., \u201Ca compact representation of the scene\u201D\
    ."
- id: 7b7fb9f87c7a
  severity: writing
  text: "Explain acronyms such as \u201CVRAM\u201D, \u201CGSD\u201D, \u201CEPSG:3857\u201D\
    , and \u201CENU\u201D on first use (Section\u202F4.2) or replace with clearer\
    \ terms like \u201CGPU memory\u201D, \u201Cground sampling distance\u201D, \u201C\
    map projection\u201D, and \u201Clocal coordinate system\u201D."
- id: b4e1697811ab
  severity: writing
  text: "Replace the phrase \u201Chierarchical block\u2011based architecture\u201D\
    \ (Section\u202F3.2) with a simpler description such as \u201Ca system that splits\
    \ a city into manageable pieces\u201D."
- id: 87b7f4a1a0a9
  severity: writing
  text: "Clarify \u201Ccontinuous level\u2011of\u2011detail (LOD) hierarchy\u201D\
    \ (Section\u202F3.2) \u2013 consider rephrasing to \u201Ca system that automatically\
    \ shows more detail when you zoom in\u201D."
- id: 18d1aead673d
  severity: writing
  text: "The term \u201Cmulti\u2011strategy point cloud simplification\u201D (Section\u202F\
    3.2) is overly technical; substitute with \u201Cdifferent ways to reduce the number\
    \ of points while keeping shape\u201D."
- id: 6ad578b04591
  severity: writing
  text: "In Section\u202F3.3, replace \u201Csliding\u2011window inference\u201D with\
    \ \u201Coverlapping tile generation\u201D to make the process more intuitive."
- id: 1974c49dc287
  severity: writing
  text: "The phrase \u201Ccross\u2011view quality enhancement\u201D (Section\u202F\
    3.2) could be rewritten as \u201Cimproving quality when combining images taken\
    \ from different angles\u201D."
- id: d38207f8e6c8
  severity: writing
  text: "Avoid the dense technical term \u201CBhattacharyya distance\u201D (Section\u202F\
    4.2) or provide a short plain\u2011English explanation, e.g., \u201Ca statistical\
    \ measure used to merge data efficiently\u201D."
- id: 7c08f731a6e0
  severity: writing
  text: "The expression \u201Ctrillion\u2011scale Gaussian primitives\u201D (Section\u202F\
    4.1) is jargon; consider saying \u201Cbillions of small 3D elements\u201D."
- id: 0c19c2dfa40b
  severity: writing
  text: "Replace \u201Ctile\u2011based concurrent production pipeline\u201D (Section\u202F\
    4.1) with a simpler phrase like \u201Cparallel processing of map tiles\u201D."
- id: a738bb67a577
  severity: writing
  text: "The word \u201Cpragmatic\u201D (Section\u202F4.1) is vague; specify the concrete\
    \ design choice instead."
- id: 33110c9446bd
  severity: writing
  text: "The term \u201Cmodular, block\u2011based approach\u201D (Section\u202F4.1)\
    \ can be simplified to \u201Csplitting the work into independent blocks\u201D."
- id: 196d0fb25295
  severity: writing
  text: "In the abstract, replace \u201Cultra\u2011low\u2011cost\u201D and \u201C\
    high\u2011efficiency\u201D with more concrete descriptors such as \u201Clow\u2011\
    cost\u201D and \u201Cfast\u201D."
- id: baffb9903aaf
  severity: writing
  text: "Define or replace \u201Csimulation\u2011ready\u201D (Section\u202F1) with\
    \ a clearer phrase like \u201Cready to be used in virtual simulations\u201D."
- id: 6589cf72753b
  severity: writing
  text: "The phrase \u201Cdigital earth visualization\u201D (multiple sections) could\
    \ be clarified as \u201Cinteractive 3D maps of the planet\u201D."
- id: a4f0cbdc103e
  severity: writing
  text: "Avoid the idiom \u201Cbreak down technological and financial barriers\u201D\
    \ (Conclusion) \u2013 replace with \u201Creduce technical and cost obstacles\u201D\
    ."
- id: e2ae8e2abd11
  severity: writing
  text: "The term \u201Cplanetary\u2011scale\u201D appears repeatedly; consider using\
    \ \u201Cworld\u2011wide\u201D or \u201Cglobal\u201D for readability."
artifact_hash: 889d5a8e39acbdaa7baa4d1b8f93a551383f0dbc1ede3c36f50fc7a5e7bb8167
artifact_path: projects/PROJ-693-abot-earth-0-5-generative-3d-earth-model/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T06:19:26.541627Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is rich in specialized terminology that significantly hampers readability for a broad scientific audience. Below are the most prominent instances where jargon could be replaced with clearer language or where acronyms are introduced without sufficient definition.

**Abstract & Introduction**  
- “native 3DGS generative framework” (Sec 3.1) – the abbreviation *3DGS* (3D Gaussian Splatting) is only defined later; readers would benefit from an immediate plain‑English description.  
- “Gaussian primitives” and “latent space” are introduced without lay explanations; they could be described as “basic 3D building blocks” and “compact scene representation”, respectively.  
- Phrases such as “ultra‑low‑cost”, “high‑efficiency”, and “digital earth visualization” are buzzwords that add little concrete meaning. Simpler alternatives (“low‑cost”, “fast”, “interactive 3D maps”) improve clarity.

**Method (Sec 3)**  
- “hierarchical block‑based architecture”, “continuous level‑of‑detail (LOD) hierarchy”, and “multi‑strategy point cloud simplification” are dense technical terms. Recasting them as “splitting a city into manageable pieces”, “automatically showing more detail when zooming in”, and “different ways to reduce point numbers while preserving shape” makes the concepts accessible.  
- “cross‑view quality enhancement” could be clarified to “improving quality when combining images taken from different angles”.  
- “sliding‑window inference” (Sec 3.3) is a specialized term; “overlapping tile generation” is more intuitive.

**Deployment (Sec 4)**  
- Acronyms *VRAM*, *GSD*, *EPSG:3857*, and *ENU* appear without first‑use definitions. Even though *GSD* is defined later, its first occurrence should include the full form (“ground sampling distance”).  
- “Bhattacharyya distance” (Sec 4.2) is a statistical term unfamiliar to most readers; a brief parenthetical explanation or a simpler phrase (“statistical measure for merging data”) would help.  
- “trillion‑scale Gaussian primitives” is hyperbolic jargon; stating the actual order of magnitude (“billions of small 3D elements”) conveys the scale more transparently.  
- The “tile‑based concurrent production pipeline” and “modular, block‑based approach” can be rewritten as “parallel processing of map tiles” and “splitting the work into independent blocks”, respectively.

**Evaluation (Sec 5)**  
- The term “simulation‑ready” should be clarified as “ready to be used in virtual simulations”.  
- Repeated use of “planetary‑scale” could be varied with “global” or “world‑wide” for smoother prose.

**General Writing**  
- Several idiomatic expressions (“break down technological and financial barriers”, “ultra‑low‑cost”, “high‑efficiency”) are vague. Replacing them with precise descriptors improves scientific tone.  
- The manuscript frequently uses long compound nouns (e.g., “hierarchical level‑of‑detail (LOD) structures”) that could be broken into simpler sentences.

By systematically reducing jargon, defining all acronyms at first mention, and opting for plain language alternatives, the paper will become far more approachable to readers outside the immediate sub‑field while preserving technical accuracy.
