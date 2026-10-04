import re


_SHOPPING_CONTEXT = r"\b(?:grocer(?:y|ies)|shopping|shop|buy|purchase|market)\b"
_CONTEXT_RULES = (
    (
        re.compile(
            rf"\bto\s+(?:the\s+)?(?P<word>sore)\b(?P<context>[^.!?]{{0,100}}{_SHOPPING_CONTEXT})",
            re.IGNORECASE,
        ),
        "store",
        "In a shopping context, did you mean 'store'?",
    ),
    (
        re.compile(
            r"\bto\s+(?P<word>boutique)\b(?P<context>[^.!?]{0,100}\b(?:shopping|shop|buy|purchase|clothes|clothing)\b)",
            re.IGNORECASE,
        ),
        "a boutique",
        "This shopping phrase may need an article: 'a boutique'.",
    ),
)


def find_context_matches(text):
    """Return high-confidence word-choice and article fixes for known patterns."""
    matches = []
    for pattern, suggestion, message in _CONTEXT_RULES:
        for match in pattern.finditer(text):
            start = match.start('word')
            word = match.group('word')
            matches.append({
                "offset": start,
                "length": len(word),
                "word": word,
                "type": "grammar",
                "message": message,
                "suggestions": [suggestion],
            })
    return matches