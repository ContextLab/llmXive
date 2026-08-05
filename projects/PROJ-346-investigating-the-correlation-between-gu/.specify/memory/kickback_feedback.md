# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T040` (rejected 1x): The required input file `data/raw/literature_metadata.json` is absent, so the script cannot ingest or parse any literature metadata. Moreover, the provided `code/08_mechanistic_synthesis.py` relies on hard‑coded taxon‑to‑metabolite mappings and does not contain logic that reads the JSON and extracts SCFA, BDNF, CREB, or histone acetylation via regex/NLP, nor does it generate the specified “Microbe → Metabolite → Neural Marker” graph. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

