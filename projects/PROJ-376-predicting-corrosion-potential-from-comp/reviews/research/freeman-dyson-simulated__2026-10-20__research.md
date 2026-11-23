---
action_items: []
artifact_hash: c97359131de712f03467e05a7878cb3a002eba37b8f812f429d2505fca185649
artifact_path: projects/PROJ-376-predicting-corrosion-potential-from-comp/specs/001-predicting-corrosion-potential-from-comp/spec.md
backend: dartmouth
feedback: "The spec's engineering hygiene is real \u2014 the leakage controls (FR-004,\
  \ SC-004), the refusal to impute missing pH, and the explicit ban on synthetic-data\
  \ fallback are all commendable, more disciplined than most proposals of this shape.\
  \ But the whole edifice rests on a data source I cannot verify exists in the form\
  \ assumed. NIST-IR-8200 is cited here as if it were a queryable corrosion database\
  \ with a REST API, complete with 429-handling requirements \u2014 yet the artifact\
  \ never establishes that such "
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-20T20:07:38.728583Z'
reviewer_kind: llm
reviewer_name: freeman-dyson-simulated
score: 0.0
verdict: minor_revision
---

The spec's engineering hygiene is real — the leakage controls (FR-004, SC-004), the refusal to impute missing pH, and the explicit ban on synthetic-data fallback are all commendable, more disciplined than most proposals of this shape. But the whole edifice rests on a data source I cannot verify exists in the form assumed. NIST-IR-8200 is cited here as if it were a queryable corrosion database with a REST API, complete with 429-handling requirements — yet the artifact never establishes that such an API exists, what its schema is, or whether it contains the joint distribution of composition + environment + corrosion potential. The spec is careful to halt if the data is insufficient, which is honest, but it treats the existence of the data as an assumption rather than a checkable fact, and the entire P1 story is downstream of that assumption. Three further problems. First, FR-019's Materials Project merge is incoherent with FR-002: Materials Project is a DFT thermodynamics repository with no notion of corrosion-potential measurements or NIST record IDs, so 'link them by record ID, ensuring no fuzzy matching' between these two sources is not a design choice but an impossibility — the two databases share no keys. Second, FR-021 makes R² > 0.6 a system MUST. That is mandating a research outcome; a spec can require that the pipeline *measure* and *report* R², but requiring a particular score guarantees either failure-by-design or quiet pressure toward leakage. Third, the Leave-One-Specific-Alloy-Out split (US-1, scenario 3) puts exactly one alloy grade in the test set; an R² computed on a single held-out group is dominated by that group's internal variance and is nearly meaningless as a generalization estimate — with ≥10 designations available, leave-one-*group*-out CV or repeated group splits would be the defensible choice, and the spec's own minimum of 10 designations makes the single-holdout design look arbitrary. Minor: the pH edge case defines the 'standard aqueous range' as 'the full spectrum of the pH scale,' which is circular and also wrong in practice — concentrated acids and bases routinely yield pH < 0 or > 14, so FR-016 will flag physically legitimate extreme-environment records into a diagnostic bin rather than the regression.

---

> *Note: this contribution was authored by **Freeman Dyson (simulated)** — a simulated AI persona shaped from the public-record writings of Freeman Dyson, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Freeman Dyson.*
