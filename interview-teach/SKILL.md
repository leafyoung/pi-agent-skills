---
name: interview-teach
description: >-
  Prepare the user for a specific job interview, starting from the job spec.
  Builds a lighter teaching workspace per application with four strands -
  background (company, role, domain), knowledge (what the JD demands vs what
  the candidate can already defend), interviewer (who they are, their work,
  the process stages), and drill (Q&A banks, timed mocks, spaced retrieval) -
  in either planned mode (full JD-mapped curriculum in one go) or
  session-driven mode (grows per session, scheduled backward from the
  interview date). Use when the user asks to "prepare me for the X interview",
  "build interview prep from this job spec", "drill me on the Y role", shares
  a job description for interview preparation, or asks for mock-interview or
  application-specific study notes. Pairs with the teach skill for the two
  teaching principles and lesson anatomy; lighter than teach - no mirrors, no
  quarto, no notebook machinery.
---

# Interview Teach

Prepare the user to *perform* in one specific interview - not to master the
domain. The input is usually a job spec from a careers page, plus whatever
exists of an interviewer profile and the candidate's background. Depth is
calibrated to the interview: **interview-level fluency, not exam-level depth** -
knowing what to say, in what order, with which numbers, and where to honestly
say "never hands-on, but here's what I understand".

Read first: the **teach** skill's "How to Teach" (the two principles) and
lesson anatomy (Motivate/Establish/Connect/Check, exercises with answers).
Everything else in this skill overrides or replaces teach's machinery for
interview prep - it is deliberately lighter.

## Workspace - one section per application

Canonical layout: **one shared book** (e.g. a "2026 Job Search" book) with one
section per application, and one folder per application inside it. A standalone
per-application book is fine when an application is extensive enough to stand
alone.

```
<job-search-book>/                # mdbook; SUMMARY has a section per application
├── book.toml
└── src/
    ├── SUMMARY.md                # # <Application> section per application
    └── <application>/
        ├── MISSION.md            # from the job spec (format below)
        ├── INTERVIEW_CURRICULUM.md  # planned mode's artifact (below)
        ├── lessons/              # 0001-<slug>.md, incrementing
        ├── reference/            # cheat sheets, Q&A drill bank, formulas
        ├── GLOSSARY.md           # optional; role jargon the candidate must use
        ├── NOTES.md              # assumptions, session log
        ├── RESOURCES.md          # acquisition ledger (teach rules apply)
        ├── learning-records/     # corrections and calibration findings
        └── source/               # the INPUTS: job spec, interviewer profile,
                                  #   vehicle PDFs/papers, demos
```

Heavy data (cloned repos, datasets) stays OUT of `src/` - park it beside the
book and leave a pointer file in `source/` (a build copies everything in `src/`).
The candidate's own claims must be grounded in their real history; the
interviewer's work is studied, never claimed. Positioning honesty is a hard
rule: do not prepare content that presents another person's track record as
the candidate's.

## Mission - from the job spec

Write `MISSION.md` first: **Why** (the application, in one paragraph) /
**Success looks like** (interview-performance outcomes: "deliver X from memory
under pressure", "answer the value-add question without being defensive",
"frame IFRS-17 ignorance honestly") / **Constraints** (interview date - record
it even when unconfirmed and update when known; interview language; time-box) /
**Out of scope** (depth the role does not demand). Two standing constraints:
positioning honesty as above, and depth calibration - focus on what the
interview tests, explicitly out-of-scope what it does not.

## Parsing the job spec

Extract the responsibility headings and qualifications verbatim - they are the
knowledge strand's source of truth, and the curriculum map cites them. Extract
every named fact about the process (stages, screens, who interviews) - it is
the interviewer strand's skeleton. Distinguish carefully **who is who**: an
interviewer profile is a study object, not the candidate's biography (this
exact confusion happened once and had to be corrected by a learning record).
Record unknowns (date, format, interviewer names) in the mission and update as
intel arrives - each new fact (a stage scheduled, an interviewer named) is a
session-driven trigger.

## The four strands

- **Background** - the company in 30 seconds (founding, business model, what
  makes this seat attractive), the domain 101 the candidate lacks (a quant
  moving into insurance needs reinsurance 101, not actuarial exams), and a
  memorizable role pitch in the candidate's own words. Test: could the
  candidate say it back if asked?
