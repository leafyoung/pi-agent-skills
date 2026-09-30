"""Tests for the transcript-foundation scripts (transcript_layers.py, slide_ocr.py).

Run:  python3 -m pytest <this-dir> -q
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tl = load("transcript_layers")
so = load("slide_ocr")

VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.500
Yang Ye: Good evening everyone, today we study the Kolesky decomposition.

2
00:00:04.600 --> 00:00:07.900
Yang Ye: The Black Shores model needs
a matrix.

3
00:00:08.000 --> 00:00:12.000
Yang Ye: so thank you.

4
00:01:02.000 --> 00:01:06.000
Student: Is the four loop syntax correct?
"""

SRT = """1
00:00:01,000 --> 00:00:04,500
Yang Ye: Good evening everyone, today we study the Kolesky decomposition.

2
00:00:04,600 --> 00:00:07,900
Yang Ye: The Black Shores model needs a matrix.
"""


# ---------- parse_timing ----------

def test_vtt_parses_all_cues_with_eof_flush(tmp_path):
    p = tmp_path / "raw.vtt"
    p.write_text(VTT)
    cues = tl.parse_timing(p)
    assert len(cues) == 4                      # trailing cue captured (EOF flush)
    assert cues[1][2] == "Yang Ye: The Black Shores model needs a matrix."  # label kept in raw text
    assert cues[0][1] == 4.5                   # ms precision kept
    assert cues[3][0] == 62.0


def test_srt_comma_milliseconds(tmp_path):
    p = tmp_path / "raw.srt"
    p.write_text(SRT)
    cues = tl.parse_timing(p)
    assert len(cues) == 2
    assert cues[0][0] == 1.0 and cues[1][1] == 7.9


def test_parse_skips_webvtt_headers_and_indices(tmp_path):
    p = tmp_path / "raw.vtt"
    p.write_text(VTT)
    cues = tl.parse_timing(p)
    assert all("WEBVTT" not in c[2] and not c[2].isdigit() for c in cues)


# ---------- speaker splitting ----------

def test_split_speaker_handles_spaces_in_labels():
    assert tl.split_speaker("Yang Ye: hello there") == ("Yang Ye", "hello there")


def test_split_speaker_no_label():
    assert tl.split_speaker("plain text") == ("", "plain text")


# ---------- glossary ----------

def test_glossary_fixes_known_terms():
    assert tl.glossary("the Kolesky decomposition and the four loop") == \
        "the Cholesky decomposition and the for loop"


def test_glossary_is_idempotent():
    once = tl.glossary("the Kolesky decomposition")
    assert tl.glossary(once) == once


# ---------- verbal layer ----------

def test_verbal_layer_preserves_fillers_and_stamps(tmp_path):
    cues = tl.parse_timing(tmp_path / "v.vtt") if (tmp_path / "v.vtt").write_text(VTT) else []
    md = tl.verbal_md(cues, "T")
    assert "[00:00:08] **Yang Ye:** so thank you." in md             # filler PRESERVED
    assert "[00:01:02] **Student:** Is the for loop syntax correct?" in md  # glossary applied, label bold


# ---------- clean-side correction mechanics ----------

def test_apply_corrections_counts_applied_and_missed():
    text = "the Kolesky decomposition. The Black Shores model."
    reps = [("Kolesky", "Cholesky", -1), ("Black Shores", "Black-Scholes", 1),
            ("not present", "x")]
    out, applied, missed = tl.apply_corrections(text, reps)
    assert "Cholesky" in out and "Black-Scholes" in out
    assert len(applied) == 2 and missed == ["not present"]


def test_load_corrections_rejects_malformed(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"replacements": [["only-one-field"]]}')
    with pytest.raises(SystemExit):
        tl.load_corrections(p)


def test_load_corrections_accepts_replace_all_and_counts(tmp_path):
    p = tmp_path / "ok.json"
    p.write_text('{"replacements": [["a", "b", "replace_all"], ["c", "d", 2]], "notes": "n"}')
    reps, notes = tl.load_corrections(p)
    assert reps == [("a", "b", -1), ("c", "d", 2)] and notes == "n"


# ---------- correction brief ----------

def test_brief_groups_cues_by_slide_window_and_lists_orphans(tmp_path):
    slides = [
        {"file": "s1.png", "start_s": 0, "end_s": 8, "start": "0m00s", "ocr": "Cholesky: A = L L^T"},
        {"file": "s2.png", "start_s": 8, "end_s": 120, "start": "0m08s", "ocr": "for loops"},
    ]
    cues = tl.parse_timing(tmp_path / "v.vtt") if (tmp_path / "v.vtt").write_text(VTT) else []
    cues = tl.parse_timing if False else cues
    brief = tl.correction_brief(cues, slides, "T")
    assert "## Slide 1" in brief and "## Slide 2" in brief
    assert "Kolesky decomposition" in brief           # brief shows RAW cues (pre-correction)
    assert "No slide on screen" in brief and "Is the four loop" in brief  # 62s cue is orphaned
    assert brief.index("Cholesky: A = L L^T") < brief.index("Transcript cues in window")


# ---------- slide_ocr helpers ----------

def test_slide_name_timestamps():
    cases = {"slide1_0m00s.png": 0, "slide12_45m30s.png": 2730,
             "s03_105m30s.png": 6330, "x_1h05m10s.png": 3910}
    for name, want in cases.items():
        assert so.mmss_to_s(name) == want


def test_slide_name_regex_ignores_non_slides():
    assert so.NAME_TS.search("bad.png") is None


# ---------- fix-clean / assemble (CLI end-to-end) ----------

def run_cli(*argv):
    return subprocess.run([sys.executable, str(SCRIPTS / "transcript_layers.py"), *argv],
                          capture_output=True, text=True)


