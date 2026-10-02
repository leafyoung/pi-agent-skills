---
name: teach-course
description: >-
  Set up and maintain the teaching-workspace itself: the directory structure,
  state documents (MISSION/RESOURCES/NOTES/glossary/learning-records), lesson
  authoring into the course book, resource acquisition, marimo companion
  notebooks, verification bars and commit gates. Use when scaffolding a
  teaching workspace, creating or updating workspace state documents, building
  or verifying the course book, writing lessons into it, downloading and
  snapshotting resources, creating or verifying marimo notebooks, or wrapping
  a lesson/unit/episode for commit. This is the workspace layer under the
  teach skill (which owns the pedagogy) and beside the mdbook-authoring skill
  (which owns book mechanics); it is consumed directly by tutoring workspaces
  and by the video-teach and slides-teach source pipelines. Not for the
  teaching itself (teach), source transcription/extraction
  (video-teach/slides-teach), or raw book-building how-tos (mdbook-authoring).
---

# The teaching-workspace backend

Every way course material is produced here ends in the same kind of workspace,
and this skill owns that workspace: its layout, its state documents, how lessons
land in the book, how resources are acquired, how notebooks are verified, and
the gates a unit passes before it is committed. The layers around it:

- **teach** owns the pedagogy (teaching principles, mission interview, ZPD,
  exercise design) and is the front door for tutoring. When a tutoring session
  grows a workspace, it hands the scaffolding and verification to this skill.
- **video-teach** and **slides-teach** own the source pipelines (how raw
  material becomes a trustworthy transcript/page index). They hand lesson
  authoring, resources, notebooks and wrap-up to this skill.
- **mdbook-authoring** owns the book mechanics (toolchain, Route A/B, style
  table). Build every book with it; this skill only says when and what.

Call order in a session follows that stack: front door, then this skill when a
workspace or course artifact is touched, then mdbook-authoring when the book is
built.

## Course parameters (fix once per workspace, record in NOTES)

This skill serves two flavors. Fix the parameters at workspace creation:

| Parameter | video course | slides/documents course | tutoring workspace |
|---|---|---|---|
| Unit folder | `epN_<slug>/` | `unitN_<slug>/` | none (flat) |
| Join key | `MmSSs` timestamps | source page `pNNN` | - |
| Authoring inputs | `slides/README.md` + corrected transcript | `pages/README.md` + text layer + `notes.md` | research |
| Source gate | video-teach Phase A | slides-teach index review | - |
| Extras | `MEDIA.md` + gitignored media cache; deck PDF pulled forward | `source/` committed; `notes.md` speaker notes | - |

Everything below is written in terms of a **unit** - an episode, a unit, or a
lesson batch in a tutoring workspace.

## Output formats

A workspace authors its lessons in **one format - mdbook by default**. Ask the
user only to confirm when starting a new workspace - unless they already named a
format or explicitly want print-first lessons, do not push quarto. If they defer
("whatever", "you choose"), fall back to mdbook. Record the choice in `NOTES`;
in an existing workspace, read it from `NOTES` or infer it from disk (`mdbook/`
or `lessons_md*/` -> mdbook; `lessons/*.qmd` with no book dir -> quarto) and
don't re-ask.

- **mdbook (default)** - the whole course as a navigable, searchable web book
  (`book.toml` + `src/` + built `book/`). Best in practice: it is the format
  every active curriculum here converged on, the user browses it continuously,
  and a translated course is simply two mirror books under one convention.
- **quarto** - per-lesson `./lessons/*.qmd` rendered to PDF via Typst. Reserve
  for genuinely print-first deliverables.

**Never maintain the same lessons in two formats.** Dual sources drift:
retiring one curriculum's qmd lesson tree required a full normalized-diff audit
of all twenty lesson pairs to prove nothing was lost (2026-09-26). If a
workspace has both, convert (mdbook-authoring Route B), prove sync, retire the
qmd lessons, and record the retirement in `NOTES`.

