"""
test_sign_pipeline.py
----------------------
Run with:  python -m pytest sign_language/tests/ -v
Or standalone: python sign_language/tests/test_sign_pipeline.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from isl_preprocessor import ISLPreprocessor, text_to_isl_tokens
from gesture_mapper import GestureMapper, GestureClip


# ─── ISLPreprocessor tests ────────────────────────────────────────────────

def test_article_removal():
    pre = ISLPreprocessor()
    _, isl = pre.preprocess("The cat is on the mat.")
    assert "THE" not in isl.split()
    assert "IS" not in isl.split()

def test_negation_moved_to_end():
    pre = ISLPreprocessor()
    tokens, _ = pre.preprocess("I don't know.")
    assert tokens[-1] == "NOT", f"Expected NOT at end, got {tokens}"
    assert "KNOW" in tokens

def test_wh_moved_to_end():
    pre = ISLPreprocessor()
    tokens, _ = pre.preprocess("What is your name?")
    assert tokens[-1] == "WHAT"

def test_contraction_expansion():
    pre = ISLPreprocessor()
    tokens, _ = pre.preprocess("I'm going to school.")
    assert "I" in tokens

def test_empty_input():
    pre = ISLPreprocessor()
    tokens, isl = pre.preprocess("")
    assert tokens == []
    assert isl == ""

def test_simple_sentence():
    tokens = text_to_isl_tokens("Please help me.")
    assert "PLEASE" in tokens
    assert "HELP" in tokens
    assert "ME" in tokens


# ─── GestureMapper tests ──────────────────────────────────────────────────

def test_mapper_exact_match():
    mapper = GestureMapper(assets_root="assets/gestures")
    clips = mapper.map_token("HELLO")
    assert len(clips) == 1
    assert clips[0].word == "HELLO"

def test_mapper_unknown_falls_back():
    mapper = GestureMapper(assets_root="assets/gestures")
    clips = mapper.map_token("XYZABC_UNKNOWN_WORD_LONG")
    # Long unknown word → UNKNOWN fallback
    assert any(c.word == "UNKNOWN" for c in clips)

def test_mapper_short_unknown_fingerspells():
    mapper = GestureMapper(assets_root="assets/gestures")
    clips = mapper.map_token("XYZ")
    # Short unknown word ≤ 6 chars → fingerspell
    modes = [c.mode for c in clips]
    assert all(m in ("fingerspell", "missing") for m in modes)

def test_mapper_sentence():
    mapper = GestureMapper(assets_root="assets/gestures")
    tokens = ["I", "WANT", "LEARN"]
    clips = mapper.map_sentence(tokens)
    words = [c.word for c in clips]
    assert "I" in words
    assert "WANT" in words

def test_coverage_report():
    mapper = GestureMapper(assets_root="assets/gestures")
    tokens = ["HELLO", "WORLD"]
    report = mapper.coverage_report(tokens)
    assert "total_clips" in report
    assert "coverage_pct" in report


# ─── Runner ──────────────────────────────────────────────────────────────

def run_all():
    tests = [
        test_article_removal,
        test_negation_moved_to_end,
        test_wh_moved_to_end,
        test_contraction_expansion,
        test_empty_input,
        test_simple_sentence,
        test_mapper_exact_match,
        test_mapper_unknown_falls_back,
        test_mapper_short_unknown_fingerspells,
        test_mapper_sentence,
        test_coverage_report,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
