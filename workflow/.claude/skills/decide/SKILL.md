---
name: decide
description: Append one decision entry to docs/decisions/ and regenerate the index. Use when a decision reverses or changes a standing one; a feature's other decisions go in its docs/features/<name>.md "Decisions" section instead.
---

# /decide <the decision in one sentence>

The log is one file per area under docs/decisions/ (DECISIONS.md lists the areas), one global sequence of ids, and
docs/decisions/INDEX.md generated from the area files. An entry is never edited; reversing one appends a new entry
and sets the old one's Status to "Superseded by D-NNN".

1. Search docs/decisions/INDEX.md for the topic and read the matching entries. If a standing entry already says
   this, stop and say so. If one contradicts it, this entry supersedes it.
2. Take the next free id, after rebasing on origin/master.
3. The why, what was rejected and how reversible it is come from the person who made the decision or from the
   ticket; "Nothing recorded" is an honest answer. Append to the area file that fits:

```
### D-NNN · YYYY-MM-DD · <Title, five to ten words>
**Decision.** One sentence.
**Why.** One to three sentences.
**Rejected.** One line each, or "Nothing recorded".
**Reversibility.** Easy | Costly | Hard, plus what reversing would take.
**Status.** Standing | Superseded by D-NNN | Parked (un-parked by: <trigger>)
```

4. Run `python scripts/decisions_index.py`, then `python scripts/decisions_index.py --check`.
5. If it changes behaviour, change SPEC (docs/spec/) in the same push; if it changes a boundary or invariant,
   ARCHITECTURE. Commit by path: `decide: D-NNN <title>`.
