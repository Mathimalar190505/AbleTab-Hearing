"""
utils/braille.py - Braille Output (Software Simulation)
=========================================================
Maps characters to Grade 1 Braille 8-pin dot patterns.
On laptop: prints a visual dot pattern to terminal.

8-pin cell layout:
  Pin 1  Pin 4
  Pin 2  Pin 5
  Pin 3  Pin 6
  Pin 7  Pin 8  ← extended pins

To extend for hardware:
  Connect solenoids/pins to GPIO or Arduino
  and implement output_to_gpio() below.
"""

# Grade 1 Braille — (raised dot numbers)
BRAILLE_MAP = {
    'a': (1,),           'b': (1, 2),         'c': (1, 4),
    'd': (1, 4, 5),      'e': (1, 5),          'f': (1, 2, 4),
    'g': (1, 2, 4, 5),   'h': (1, 2, 5),       'i': (2, 4),
    'j': (2, 4, 5),      'k': (1, 3),          'l': (1, 2, 3),
    'm': (1, 3, 4),      'n': (1, 3, 4, 5),    'o': (1, 3, 5),
    'p': (1, 2, 3, 4),   'q': (1, 2, 3, 4, 5), 'r': (1, 2, 3, 5),
    's': (2, 3, 4),      't': (2, 3, 4, 5),    'u': (1, 3, 6),
    'v': (1, 2, 3, 6),   'w': (2, 4, 5, 6),    'x': (1, 3, 4, 6),
    'y': (1, 3, 4, 5, 6),'z': (1, 3, 5, 6),    ' ': (),
}


def display_braille_text(text):
    """
    Print a visual Braille representation to the terminal.
    Useful for verifying mappings and demonstrating to sighted users.
    """
    print("\n  [Braille Simulation]")
    print("  " + "-" * (len(text) * 5))

    for char in text.lower():
        dots = BRAILLE_MAP.get(char, ())
        row1 = ("●" if 1 in dots else "○") + ("●" if 4 in dots else "○")
        row2 = ("●" if 2 in dots else "○") + ("●" if 5 in dots else "○")
        row3 = ("●" if 3 in dots else "○") + ("●" if 6 in dots else "○")
        print(f"  [{char.upper()}] {row1}  {row2}  {row3}")

    print("  " + "-" * (len(text) * 5))


def text_to_dot_patterns(text):
    """Return list of (char, dot_tuple) for each character."""
    return [(c, BRAILLE_MAP.get(c.lower(), ())) for c in text]
