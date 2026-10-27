import re
import Stemmer


_STEMMER = Stemmer.Stemmer("english")


def tokenize_text(text: str) -> list[str]:
    """Return lowercase tokens, including parts of compound identifiers."""
    tokens: list[str] = []

    for word in re.findall(r"\w\w+", text):
        tokens.append(word.lower())

        parts = word.replace("_", " ")
        parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", parts).lower().split()

        if len(parts) > 1:
            tokens.extend(part for part in parts if len(part) >= 2)

    stemmed: list[str] = _STEMMER.stemWords(tokens)
    return stemmed