**State-doc flavor - decide once, never straddle.** Canonical in an mdBook
workspace: MISSION/NOTES/RESOURCES/GLOSSARY/learning-records live **inside the
book** as `src/*.md` (canonical layout: [MDBOOK.md](./MDBOOK.md)). Two
sanctioned exceptions: the **linkage route** (artifacts link into rendered root
documents, so state docs stay root Quarto docs rendered from a root
`_quarto.yml` that no longer lists lessons) and the **ledger flavor** used by
video courses and slides courses (root `.qmd` state docs kept as
editor-readable ledgers - deliberately never rendered, no root `_quarto.yml` -
because the book's `about.md` carries the in-book summary). Two living copies
of a state document is how mirror drift happens.

## Workspace layout

**Tutoring workspace** (flat, created by teach):

- `MISSION.qmd` - the reason the user is learning this
  (format: [MISSION-FORMAT.md](./MISSION-FORMAT.md)); mdBook flavor:
  `<book-dir>/src/mission.md`.
- `RESOURCES.qmd` - the acquisition ledger
  ([RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md)); mdBook: `src/resources.md`.
- `GLOSSARY.qmd` - canonical terminology
  ([GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md)); mdBook: `src/glossary.md`.
- `./learning-records/*.md` - what the user has learned, `0001-<name>.md`,
  incrementing ([LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md));
  mdBook: `<book-dir>/src/learning-records/`.
- `./lessons/` - the lessons; `./assets/` - reusable components;
  `NOTES.qmd` - preferences and working notes (mdBook: `src/NOTES.md`).

**Course workspace** (one git repo, one `uv` project, one folder per unit):

```
<course>/
├── AGENTS.md              # how to work here: layout + conventions (adapt on init)
├── MISSION.qmd            # root, canonical (ledger flavor - never rendered)
├── RESOURCES.qmd          # acquisition ledger (root; snapshots live per-unit)
├── NOTES.qmd              # scratchpad (root, canonical)
├── pyproject.toml         # ONE uv project for the whole course
├── .python-version        # 3.12 unless the course needs otherwise
├── .gitignore             # mdbook/book/, output/, __pycache__, caches (+ video: media, transcript intermediates)
├── mdbook/                # the course book (mdbook-authoring Route A scaffold)
│   ├── src/SUMMARY.md     #   one Part per unit; every file listed or it won't render
│   ├── src/about.md       #   course overview + progress table (the resume anchor;
│   │                      #   NOT mission.md - root MISSION.qmd is canonical)
│   ├── src/unitN-<slug>/  #   unit overview chapter + lessons/*.md
│   ├── src/reference/     #   cross-unit cheat sheets (glossary.md first)
│   └── src/assets/unitN/  #   copies of figures embedded in lessons (source in unitN/assets/)
└── <unit>N_<slug>/        # one folder per unit - everything else is per-unit
    ├── README.md          # provenance, index summary, what's built, open gaps
    ├── notebooks/<slug>.py    # marimo companion notebook(s)
    ├── resources/         # downloaded PDFs; web snapshots as resources/web/*.qmd
    ├── assets/            # lesson figure generation scripts + rendered images
    ├── output/            # marimo export artifacts (gitignored)
    └── learning-records/  # per-unit ZPD findings, per teach skill
```

plus the flavor's source artifacts (video: `transcript/`, `slides/`, `MEDIA.md`
- see video-teach; slides: `source/`, `pages/`, `notes.md` - see slides-teach).

**Placement is not negotiable**: only `AGENTS.md`, the root state docs,
`pyproject.toml`, `.python-version`, `.gitignore` (and the flavor's root extras:
`MEDIA.md` for video) are root-level; everything else lives in the unit folder.

**Python code.** One root `pyproject.toml`, no per-unit files; add a dependency
once at the root when any unit needs it (marimo - pin the version - pillow,
pytest, ruff, plus format-specific extras). Notebooks are **marimo, never
Jupyter** (user preference). Add a root `.vscode/settings.json` so unit
notebooks open as marimo while `assets/*.py` figure scripts and any `src/`
package keep the default editor (ipynb-to-marimo skill's
`workbench.editorAssociations` pattern; add an explicit `"default"` override
for any non-notebook `.py` that would otherwise fall inside the notebook glob):

