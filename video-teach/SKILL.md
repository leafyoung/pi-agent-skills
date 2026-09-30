---
name: video-teach
description: >-
  Build a full study course from a list of YouTube lecture videos, laid out as
  one workspace: one git repo, one `uv` project, one folder per
  episode (`epN_<slug>/`) holding the downloaded-and-cleaned transcript, extracted
  slide captures with an authoritative slides/README.md index, qmd resource
  snapshots, marimo notebooks, and teach-skill lessons authored into an mdBook at
  the repo root. Use when the user asks to "build a course from these videos",
  "turn these lectures into lessons/episodes", "set up a course workspace for a
  YouTube playlist", or otherwise wants the video→transcript→slides→lessons→
  notebooks pipeline over one or more lecture URLs. Pairs with the `teach` skill
  (teaching rules, mdBook format) and the `transcribe-video` skill (transcription).
---

# Build a video course workspace

**Definitive pipeline** (one episode; the steps below are the full contract):

1. **Step 1** — `transcribe-video` (URL or local media in) →
   `transcript/<slug>.raw.vtt` (timing kept) + canonical `<slug>.clean.md`
   (overrides: no `.clean.zh.md`, glossary handed over, intermediates kept).
2. **Step 2** — slide extraction + OCR → `slides/slideK_<slug>_<MmSSs>.png`,
   `slides/README.md`, `slides/slides_ocr.json`.
3. **Step 3** — transcript foundation → `<slug>.verbal.md`, term-corrected
   `.clean.md` (slide refs + index), tagged `.clean.srt`,
   `correction_brief.md`/`corrections.json`.
4. **Steps 4–7** — lessons (mdBook) → resources → marimo notebook → wrap.

Turn a list of YouTube lecture videos into a **teaching workspace**: one git repo
whose per-episode folders hold every primary source (transcript, slide captures,
resource snapshots, notebook, lessons), and one mdBook that teaches the course.
The pipeline per episode:

```
video/URL ──transcribe-video──► transcript/<slug>.raw.vtt + .clean.md   (Step 1;
  │                             intermediates kept: video/audio + .groq.* + .srt)
  └──ffmpeg frames──► slides/slideK_*.png + slides_ocr.json             (Step 2;
                                       │            timestamps join keys)
                     ┌─────────────────┴──────────────────┐
                     ▼                                    ▼
  transcript_layers: .verbal.md + slide-tagged .clean.srt + corrected .clean.md
                     (Step 3)
                                       │
                     ┌─────────────────┴──────────────────┐
                     ▼                                    ▼
        mdbook lessons (teach skill)            epN/notebooks/*.py (marimo)
        + epN/resources/*.qmd snapshots         + episode README + learning records
```

The video content itself is **ground truth**: never teach from parametric memory
when a transcript or slide says otherwise. Web-search only for things the video
implies but doesn't state (links, paper citations, published course materials).

