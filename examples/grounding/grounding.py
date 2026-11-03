"""Three grounding checks from docket, reduced to their core (standard library only).

The model proposes; code verifies. Each check drops (or refuses) what it cannot verify and says why.
Nothing is repaired: a fixed-up quote would be a quote nobody wrote.

1. check_quote: a quote from a posting must be a real line of that posting, or a span inside it,
   copied verbatim, at most 25 words, and never one that holds a personal-data removal marker.
2. check_fit_rows: a fit verdict of tick or confirm must cite a resume line that exists. A cross
   (a gap) cites none.
3. told_line_gate: when a person tells the app what they did and a model turns it into a resume
   line, every number in the line must be one they said, and every word must be theirs, the
   requirement label's, or a joining word. Otherwise the line is refused and the person's own words
   are used instead.
"""
import re

MAX_QUOTE_WORDS = 25
REMOVAL = re.compile(r"\[(?:email|phone|link|name) removed\]")
JOINING = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to",
    "with", "across", "over", "using", "via", "i", "my", "our", "we",
}
NUMBER = re.compile(r"\d+(?:[.,]\d+)*%?")


# --- 1. quotes from a posting ---------------------------------------------------------------------

def check_quote(item, posting_lines):
    """(quote, None) when the item's quote checks out, else (None, why dropped).

    item: {"line": 1-based line number, "span": optional text inside that line}
    A short line (at most 25 words) is quoted whole, so it is verbatim by construction. A long line
    needs a span, and the span must sit inside the line exactly (whitespace collapsed)."""
    n = item.get("line")
    if not isinstance(n, int) or not 1 <= n <= len(posting_lines):
        return None, "line out of range"
    line = " ".join(posting_lines[n - 1].split())
    if len(line.split()) <= MAX_QUOTE_WORDS:
        quote = line
    else:
        span = " ".join((item.get("span") or "").split())
        if not span:
            return None, "no span for a long line"
        if len(span.split()) > MAX_QUOTE_WORDS:
            return None, "span over 25 words"
        if span not in line:
            return None, "span not in its line"
        quote = span
    if REMOVAL.search(quote):
        return None, "quote carries a removal"
    return quote, None


# --- 2. fit verdicts cite real resume lines -------------------------------------------------------

def check_fit_rows(rows, resume_lines):
    """(kept rows, drops). resume_lines: {line id: text}. A tick or a confirm must cite an existing
    line; a cross must cite none. Whether the line truly supports the claim is the model's judgement,
    which the golden-set eval measures; code guarantees only that the citation is real."""
    kept, drops = [], []
    for row in rows:
        verdict, cited = row.get("verdict"), row.get("line")
        if verdict not in ("tick", "confirm", "cross"):
            drops.append("%s: unknown verdict %r" % (row.get("label"), verdict))
        elif verdict == "cross" and cited is not None:
            drops.append("%s: a cross cites a line" % row.get("label"))
        elif verdict in ("tick", "confirm") and cited not in resume_lines:
            drops.append("%s: a %s cites no line that exists" % (row.get("label"), verdict))
        else:
            kept.append(row)
    return kept, drops


# --- 3. the told-line gate ------------------------------------------------------------------------

def _stem(word):
    word = word.lower()
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _words(text):
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text)


def told_line_gate(line, said, label):
    """None when the line passes, else why it is refused.

    said: what the person typed or spoke. label: the posting requirement they were asked about."""
    if not 1 <= len(line) <= 400 or not line.rstrip().endswith("."):
        return "shape: 1 to 400 characters ending in a full stop"
    said_numbers = set(NUMBER.findall(said))
    for number in NUMBER.findall(line):
        if number not in said_numbers:
            return "number %s was not said" % number
    allowed = {_stem(w) for w in _words(said) + _words(label)} | JOINING
    for word in _words(line):
        if _stem(word) not in allowed and word.lower() not in allowed:
            return "word %r was not said" % word
    negations = re.compile(r"\b(?:not|never|no)\b", re.I)
    if len(negations.findall(line)) < len(negations.findall(said)):
        return "a negation the person said is missing"
    return None