```json
{
  "workbench.editorAssociations": {
    "**/unit*_*/notebooks/*.py": "marimo-notebook"
  }
}
```

(video courses: glob `**/ep*_*/notebooks/*.py`.)

## Authoring lessons into the book

Author per the **teach** skill - its teaching rules (mission grounding,
Motivate/Establish/Connect/Check per node, unconditional truths first,
exercises with answer keys, citations, ZPD) all apply unchanged. This section
is only about where lessons land and what they must contain.

- Content comes from the unit's authoritative index and narration layer (see
  the course parameters). The source tells you *what to teach and in what
  order*; the teach rules tell you *how*.
- Lesson language: the course's language - the user's stated preference, else
  the source's. Teach's mirror books apply only when the user explicitly
  requests a translated course (see "Mirrors, sync, and verification").
- 2-4 lessons per lecture hour (video) or per 30-40 content pages (slides),
  each tightly-scoped, self-contained, with a single tangible win and its
  `## Exercises`/`## Answers` sections. A lesson with unanswered exercises must
  not ship.
- Retrofit (absorbing pre-existing lessons): normalize their exercise headings
  to the book's convention (`## Exercises` / `## Answers`) and bring each
  chapter to the same bar - a numerical, chapter-computable exercise where the
  existing mix is conceptual-only.
- Book structure: one Part per unit in `SUMMARY.md`; each Part opens with a
  unit overview chapter (what the source covers, link to the original, links
  to its notebook and resources) followed by the lessons. Add each chapter to
  `SUMMARY.md` in the same edit that creates it.
- Cite the source: video courses link the video with a timestamp
  (`https://youtu.be/<id>?t=<s>`) plus the local transcript section; slides
  courses cite the page ("source p.12") with a relative link to the kept page
  image in `mdbook/src/assets/unitN/` and the `pages/README.md` row.
- Figures are regenerable - generation script in `<unit>/assets/lessonNNNN-<topic>.py`,
  rendered image beside it, **copy** the image into `mdbook/src/assets/unitN/`
  for embedding (re-copy after regenerating).
- Source images may be embedded where the source IS the content (a key
  formula, a result table): copy into `mdbook/src/assets/unitN/` likewise, and
  keep a conservative copyright posture - brief excerpts for personal study
  are fine, wholesale re-publication is not. An asset copied into
  `mdbook/src/assets/` must be embedded by a lesson in the same session - an
  unreferenced copy is dead weight that reads as already-used, and no build
  warning will flag it.
- Build bar: `mdbook build` with zero warnings; math via KaTeX, callouts via
  admonish, per the mdbook-authoring skill's style table and gotchas (escape
  literal `$`, wire the text-fix preprocessor, no `README.md` in src/).

## Resources (download on the spot)

`RESOURCES.qmd` at the root is the ledger; per the teach skill, **every entry
is acquired the moment it's added**. In a course workspace acquisition means:

- Papers / references / slides / cited works -> PDF verbatim into
  `<unit>/resources/`. **Verify every fetched PDF**: page count + text
  extraction (`pdfinfo`/`pdftotext`), and prefer the largest of N archive
  captures - a truncated download parses as a valid PDF header but is worse
  than no local copy (seen in practice: a Wayback capture complete only to
  ~half its size). A truncated PDF must not be kept.
- Web pages (course site, docs, project pages) -> snapshot to
  `<unit>/resources/web/<slug>.qmd`: YAML `title`, a provenance blockquote
  (source URL, fetch date, license note), then the content as markdown.
- The course's own source -> entry marked *in-repo* (slides) or *streaming* +
  media-cache path from `MEDIA.md` (video, never commit video).
- Find the official materials first (the course's or deck's own published
  materials beat any third-party summary); record and cite them from the
  unit's lessons.

Before finishing any session: every `RESOURCES.qmd` entry has a local path or
an explicit streaming-only/paywalled note.