**The transcript is a first-class input to everything downstream** — not a
byproduct of Step 2. Lessons take their structure, derivations, and emphasis
from the spoken narrative (the lecturer's ordering, motivation, and emphasis
are the course's pedagogy), joined to the slide record by timestamp; notebooks
implement what the transcript works through; the slides index captures what
each slide shows. Author from the transcript outward: read it end-to-end for
the argument's shape before writing anything, then reconcile against the slide
images where they disagree — the image outranks the spoken word on formulas
and numbers, the transcript outranks the slide on reasoning and motivation.

## Workspace layout (create once per course)

```
<course>/
├── AGENTS.md              # how to work here: layout + conventions (adapt on init)
├── MISSION.qmd            # teach-skill mission (root — video-course flavor, see below)
├── RESOURCES.qmd          # acquisition ledger (root, canonical; snapshots live per-episode)
├── NOTES.qmd              # scratchpad (root, canonical)
├── MEDIA.md               # pointer to the gitignored video cache (heavy-data policy)
├── pyproject.toml         # ONE uv project for the whole course (marimo — pin the
│                          #   version, pillow, pytest, ruff)
├── .python-version        # 3.12 unless the course needs otherwise
├── .gitignore             # mdbook/book/, output/, __pycache__, caches,
│                          #   transcript intermediates (.webm, .groq.*, raw .srt)
├── mdbook/                # the course book (teach-skill mdBook flavor)
│   ├── book.toml          #   scaffold per teach/MDBOOK.md Route A (admonish+katex+text-fix)
│   ├── src/SUMMARY.md     #   one Part per episode; every file listed or it won't render
│   ├── src/about.md       #   course overview (NOT mission.md — root MISSION.qmd is canonical)
│   ├── src/epN-<slug>/    #   episode overview chapter + lessons/*.md for that episode
│   ├── src/reference/     #   cross-episode cheat sheets (glossary.md first)
│   └── src/assets/epN/    #   copies of figures embedded in lessons (source in epN/assets/)
└── epN_<slug>/            # one folder per episode — everything else is per-episode
    ├── README.md          # video link, duration, slide count, topic map, what's built
    ├── transcript/<slug>.raw.vtt           # raw transcription (Step 1)
    ├── transcript/<slug>.clean.md          # canonical clean (Step 1); slide refs + index added (Step 3)
    ├── transcript/<slug>.verbal.md         # verbatim layer, never LLM-edited (Step 3)
    ├── transcript/{correction_brief.md,corrections.json}  # Step 3 provenance
    ├── slides/slideK_<slug>_<MmSSs>.png + README.md   # the authoritative slide index
    ├── notebooks/<slug>.py # marimo notebook(s)
    ├── resources/         # downloaded PDFs; web snapshots as resources/web/*.qmd
    ├── assets/            # lesson figure generation scripts + rendered images
    ├── output/            # marimo export artifacts (gitignored)
    └── learning-records/  # per-episode ZPD findings, per teach skill
```

**Canonical vs book.** MISSION/RESOURCES/NOTES stay `.qmd` at the root (the user
reads them in editors and quarto) — this is the teach skill's sanctioned
**video-course flavor** of the state-doc rule: root `.qmd` state docs kept as
editor-readable ledgers, deliberately never rendered (no root `_quarto.yml`); the
book's `about.md` is the in-book summary, not a duplicate. Reference docs live in
the book (it's the living format). Record the flavor choice in `NOTES`.
Every mdBook rule — toolchain pinning, plugin wiring, SUMMARY completeness,
zero-warning build bar, style table — is in the teach skill's `MDBOOK.md`; follow it,
starting from its `assets/book.toml`.

**Python code.** One root `pyproject.toml`, no per-episode files; add a dependency once
at the root when any episode needs it. If episodes grow importable `src/` packages,
use a hatchling multi-package pyproject. Notebooks are
**marimo, never Jupyter** (user preference; also a teach-skill rule). Add a root
`.vscode/settings.json` so every `epN_<slug>/notebooks/*.py` opens as a marimo
notebook while `assets/*.py` figure scripts and any `src/` package keep the
default Python editor (ipynb-to-marimo skill's `workbench.editorAssociations`
pattern — add an explicit `"default"` override for any non-notebook `.py` that
would otherwise fall inside the notebook glob):

```json
{
  "workbench.editorAssociations": {
    "**/ep*_*/notebooks/*.py": "marimo-notebook"
  }
}
```

## Episode pipeline

**Step 0 — teach first-session flow (new course only).** Run teach's mandatory
first-session steps before authoring: mission interview, format confirmation
(mdbook here), research + dependency-map plan, then stop and wait for the
user's go-ahead. Steps 1–3 below are mechanical (transcribe / slides + OCR / transcript layers)
and may run while that interview and planning happen; no lesson authoring
before the go-ahead.

Work episodes in watch order. Steps 1–3 are mechanical and can run while you author
an earlier episode's lessons; authoring (Steps 4–6) is where the care goes.

### Step 1 — Transcribe (via the `transcribe-video` skill)

One step covers download + transcription: invoke the transcribe-video skill and
follow it exactly, passing the **YouTube URL** (it downloads the video itself)
or a **local video/audio file**. Course-specific points:

- **The video intermediary is kept** (standing override: callers skip the
  skill's move-and-cleanup) — Step 2 needs the same video file for slide
  extraction, and a shared file guarantees slide timestamps align with
  transcript timestamps. Move it into the media cache (`$MEDIA_DIR`, recorded
  in `MEDIA.md`) if the skill left it elsewhere.
- Standing overrides: **no `.clean.zh.md`**; hand over any known proper-noun
  list (course-level terms from prior episodes). A raw `.vtt`/`.srt` from an
  earlier pass may be supplied instead (the skill's Step 1b mode, skipping
  Groq). The slide-OCR-grounded term pass runs in Step 3, after Step 2's OCR
  exists.
- **Leave the timing file as `transcript/<slug>.raw.vtt`**: copy (not move)
  the skill's `<name>.groq.transcript.srt` — or the caller-supplied
  `.vtt`/`.srt` — to that name. Step 3's commands read exactly this file.
- Pass `--language-code en` (or the actual language) and
  `--output-dir <episode>/transcript --output-name <slug>` so outputs land with
  the right names on the first pass. On `HTTP 403`/`HTTP 500` (SABR/client
  problem): retry with `--extractor-args "youtube:player_client=visionos"`.
- Fetch `%(title)s`/`%(channel)s`/`%(duration_string)s` first to pick the
  episode `<slug>` (lowercase, descriptive, one separator style per course).
- **Timestamps are the join key** for everything downstream — slide files, the
  slides index, and lesson citations all reference `MmSSs` positions on the raw
  video timeline. Everything stays aligned to it.

### Step 2 — Extract slides and OCR them

Run the skill's extractor on the video from Step 1, then review and index:

```bash
cd ep<N>_<slug> && python3 ~/.agents/skills/video-teach/scripts/extract_slides.py "$VIDEO" \
  [--scene-threshold 0.25] [--sample-interval 20]
```

It writes `slides_raw/chosen/sNN_<MmSSs>.png` (one full-res frame per distinct
slide window, captured late in the window), a
`slides_raw/contact_sheet.jpg` for fast review, and `slides_raw/candidates.tsv`. Then:

1. **Review every candidate** with the Read tool (contact sheet first, then
   full-res frames). Drop non-slides: webcam cutaways, terminal demos, transition
   blurs. Lower `--scene-threshold` and re-run if slide changes were missed;
   extract a missed frame manually with `ffmpeg -ss <t> -i video -frames:v 1`.
2. Move keepers to `ep<N>_<slug>/slides/`, renamed `slideK_<slug>_<MmSSs>.png`
   (K = 1..count in first-appearance order; `MmSSs` = the capture timestamp).
3. Write `slides/README.md` — the **authoritative index**: source video URL/title,
   slide count, then one table row per slide: file, on-screen title, transcript
   section (timestamp range), and a dense summary of every formula, claim, and
   number on the slide. Formulas as text (`M_t(n) = P_t − MA_t(n)`), verified
   against the image, not the transcript's spoken version. Note slide callbacks
   (presenter flips back to an earlier slide) in the header prose, not as new slides.
4. **OCR the kept slides** — `python3 ~/.agents/skills/video-teach/scripts/slide_ocr.py
   slides/ --duration <video-seconds>` writes `slides/slides_ocr.json` (+ `.md`
   index): per slide, its OCR text and on-screen time window. This is the ground
   truth consumed by Step 3's correction pass.
5. Delete `slides_raw/` once indexed.

Expect roughly one slide per 2–6 lecture minutes; wildly more candidates means the
threshold is too low or the lecture is whiteboard-style (then capture *boards*
state-by-state, same naming).

### Step 3 — Two-layer transcript with slide-assisted correction
With `slides/slides_ocr.json` from Step 2, run the transcript-foundation
pipeline (`scripts/transcript_layers.py`) against
`transcript/<slug>.raw.vtt`: derive the verbatim `<slug>.verbal.md`, correct
the canonical `.clean.md` against slide OCR via a correction brief →
`corrections.json` → `--fix-clean --assemble` (term fixes in place, slide
index appended), and tag the `.clean.srt` with `[Slide K]`. Because these
courses are technical, the slides' OCR is the ground truth for exactly the
words ASR garbles — named methods, library calls, linearized formulas,
numbers.

Full commands, artifact definitions, and the precedence rules:
`references/transcript-foundation.md`. Outputs the checklist expects:
`transcript/<slug>.verbal.md`, the corrected `transcript/<slug>.clean.md`
(slide index appended), the slide-tagged `transcript/<slug>.clean.srt`, and
`correction_brief.md`/`corrections.json` for provenance.

### Step 4 — Lessons (teach skill, mdBook flavor)

Author per the `teach` skill with output format **mdbook** — its teaching rules
(mission grounding, Motivate/Establish/Connect/Check per node, unconditional
truths first, exercises with answer keys, citations, ZPD) all apply unchanged.

- Course content comes from the episode's `slides/README.md` (densest source) and
  `transcript/*.clean.md` (narrated derivations, joined by timestamp). The lecture
  tells you *what to teach and in what order*; the teach rules tell you *how*.
- Lesson language: the course's language — the user's stated preference, else the
  transcript's language. Teach's per-language mirror books (`lessons_md/` +
  `lessons_md_zh/` lockstep) apply only when the user explicitly requests a
  translated course; otherwise author one book in the course language.
- 2–4 lessons per lecture hour, each one tightly-scoped, self-contained, with a
  single tangible win and its `## Exercises`/`## Answers` sections. A lesson with
  unanswered exercises must not ship.
- Book structure: one Part per episode in `SUMMARY.md`; each Part opens with an
  episode overview chapter (what the lecture covers, video link, links to its
  notebook and resources) followed by the lessons. Add each chapter to `SUMMARY.md`
  in the same edit that creates it.
- Cite the lecture: link the video with a timestamp (`https://youtu.be/<id>?t=<s>`)
  and the local transcript section. Figures are regenerable — generation script in
  `epN_<slug>/assets/lessonNNNN-<topic>.py`, rendered image beside it, **copy** the
  image into `mdbook/src/assets/epN/` for embedding (re-copy after regenerating).
- Slides screenshots may be embedded in lessons where the slide IS the content
  (a key formula, a result table): copy into `mdbook/src/assets/epN/` likewise, and
  keep a conservative copyright posture — brief excerpts for personal study are
  fine, wholesale re-publication is not.
- Build bar: `mdbook build` with zero warnings; math via KaTeX, callouts via
  admonish, per MDBOOK.md's style table and gotchas (escape literal `$`, wire the
  text-fix preprocessor, no `README.md` in src/).

### Step 5 — Resources (download on the spot, as qmd)

`RESOURCES.qmd` at the root is the ledger; per the teach skill, **every entry is
acquired the moment it's added**, and in this workspace acquisition means:

- Lecture slides / papers / references → PDF verbatim into `epN_<slug>/resources/`.
- Web pages (course site, docs, project pages) → snapshot to
  `epN_<slug>/resources/web/<slug>.qmd`: YAML `title`, a provenance blockquote
  (source URL, fetch date, license note), then the content as markdown.
- The video itself → entry marked streaming + note the local cache path from
  `MEDIA.md` (never commit video).
- Find the course's official materials first (most lecture courses publish slides,
  code, and readings per lecture — search the course name + lecturer + term); they
  beat any third-party summary. Record each episode's official-materials links in
  its `resources/web/` snapshot and cite them from the episode's lessons.

Before finishing any session: every `RESOURCES.qmd` entry has a local path or an
explicit streaming-only/paywalled note.

### Step 6 — Marimo notebook

Each episode gets `epN_<slug>/notebooks/<slug>.py` — an interactive companion that
runs the lecture's central artifact: the algorithm the lecture teaches, the
worked example, the visualization of the phenomenon. Conventions:

- marimo app with `app_title`, `hide_code` markdown cells explaining each section,
  LaTeX via `$...$`/`$$...$$` in `mo.md`, interactive controls (`mo.ui.slider`,
  `mo.ui.text`) wherever a parameter is pedagogically interesting.
- Self-contained: synthetic data or tiny bundled samples by default; if it needs a
  download, cache into `epN_<slug>/data/` and degrade gracefully offline.
- **Verify by execution**: `uv run python
  ~/.agents/skills/video-teach/scripts/run_marimo_notebook.py
  epN_<slug>/notebooks/<slug>.py` — it imports the module, runs every cell via
  `app.run(defs={"mo": marimo})`, and detects a raised cell by diffing the
  notebook's statically declared cell outputs against the definitions the run
  actually produced (headless marimo swallows plain cell exceptions —
  verified on 0.25.0). Any failure exits nonzero. (Plain `marimo export html`
  is NOT a verifier here: it exits 0 on broken cells AND wrongly exits 1 on
  correct mo-using notebooks.) Reference the notebook from the episode overview
  chapter and the relevant lessons (repo-relative path in prose).

### Step 7 — Wrap the episode

1. `epN_<slug>/README.md`: video link + title + duration, the slide index summary,
   what was built (lessons, notebook, resources), open gaps.
2. Learning records when the session surfaced something non-obvious (a ZPD finding,
   a transcription convention decision, a bug in extracted material).
3. Update root `RESOURCES.qmd` / `NOTES.qmd`; bump the episode's row in the book's
   `about.md` progress table (keep this table — it is the resume anchor).
4. Commit at episode boundaries (`ep3: transcript, slides, 3 lessons, notebook`); on a
   long episode, commit at pipeline-step boundaries too (`ep3: transcript + slides`) —
   never leave hours of transcript/slide work uncommitted.

## Conventions

- **Timestamps as the join key** across slide filenames, slides/README.md, SRT, and
  lesson citations — never assume section headers line up 1:1 with slides.
- **Formulas are transcribed as text** in transcripts and the slides index; the
  slide image outranks the spoken formula when they disagree.
- **Honest gaps**: if a notebook can't reproduce a claimed number (library drift,
  missing data), say so in the episode README with what was checked — never tune
  until it matches.