- **Knowledge** - one lesson per JD responsibility heading the candidate cannot
  already defend, plus the qualifications that make the answers credible.
  Knowledge threads (statistics, risk, research integrity) weave through
  lessons rather than getting standalone survey lessons. Every lesson ends
  with **an interview answer to practise**, not just understanding.
- **Interviewer** - who interviews at each stage and what their job in that
  stage is (a recruiter screens for real-but-box-fitting and clean logistics;
  a 15-minute screen decides whether to escalate); their published work,
  strategies, and frameworks as study objects, so the candidate can engage
  credibly *without claiming them*; the questions each stage will almost
  certainly ask.
- **Drill** - the Q&A bank (weak answer vs strong answer per question), the
  formula/number speed drills, and the mock-interview capstone. See Drill
  pedagogy below.

Plus the **positioning** thread across all strands: mapping the candidate's
real history onto the JD's hard requirements (lead cards), the value-add
answer for the candidate's weak flank, and honest-ignorance framings for
gaps that cannot be closed in time.

## Planned mode

The default when the interview is soon and the user wants the course in one
go. Parse the JD into the curriculum artifact `INTERVIEW_CURRICULUM.md`: a
table - lesson, JD focus (verbatim heading), tangible interview outcome - plus
the knowledge threads and the background/interviewer/drill lessons the table
implies. Size it to the time available: a brief application is 5 lessons
(domain 101 -> products -> regulatory/company -> mock); an extensive one maps
every JD heading and runs to 14+. Author all of it, acquire the resources,
build, commit. Every lesson ends with the answer to practise; the mock and
the drill bank are always included, whatever the size.

## Session-driven mode

When the user will practise across sessions before the date, or the process
is still unfolding (stages not yet scheduled, interviewers not yet named):

- First session: parse the spec, write the mission, scaffold the book,
  author the first 1-2 lessons (usually background + the JD's hardest
  knowledge heading), and record the plan as a curriculum table with unwritten
  rows marked.
- Every later session: absorb new intel first (a stage scheduled, an
  interviewer named, a call's outcome - each mints a lesson or a correction:
  bluecrest's recruiter-screen lesson exists because stage one got scheduled);
  then drill per the countdown (below); then author toward the plan.
- **Schedule backward from the interview date**: spaced retrieval practice
  over the Q&A bank, the formula drills, and the mock - heavier as the date
  approaches, in the interview's language. If the date is unconfirmed, say so
  in the mission and schedule when it lands.
- Corrections are learning records (the interviewer-profile confusion above
  is the canonical example).

Both modes end sessions the same way: resources ledgered, book built with
zero warnings, committed.

## Drill pedagogy

Drills are the point of the whole skill - knowledge lessons exist to feed
them. The rules that make them work:

- **Say the strong answer out loud**, then check it against the bank. Never
  read the weak answer during practice - reading it contaminates retrieval.
- **Weak/strong pairs** in the bank: the weak answer is the plausible
  textbook-level response; the strong answer names the framework, surfaces
  the non-obvious tension, takes a quantified point of view, and lands a
  senior-level day-one question. Aim for point-of-view on every substantive
  question; deliver a day-one question at least once per interview.
- **Timed, scored mocks** as the capstone: a script an interviewer could read
  aloud (parts, per-question time boxes), a scoring rubric with dimensions
  and a pass line, and a rule for what to re-drill below the line. Solo
  fallback: record yourself, score after.
- **Speed drills** for formulas and numbers the mission demands "with
  numbers, not vibes".
- Practice in the interview's language, whatever the working material's.

## Exit gate - ready for the interview

- [ ] every JD responsibility heading has a lesson or an explicit
      already-defensible note, and each lesson's answer has been practised
      out loud
- [ ] the Q&A bank covers the mock's questions; the mock was run against the
      rubric and passed its line (or the weak dimensions have a re-drill
      plan)
- [ ] background: firm-in-30-seconds and role pitch can be said from memory;
      interviewer strand is current with the latest process intel
- [ ] cheat sheets (formulas, frameworks) exist and match the lessons
- [ ] resources acquired, book built zero warnings, committed

## Editing This Skill

Real files live in `~/.agents/shared_skills/interview-teach/` (symlinked from
`~/.agents/skills/`); stage exactly that path when committing to the
shared-skills repo. This skill changes only when the method changes - course
content and application history live in the job-search book.