def test_fix_clean_applies_in_place_and_appends_index_once(tmp_path):
    clean = tmp_path / "ep.clean.md"
    clean.write_text("# Ep\n\nWe studied the Kolesky decomposition today.\n")
    ocr = tmp_path / "slides_ocr.json"
    ocr.write_text(json.dumps([{"file": "s1.png", "start_s": 0, "end_s": 600,
                                "start": "0m00s", "ocr": "Cholesky: A = L L^T"}]))
    corr = tmp_path / "corrections.json"
    corr.write_text('{"replacements": [["Kolesky", "Cholesky", "replace_all"]]}')
    argv = ("--fix-clean", str(clean), "--apply-corrections", str(corr),
            "--slides-ocr", str(ocr), "--assemble")
    r = run_cli(*argv)
    assert r.returncode == 0, r.stderr
    t = clean.read_text()
    assert "Kolesky" not in t and "Cholesky decomposition" in t
    assert t.count("## Slide index") == 1 and "Slide 1 @ 0m00s" in t
    # rerun: idempotent (index not duplicated), already-fixed text untouched
    r2 = run_cli(*argv)
    assert r2.returncode == 0, r2.stderr
    t2 = clean.read_text()
    assert t2.count("## Slide index") == 1 and "Kolesky" not in t2


def test_vtt_only_run_never_creates_clean_md(tmp_path):
    vtt = tmp_path / "raw.vtt"
    vtt.write_text(VTT)
    r = run_cli("--vtt", str(vtt), "--out", str(tmp_path / "ep"))
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "ep.verbal.md").exists()
    assert not (tmp_path / "ep.clean.md").exists()   # .clean.md ownership stays with transcribe-video


def test_missing_slides_ocr_with_brief_flag_fails_loudly(tmp_path):
    vtt = tmp_path / "raw.vtt"
    vtt.write_text(VTT)
    r = run_cli("--vtt", str(vtt), "--out", str(tmp_path / "ep"), "--emit-correction-brief")
    assert r.returncode != 0


# ---------- SRT slide tagging ----------

def test_tag_srt_tags_by_window_and_shows_on_change():
    slides = [
        {"file": "s1.png", "start_s": 0, "end_s": 8, "start": "0m00s", "ocr": "Cholesky"},
        {"file": "s2.png", "start_s": 8, "end_s": 600, "start": "0m08s", "ocr": "for loops"},
    ]
    srt = ("1\n00:00:01,000 --> 00:00:04,500\nYang Ye: the Kolesky decomposition\n\n"
           "2\n00:00:09,000 --> 00:00:12,000\nYang Ye: the four loop\n")
    once = tl.tag_srt_text(srt, slides)
    assert "[Slide 1] Yang Ye: the Kolesky" in once
    assert "[Slide 2] Yang Ye: the four loop" in once


def test_tag_srt_is_idempotent():
    slides = [{"file": "s1.png", "start_s": 0, "end_s": 600, "start": "0m00s", "ocr": "x"}]
    srt = "1\n00:00:01,000 --> 00:00:04,500\nYang Ye: hello there\n"
    once = tl.tag_srt_text(srt, slides)
    twice = tl.tag_srt_text(once, slides)
    assert once == twice and once.count("[Slide 1]") == 1


def test_assemble_only_mode_adds_index_without_corrections(tmp_path):
    clean = tmp_path / "ep.clean.md"
    clean.write_text("# W\n\nBody text.\n")
    slides = tmp_path / "slides_ocr.json"
    slides.write_text(json.dumps([
        {"file": "slide1_ep_0m30s.png", "start_s": 30, "end_s": 600,
         "start": "0m30s", "ocr": "Cholesky decomposition"}]))
    sys.argv = ["tl", "--fix-clean", str(clean), "--assemble",
                "--slides-ocr", str(slides)]
    tl.main()
    out = clean.read_text()
    assert "## Slide index" in out and "Slide 1 @ 0m30s" in out


def test_assemble_requires_slides_ocr(tmp_path, capsys):
    clean = tmp_path / "c.clean.md"
    clean.write_text("# W\n\nBody.\n")
    sys.argv = ["tl", "--fix-clean", str(clean), "--assemble"]
    with pytest.raises(SystemExit) as ei:
        tl.main()
    assert "--assemble requires --slides-ocr" in str(ei.value)


def test_empty_timing_file_warns_and_writes_header_only(tmp_path, capsys):
    vtt = tmp_path / "empty.raw.vtt"
    vtt.write_text("WEBVTT\n")
    out_stem = tmp_path / "e"
    sys.argv = ["tl", "--vtt", str(vtt), "--out", str(out_stem)]
    tl.main()
    captured = capsys.readouterr()
    assert "yielded 0 cues" in captured.err
    verbal = (tmp_path / "e.verbal.md").read_text()
    assert "verbal transcript" in verbal and "[00:00:01]" not in verbal


def test_tag_srt_flip_back_outside_windows_keeps_last_slide_number():
    slides = [
        {"file": "s1", "start_s": 0, "end_s": 100, "start": "0m00s", "ocr": "A"},
        {"file": "s2", "start_s": 100, "end_s": 200, "start": "1m40s", "ocr": "B"},
    ]
    srt = "1\n00:02:30.000 --> 00:02:40.000\ntext mid gap\n\n2\n00:02:50.000 --> 00:03:00.000\nmore"
    out = tl.tag_srt_text(srt, slides)
    assert "[Slide 2]" in out  # t=150 and t=170 fall outside windows -> last slide


def test_zero_cue_guard_message():
    assert "clean-srt" in "nothing to do: pass --vtt (verbal/brief), --fix-clean [--apply-corrections] [--assemble], and/or --clean-srt + --slides-ocr"
