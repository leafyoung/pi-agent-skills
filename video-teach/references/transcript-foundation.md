# Transcript foundation — two layers + slide-assisted correction

Shared pipeline for `video-teach` (Step 3) and `post-lecture-slides-update`
(Phase 1a): from a raw `.vtt`/`.srt`, derive the verbatim **verbal layer** and
correct the readable **clean layer** against slide-OCR ground truth. This
matters in proportion to how technical the lecture is: ASR fails precisely on
the material these courses teach — named theorems and methods (Cholesky,
Bachelier, Crank-Nicolson), library and function names (NumPy, ggplot2,
`norm.s.inv`), linearized formulas, and numbers — while the slides spell every
one of them correctly.

## Commands (chronological; each step a separate invocation)

```bash
L=~/.agents/skills/video-teach/scripts/transcript_layers.py
# 1. verbal layer from the raw VTT (deterministic; never LLM-edited later)
python3 $L --vtt <slug>.raw.vtt --out <slug> --title "<Episode title>"
# 2. OCR the kept slides (tesseract on PATH) -> slides_ocr.json (+ .md index)
python3 ~/.agents/skills/video-teach/scripts/slide_ocr.py <slides-dir> --duration <video-seconds>
# 3. emit the correction brief: per slide, OCR + the cues spoken in its window
python3 $L --vtt <slug>.raw.vtt --out <slug> --title "<Episode title>" \
  --slides-ocr <slides-dir>/slides_ocr.json --emit-correction-brief
# 4. work the brief (Read tool): fix garbled terms against the slide OCR, then
#    write corrections.json = {"replacements": [["garbled","correct","replace_all"], ...]}
# 5. fine-tune the .clean.md IN PLACE: term fixes + slide index appended
python3 $L --fix-clean <slug>.clean.md --apply-corrections corrections.json \
  --slides-ocr <slides-dir>/slides_ocr.json --assemble
# 6. map slides+OCR onto the cleaned SRT by timing: entries tagged [Slide K]
#    at slide changes (idempotent)
python3 $L --clean-srt <slug>.clean.srt --slides-ocr <slides-dir>/slides_ocr.json
```

For `post-lecture-slides-update`: the clean side usually already exists (the
instructor's transcript); steps 1 and 5 are the ones that run, and `--fix-clean`
fine-tunes that existing file in place. For `video-teach`: the clean layer is
owned by the `transcribe-video` clean pass — step 5 fine-tunes its output.

## Artifacts

- **`<stem>.verbal.md`** — the verbatim layer, by design never LLM-edited:
  `[HH:MM:SS]`-stamped paragraphs, speaker labels, fillers/repetitions/false
  starts preserved; only deterministic glossary casing. Read it for the
  instructor's actual words (emphasis, hedging, asides) — delivery evidence.
- **`<stem>.clean.md`** — the readable layer (owned by the transcribe-video
  clean pass; step 5 never regenerates it): term corrections applied in place
  and a time-stamped `## Slide index` appended. Every downstream step reads
  this layer.
- **`<stem>.clean.srt`** — stays aligned to the video timeline with each entry
  tagged `[Slide K]` at slide changes: the timing-based slide↔transcript map.
- **`correction_brief.md` / `corrections.json`** — working artifacts of the
  correction pass; keep them next to the transcript for provenance.

## Rules

- Wording stays verbatim: fix ASR errors only, never paraphrase; severely
  degraded fragments stay as-is (do not invent).
- Speaker labels untouched; `## Part N` structure untouched.
- When slide OCR and the transcript disagree on a term or number, the OCR
  wins (the slide spells it); on reasoning and emphasis, the transcript wins.
