
"""Tokenizer shared by the indexer and the retriever."""

import re
import Stemmer


_STEMMER = Stemmer.Stemmer("english")


def tokenize_text(text: str) -> list[str]:
    """Return lowercase stemmed tokens, including compound identifier parts.

    Each word is kept whole and also split on underscores and camelCase,
    so ``max_num_seqs`` and ``maxNumSeqs`` share the tokens max, num, seq.

    Args:
        text: Raw text of a chunk or a user query.

    Returns:
        List of stemmed tokens; empty if the text has no word of 2+ chars.
    """
    tokens: list[str] = []

    for word in re.findall(r"\w\w+", text):
        tokens.append(word.lower())

        parts = word.replace("_", " ")
        parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", parts).lower().split()

        if len(parts) > 1:
            tokens.extend(part for part in parts if len(part) >= 2)

    stemmed: list[str] = _STEMMER.stemWords(tokens)
    return stemmed
