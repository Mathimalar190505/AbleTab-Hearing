"""
gesture_mapper.py
-----------------
Converts English text → ISL token sequence (video clips to play).

Pipeline inside this module:
  1. Text cleaning
  2. Rule-based ISL grammar conversion  (SOV order, drop articles/auxiliaries)
  3. Word → video lookup
  4. Fallback → fingerspell unknown words
  5. Return ordered list of GestureToken objects
"""

import re
from dataclasses import dataclass, field
from isl_preprocessor import ISLPreprocessor


# ──────────────────────────────────────────────
# DATA CLASSES
# ──────────────────────────────────────────────

@dataclass
class GestureToken:
    word: str                    # original word (for display)
    video_path: str | None       # path to sign video (None = pause)
    token_type: str              # "sign" | "fingerspell" | "pause"
    fingerspell_chars: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# ISL GRAMMAR RULES
# (rule-based, no ML — sufficient for demos)
# ──────────────────────────────────────────────

# Words that ISL typically drops
DROPPED_WORDS = {
    "a", "an", "the",                          # articles
    "is", "am", "are", "was", "were",          # aux verbs (be)
    "do", "does", "did",                       # aux (do)
    "has", "have", "had",                      # aux (have)
    "will", "would", "shall", "should",        # modals
    "can", "could", "may", "might",
    "of", "to",                                # common prepositions often dropped
}

# Negation — place sign AFTER main verb in ISL
NEGATION_WORDS = {"not", "n't", "never", "no", "nothing"}

# Question words — placed at END in ISL wh-questions
WH_WORDS = {"what", "who", "where", "when", "why", "how", "which"}


def _clean_text(text: str) -> str:
    """Lowercase, remove punctuation (keep apostrophes for contractions)."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _expand_contractions(text: str) -> str:
    contractions = {
        "don't": "do not", "doesn't": "does not", "didn't": "did not",
        "isn't": "is not", "aren't": "are not", "wasn't": "was not",
        "weren't": "were not", "won't": "will not", "can't": "cannot",
        "couldn't": "could not", "i'm": "i am", "i've": "i have",
        "i'll": "i will", "i'd": "i would", "you're": "you are",
        "they're": "they are", "we're": "we are", "it's": "it is",
        "that's": "that is", "there's": "there is",
    }
    for contraction, expansion in contractions.items():
        text = text.replace(contraction, expansion)
    return text


def convert_to_isl_grammar(words: list[str]) -> list[str]:
    """
    Applies simplified ISL grammar rules:
    1. Drop function words (articles, auxiliaries)
    2. Move wh-words to end
    3. Move negation to after the main verb
    4. Keep content words in subject-object-verb order (approximate)

    This is a heuristic — it won't be perfect for all sentences
    but works well enough for demos and common classroom phrases.
    """
    filtered = []
    wh_collected = []
    neg_collected = []
    has_negation = False

    for w in words:
        w_clean = w.strip("'")
        if w_clean in DROPPED_WORDS:
            continue
        if w_clean in NEGATION_WORDS:
            has_negation = True
            neg_collected.append(w_clean)
            continue
        if w_clean in WH_WORDS:
            wh_collected.append(w_clean)
            continue
        filtered.append(w_clean)

    # Append negation after content words (ISL: "school go NOT")
    if has_negation:
        filtered.extend(neg_collected)

    # Append wh-words at end (ISL: "name your WHAT")
    filtered.extend(wh_collected)

    return filtered


# ──────────────────────────────────────────────
# MAIN MAPPER CLASS
# ──────────────────────────────────────────────

class GestureMapper:
    """
    Maps a sentence string to an ordered list of GestureTokens.
    """

    def __init__(self, preprocessor: ISLPreprocessor):
        self.pre = preprocessor

    def map_sentence(self, sentence: str,
                     use_isl_grammar: bool = True) -> list[GestureToken]:
        """
        Full pipeline:
          clean → grammar → word lookup → fingerspell fallback
        Returns list of GestureToken in playback order.
        """
        # Step 1: clean + expand
        text = _expand_contractions(_clean_text(sentence))
        words = text.split()

        # Step 2: ISL grammar reorder
        if use_isl_grammar:
            words = convert_to_isl_grammar(words)

        # Step 3: map each word
        tokens = []
        for word in words:
            if not word:
                continue
            token = self._resolve_word(word)
            tokens.append(token)

            # Brief pause token after each sign for smoother viewing
            tokens.append(GestureToken(
                word="", video_path=None,
                token_type="pause"
            ))

        return tokens

    def _resolve_word(self, word: str) -> GestureToken:
        # Direct sign match
        video = self.pre.get_word_video(word)
        if video:
            return GestureToken(word=word, video_path=video,
                                token_type="sign")

        # Fingerspell fallback
        chars = [c for c in word if c.isalpha()]
        char_videos = []
        for c in chars:
            v = self.pre.get_alpha_video(c)
            if v:
                char_videos.append((c, v))

        if char_videos:
            return GestureToken(
                word=word,
                video_path=None,          # avatar_player handles char_videos
                token_type="fingerspell",
                fingerspell_chars=char_videos   # [(char, path), …]
            )

        # Completely unknown — just pause
        print(f"[GestureMapper] WARNING: no sign or fingerspell for '{word}'")
        return GestureToken(word=word, video_path=None, token_type="pause")

    def map_with_cslrt(self, sentence: str) -> list[GestureToken] | str:
        """
        First tries ISL-CSLRT sentence-level match (realistic full sentence).
        Falls back to word-level mapping if no close match.

        Returns:
          str  → path to CSLRT video  (play as single clip)
          list → word-level GestureToken list
        """
        cslrt_video = self.pre.get_cslrt_video(sentence)
        if cslrt_video:
            print(f"[GestureMapper] ISL-CSLRT match found: {cslrt_video}")
            return cslrt_video           # caller plays this single video
        return self.map_sentence(sentence)


# ──────────────────────────────────────────────
# Quick self-test
# ──────────────────────────────────────────────
if __name__ == "__main__":
    from isl_preprocessor import ISLPreprocessor
    pre = ISLPreprocessor()
    mapper = GestureMapper(pre)

    test = "What is your name?"
    result = mapper.map_sentence(test)
    for t in result:
        print(t)