Downloaded papers are copyrighted third-party material - **gitignore
`<unit>/resources/*.pdf`** so `resources/web/*.qmd` snapshots carry the record
while the binaries stay local.

## Marimo companion notebooks

Each unit gets `<unit>/notebooks/<slug>.py` - an interactive companion that
runs the source's central artifact: the algorithm it teaches, the worked
example, the visualization of the phenomenon, the spreadsheet model made live.

- marimo app with `app_title`, `hide_code` markdown cells explaining each
  section, LaTeX via `$...$`/`$$...$$` in `mo.md`, interactive controls
  (`mo.ui.slider`, `mo.ui.text`) wherever a parameter is pedagogically
  interesting.
- Self-contained: synthetic data or tiny bundled samples by default. If it
  needs a download, cache into `<unit>/data/` and degrade gracefully offline;
  for XLSX sources bundle the real sheet as a small CSV when it is small
  enough to commit, else generate a faithful synthetic stand-in and say so.
- **Verify by execution**:

  ```bash
  uv run python ~/.agents/skills/teach-course/scripts/run_marimo_notebook.py \
      <unit>/notebooks/<slug>.py
  ```

  It imports the module, runs every cell via `app.run(defs={"mo": marimo})`,
  and detects a raised cell by diffing the notebook's statically declared cell
  outputs against the definitions the run actually produced (headless marimo
  swallows plain cell exceptions - verified on 0.25.0). Any failure exits
  nonzero. Plain `marimo export html` is NOT a verifier: it exits 0 on broken
  cells AND wrongly exits 1 on correct mo-using notebooks. One known failure
  mode: the runner's `mo` injection makes marimo prune a cell that bundles
  `import marimo as mo` with the other imports (`IncompleteRefsError`, with
  later cells orphaned) - the fix is to put `import marimo as mo` alone in its
  own cell; the verifier prints this hint when it sees the error.
- Reference the notebook from the unit's overview chapter and the relevant
  lessons (repo-relative path in prose).

## Assets

Lessons are built from reusable **components**, stored in `<unit>/assets/`
(or `./assets/` in a tutoring workspace): Typst template partials, reusable
markdown includes, diagram helpers, code snippets - anything a second lesson
could reuse. Reuse is the default: before authoring, read `./assets/` and
build from what is there; when a lesson needs something new and reusable, write
it as a component and reference it - never inline content a future lesson would
duplicate.

**Every figure is regenerable, not just embeddable.** When a figure is
produced by code, save the generation script itself, named to match
(`lessonNNNN-topic.py` -> `lessonNNNN-topic.svg`/`.png`), runnable standalone
from the workspace root with a one-line invocation (document it in a module
docstring), regenerating the exact embedded figure. Edit the script and
re-run; never hand-patch the image.

Bootstrap shared helpers once per workspace rather than re-typing them: the
mdbook-authoring skill's bundled `assets/book.toml` (callouts, KaTeX, text-fix
preprocessor pre-wired), this skill's
[`assets/_quarto.yml`](./assets/_quarto.yml) for print-first Quarto
workspaces, and [`assets/scripts/svgutil.py`](./assets/scripts/svgutil.py) for
hand-built SVG figures (includes `FONT_EN`/`FONT_ZH` and `lang_from_argv()`
for dual-language variants; re-verify CJK font availability per workstation).

Diagrams: use the `mermaid-maker` subagent for relational diagrams and
`svg-maker` for spatial/geometric figures; embed the result (```` ```mermaid ````
block under mdBook, ```` ```{mermaid} ```` chunk in Quarto). If neither
subagent is available, hand-build per the figure-script rule above.

## Mirrors, sync, and verification

A translated course is full mirror books (`lessons_md/` + `lessons_md_zh/`):
every lesson change lands in all languages *and* the companion notebooks in the
same session - never "I'll translate it later". Shared state (mission, NOTES,
RESOURCES, learning-records) is maintained **once**, in the primary-language
book; the mirror carries only translated teaching content. Sync is proven, not
assumed: normalized-diff the language pairs after stripping the known
per-format differences - use
[`assets/scripts/normalized_diff.py`](./assets/scripts/normalized_diff.py),
don't hand-roll the stripping: `--digest` proves the structural lockstep (the
proof for language mirrors, since every word legitimately differs), the default
full-text diff is for same-language conversions (qmd -> mdBook). Figure
convention: the Chinese variant of a figure is `name-zh.svg` beside the English
original; errata caveat wording follows the book's language.