- **Per-episode placement is not negotiable**: only AGENTS.md, MISSION/RESOURCES/NOTES/
  MEDIA, pyproject.toml, .python-version, .gitignore, and mdbook/ are root-level;
  everything else lives in `epN_<slug>/`.
- **New session in an existing course**: read AGENTS.md → NOTES.qmd → the book's
  `about.md` progress table → `git log --oneline` + `git status` → the current
  episode's README.md, then resume the pipeline at its first incomplete step (the
  checklist below defines each step's end state: raw transcript + `.clean.md`
  present = Step 1 done, `slides/README.md` + `slides_ocr.json` present = Step 2
  done, `.verbal.md` + tagged `.clean.srt` present = Step 3 done, …).
- Skill-scripts and extractors are regenerable; never commit `.venv`, caches,
  build output, or media.

## Verification checklist (per episode, before commit)

- [ ] transcript: `<slug>.raw.vtt`, `.clean.md` (slide refs + slide index assembled), and
      `.verbal.md` present; corrections.json accounted for every correction-brief finding
- [ ] slides: count sane vs lecture length; every PNG named `slideK_<slug>_<MmSSs>.png`;
      `slides/README.md` table covers every slide with formulas verified against images
- [ ] book: new chapters in `SUMMARY.md`; `mdbook build` zero warnings; exercises all answered
- [ ] notebook: `run_marimo_notebook.py` exits 0 — the execution bar; headless
      `marimo export html` can silently skip `mo` injection (an HTML export into
      `output/` is optional); linked from the episode's book chapters
- [ ] resources: every RESOURCES.qmd entry added this session has a local path or
      streaming-only note
- [ ] episode README current; one git commit for the episode
