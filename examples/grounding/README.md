# Grounding checks: the model proposes, code verifies

Three checks from docket, reduced to their core. Standard library only, synthetic data (an invented
posting and resume, with planted errors).

```
python3 demo.py
python3 -m unittest -v test_grounding
```

None of them repairs what fails. A dropped item is counted with its reason, so a prompt that starts
producing more drops shows up in the numbers.

## 1. Quotes from a posting (`check_quote`)

Every requirement docket shows comes with a quote from the original posting, so the person can check
it. The model cites a line number; code copies the line. A line of at most 25 words is quoted whole,
so it is verbatim by construction. A longer line needs a span, and the span must sit inside the line
exactly. A quote holding a personal-data removal marker is dropped (docket strips emails, phones,
personal links and contact names before the model reads a posting).

```
SQL reporting              kept: Strong SQL and experience building reporting for non-technical stakeholders.
Workshops                  kept: running workshops with operations managers, finance and the engineering team
Workshops (paraphrased)    dropped: span not in its line
Workshops (too long)       dropped: span over 25 words
Contact                    dropped: quote carries a removal
Invented line              dropped: line out of range
```

## 2. Fit verdicts cite real resume lines (`check_fit_rows`)

The fit read gives each requirement `tick` (shown), `confirm` (ask the person) or `cross` (a gap). A
tick or confirm must cite a resume line that exists; a cross cites none. Code guarantees the citation
is real. Whether the line truly supports the claim is the model's judgement, and that is what the
golden-set eval measures.

```
dropped: German or French: a tick cites no line that exists
```

## 3. The told-line gate (`told_line_gate`)

When a person answers a question ("Have you run workshops?") in their own words, a model turns the
answer into one resume line. The gate refuses the line unless every number in it is one the person
said, and every word is theirs, the requirement label's, or a joining word. A refused line falls back
to the person's own words. It does not try to judge whether an invented fact is plausible; it refuses
anything the person did not say.

```
Ran 12 monthly workshops with finance to agree report definitions.
   refused: number 12 was not said
Led monthly workshops with finance and engineering leadership.
   refused: word 'Led' was not said
Used dbt and plain SQL.
   refused: a negation the person said is missing
```

docket's version also handles tenses and plurals more carefully, spoken numbers ("twelve"), names and
acronyms, and checks which word a negation applies to. This one stems crudely and counts negations.