**Errata discipline.** A defect found in a source is folded into the lesson at
the exact point the wrong figure appears - a red **ERRATA** (English book) /
**修正** (Chinese book) tag, then the note, always preserving the caveat
"flagged, not yet confirmed with the source's owner". No standalone
root-level errata source (tried and deleted 2026-09-26); a per-book
`errata.md` ledger page inside `src/` is fine, maintained directly in the
book.

**The verification bar for any session that touched lessons or notebooks**:
`ruff` + `marimo check` on each touched notebook, then the execution bar -
`marimo export html` in ordinary (non-video) workspaces, or the
`run_marimo_notebook.py` runner above in video-course workspaces (it injects
`mo` explicitly; headless export can silently skip that injection); `mdbook
build` per book with zero warnings; `quarto render` only for root reference
docs. If other artifacts link into the built `book/` (reference-doc PDFs,
notebook headers), commit the rebuilt output as part of the change - where the
book output is tracked, linkage commits its `book/`; gitignored books just
rebuild.

## Wrap and the exit gate

1. `<unit>/README.md`: source provenance (origin, date, version; video link +
   duration for episodes), the index summary, what was built (lessons,
   notebook, resources), open gaps.
2. Learning records when the session surfaced something non-obvious (a ZPD
   finding, a convention decision, a bug or erratum in the source material).
3. Update root `RESOURCES.qmd` / `NOTES.qmd`; bump the unit's row in the
   book's `about.md` progress table (keep this table - it is the resume
   anchor).
4. Commit at unit boundaries (`unit3: pages indexed, 2 lessons, notebook`);
   on a long unit, commit at pipeline-step boundaries too - never leave hours
   of transcript/extraction work uncommitted.

**Exit gate - all items before the unit commit:**

- [ ] book: new chapters in `SUMMARY.md` (added in the same edit that creates
      them); `mdbook build` zero warnings; exercises all answered
- [ ] lessons cite the source layers per the course's join key; every figure
      or source image copied into `mdbook/src/assets/` is embedded by a lesson
- [ ] notebook: `run_marimo_notebook.py` exits 0 - the execution bar; headless
      `marimo export html` is not a verifier; linked from the unit's book
      chapters
- [ ] resources: every RESOURCES.qmd entry added this session has a local path
      or a streaming-only note
- [ ] unit README current (including open gaps); commit(s) for the unit

Source pipelines add their own gates before this one (video-teach's Phase A
handover gate runs when the unit's data phase completes; the pipeline's own
checklist defines each upstream step's end state).

## Conventions

- **Honest gaps**: if a notebook can't reproduce a claimed number (library
  drift, missing data), say so in the unit README with what was checked -
  never tune until it matches.
- **New session in an existing course**: read `AGENTS.md` -> `NOTES.qmd` ->
  the book's `about.md` progress table -> `git log --oneline` + `git status`
  -> the current unit's `README.md`, then resume the pipeline at its first
  incomplete step (the source pipeline's gate defines the upstream steps' end
  states; the exit gate above defines the rest).
- **Running steps with subagents** (the judgment-heavy steps - correction
  passes, lesson authoring - parallelize well, with three rules learned the
  hard way): dispatch at most 2-3 concurrent workers (4-5 tripped a provider
  5-hour usage cap twice on one course; solo dispatches kept working); **audit
  `git status` and diffs before re-dispatching a "failed" worker** - workers
  that time out or die writing their final report often leave all their file
  edits already on disk; and give each worker the unit's own paths and IDs in
  the prompt, so it never has to trust summary-level context.
- Skill scripts and extractors are regenerable; never commit `.venv`, caches,
  build output, or media.
