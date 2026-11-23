# Case-insensitive checkout collisions — 2026-10-09

An index-only inventory of main `c95996fa5e106216da756a75746eaab6e9a370e7` found **36 collision groups / 72 tracked files**, using Unicode NFD normalization plus case folding. **Every pair contains different Git blobs.** The full paths, modes, and blobs are preserved in `case-collisions.json`. Reading this evidence directly from the Git tree avoids losing either version through a case-insensitive checkout.

Most collisions are project documentation, but two pairs are scientific Python tests in PROJ-149. The audit does not choose a scientifically authoritative variant or mass-rename imports. **35 groups remain for project-specific reference/provenance review under recurring issue #1139.** The inventory is evidence, not a blanket permission for more collisions.

## Concrete, byte-preserving fix

PROJ-715's spec folder contained both `API_analysis.md` and `api_analysis.md`. The files have different function signatures. Preserve the former at `API_analysis.case-preserved.md` without changing its bytes; retain the latter unchanged. Review of exact filename references under that project found two references, both in the sibling README; both now point to the distinct name. The README explicitly records that filename disambiguation does not validate either API description against the code. The JSON receipt records the original/new path and unchanged blob. Both variants now coexist on the Mac filesystem.

Separately, PROJ-008's `.gitattributes` had an inline comment interpreted as invalid attributes. Move that comment onto its own line while keeping `*.csv binary`. `git check-attr --cached` confirms binary is set and text unset without the prior warning.

## Prevention and recovery

Before a model-generated artifact write, the implementer checks every existing path component for a case/Unicode-normalization alias. A new spelling that aliases an existing file or directory is refused on Linux as well as Mac; exact existing spellings remain editable. Refusals use the existing per-task diagnostic channel from #1528, leave source bytes intact, keep the task incomplete, skip execution of the refused proposal, and appear verbatim in the next repair prompt. Two conflicting artifacts in the same response are detected too.

This is a focused artifact-writer guard, not a claim that arbitrary subprocess filesystem writes are an operating-system sandbox. Historical collisions and scientific imports still need the recorded project-specific audit. No scientific canary directories or original dirty checkout were modified.

Hosted CI passed the filename guards, all repository audits, and Dartmouth runtime
checks after inheriting #1540. The external-reference job repeatedly failed only
because the unchanged known Zenodo DOI timed out at 30 seconds. Its fixed service
examples never consume the changed project documents. With CI-owner review,
classify project-local Markdown and project-root `.gitattributes` as independent
of registrar availability while retaining offline and Dartmouth coverage. The
known `repair.yml` orchestration workflow has the same classification; its #1537
change only adds a quoted project-selection argument. Unknown project code,
dependencies, schemas, fixtures, and workflows remain conservative. Selection and
collection regressions preserve these boundaries; no reference assertion changes.
