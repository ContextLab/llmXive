# Live repair failure: source selection and incomplete context

Production run https://github.com/ContextLab/llmXive/actions/runs/37879037485 failed before baseline tests. Its retained artifacts show:

- Attempt 1 emitted malformed JSON and proposed rewriting an unselected file.
- Attempts 2 and 3 guessed `src/llmxive/project_initializer.py`, which does not exist.
- All three diagnoses treated regular files occupying directory paths as ordinary directory-exists errors. The current evidence omitted filesystem type/content.
- Source context was silently sliced at 40,000 characters while the model had to return complete replacement files. Large platform modules exceeded that boundary.

The repair runner now validates selections against the actual file inventory, includes read-only observations of error paths and their parents, supplies complete source files within an explicit 250 KB budget, and supports exact unique text edits. Existing files cannot be changed without first being read. One bounded JSON correction retains both raw responses and reports the actual responding model. Candidate test and independent-review gates remain mandatory.

Validation: 25 focused tests passed, including real before/after subprocess pytest checks, file-parent collisions, large-file tail preservation, rejected ambiguous edits, invented filenames, unread-file replacement, and bounded JSON correction. This is platform verification; another live autonomous run is still required to establish useful repair output.
