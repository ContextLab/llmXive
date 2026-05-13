# Contract: static-site UI fixes (wordmark, tab indicator, modals, "How to contribute", Markdown rendering)

**Files**: `web/index.html`, `web/css/*` (mainly `site.css`, `components.css`, `layout.css`), `web/js/app.js`, `web/js/data.js`, `web/js/vendor/markdown.min.js` (NEW), `web/js/vendor/README.md` (NEW). **Maps to**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-009, FR-009b, FR-017, FR-018, FR-019; data-model E1, E2, E3. **Verification**: per Constitution III's UI clause, these are *visually* verified — screenshots at desktop (~1280px) and mobile (~375px) widths + a click-through of every new/modified modal — recorded in the implementation diagnostic.

## FR-001 — Header wordmark is one word

The `.brand` element in the header currently renders the project name split (`[llm]` + `Xive`). Fix: the wordmark text MUST be a single inline token inside its box — `white-space: nowrap` on the wordmark span, and the box sized to fit it (no `flex`/`inline-block` boundary that lets it wrap). Verify at every width down to ~320px the wordmark is one unbroken token.

## FR-002 — Active-tab indicator (D1)

`web/js/app.js`: replace the `tab.offsetLeft`/`tab.offsetWidth`-based positioning with a function `positionUnderline()` that sets `underline.style.left` / `underline.style.width` from `activeTab.getBoundingClientRect()` minus the tab-row container's `getBoundingClientRect()` (so it's correct even when the row has scrolled horizontally). Call it: on tab click; on `window` `resize` (rAF-debounced); on `orientationchange`; and once `document.fonts.ready` resolves (web-font load shifts widths). `web/css/site.css`: `.tab-underline` keeps its transition; remove any hard-coded left/width. Verify on desktop (click each tab; resize the window — indicator re-aligns) and mobile (the indicator is visible and correctly under the active tab; rotating the device re-aligns it).

## FR-003 — Pipeline-diagram-step modal (D8)

`web/index.html`: each `.stage` circle in `.pipeline.two-lane` gets `data-step="<key>"` (the `pipeline_steps[].key` from `projects.json` — E2); the per-stage `<p>` blurbs currently inline in the HTML are removed (the text now comes from the data). `web/js/app.js`: a click handler on `.stage[data-step]` opens a modal rendering that step's `pipeline_steps` entry: `name` (heading); `description` (rendered via the vendored Markdown lib); `inputs` / `outputs` (labelled lists); `agents` (a list — each agent name links to the agent-registry modal / opens that agent's prompt); `example_artifacts` (links to recent artifacts, or "no examples yet" if empty). Modal is dismissible (backdrop click / Escape / close button) and usable at mobile widths.

## FR-004 — Agent-registry modal (D8)

`web/index.html`: an "Agent registry" entry point (e.g. the existing "Agent registry" footer button becomes a modal trigger, or a new button on the About page) — `data-open-modal="agents"` (or equivalent). `web/js/app.js`: opening it renders the `agents` block (E1) as a list of `name` + `purpose`, with a link to `agents/registry.yaml` on GitHub (`agents[].registry_github_url`); clicking an agent fetches `agents[].prompt_raw_url`, renders it with the vendored Markdown lib, shows `agents[].tools` (+ `default_backend`/`default_model`), and a "view prompt on GitHub" link (`agents[].prompt_github_url`). Dismissible; mobile-usable.

## FR-005 — "How to contribute" section

`web/index.html`: add a "How to contribute" section under `#about` listing the four modes — **add ideas** (→ the "submit idea" control), **help with development** (→ the GitHub repo / open issues), **provide feedback** (→ the "submit feedback" control on any artifact), **review existing content** (→ the review controls / the Reviews data). Each with a concrete pointer (a link or a "click here on the site" cue). Plain static markup.

## FR-009 / FR-009b — Project-modal artifact + Markdown rendering (D2, D9)

`web/js/vendor/markdown.min.js` (NEW): the vendored small Markdown→HTML lib (`snarkdown` ~1 KB MIT, or `marked`-min fallback); `web/js/vendor/README.md` records its name/version/license/source. A small wrapper (in `app.js` or a tiny `web/js/markdown.js`) that: fetches a `.md` from a `raw.githubusercontent.com` URL, runs it through the lib, **sanitizes** the output (strip `<script>`, `on*=` attributes, `javascript:` URLs) before returning HTML. `web/js/app.js`: the project-modal open path resolves `current_artifact` (E3) — published PDF → embed (only when it actually exists); `markdown` → fetch+render+inject; `latex`/`json`/`yaml` → fetch + show as `<pre>` formatted source with a "view on GitHub" link; `none` → a placeholder ("No artifact yet — this project is at stage X; the next artifact will appear here") + the project metadata + a "browse on GitHub" link. **Never** an `<embed>` pointing at a nonexistent PDF. Verify: open a project with a PDF (PDF shows), one at the brainstormed stage (idea Markdown renders), an in-progress research project (its current artifact renders), and (if any) one with `type == "none"` (placeholder, no broken embed).

## FR-017 — Mobile

Every modal touched or added here (pipeline-step, agent-registry, project-artifact, submit-feedback, submit-paper) MUST be usable at mobile widths: scrollable body, dismissible (backdrop/Escape/close), not clipped, controls reachable. Verify at ~375px.

## FR-018 — Deploy sync

After the `web/` changes are merged to `main`, the existing `Deploy Pages` workflow (`on: push: paths: ['web/**']`) re-syncs `web/` → `docs/` and commits `deploy: sync web/ -> docs/ for GitHub Pages [skip ci]`. No manual step; the implementation just verifies that workflow runs green after the merge.

## FR-019 — No regression on data regeneration

The static-markup / JS / CSS fixes (wordmark, tab indicator, modal *structure*) are independent of `web/data/projects.json`'s content, so a pipeline-cron regeneration can't reintroduce them. The data-driven parts (the modals' *content*, the Contributors list, `current_artifact`) come from `web_data.py`, which the cron runs — so the `web_data.py` changes (the new blocks, the contributor fix) MUST be the thing the cron emits (they will be, since `web_data.py` is the canonical builder). Verify by re-running `web_data.py` and checking the new blocks + the contributor fix are still present.

## Acceptance (visual-verification checklist)

- [ ] Wordmark is one unbroken token at desktop and at ~320–375px.
- [ ] Tab indicator: correctly under the active tab on desktop; re-aligns on resize; visible+correct on mobile; re-aligns on rotate.
- [ ] Every pipeline-diagram circle opens a modal with description (rendered Markdown), inputs, outputs, the agent list (each agent → its prompt), and example-artifact links (or "no examples yet").
- [ ] The agent-registry modal lists every agent (incl. `submission_intake`); clicking one shows its rendered prompt + tools + GitHub links.
- [ ] The About page has a "How to contribute" section with the four modes + working pointers.
- [ ] A project with a PDF shows the PDF; one without shows the rendered current-stage artifact (Markdown rendered, not raw); one with no artifact shows a placeholder — 0 broken/empty embeds.
- [ ] Every new/modified modal is usable at ~375px.
- [ ] After merge, `Deploy Pages` runs green and `docs/` matches `web/`.
- [ ] Re-running `web_data.py` keeps the new blocks + the contributor fix.
- [ ] Screenshots of the above (desktop + mobile) are attached to the implementation diagnostic.
