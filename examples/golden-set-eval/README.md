# Golden-set eval with a noise verdict

A reduced version of the harness docket uses to decide whether a prompt or model change to the fit
read ships. Standard library only, no model calls, synthetic data.

```
python3 make_data.py          # regenerate the simulated passes (seeded)
python3 golden_eval.py data/marks.json data/control.json data/candidate.json
python3 -m unittest -v test_golden_eval
```

## The golden set

`data/marks.json` holds marks. A mark names one requirement line of one posting and the verdicts the
owner accepts for it:

```json
{"id": "m06", "job": "P2", "line": 2, "label": "Payments domain knowledge",
 "expect": ["confirm"], "bundle": "payments"}
```

- `tick`: the resume shows it; `confirm`: plausible, so ask the person; `cross`: a gap.
- A **bundle** is a set of marks that must be asked as one question. A bundle split across two
  questions meets none of its marks, because two questions about the same thing waste the person's
  time.
- The model's item for a mark is found by posting, line (one line of slack, since line splits shift)
  and a shared label stem.

In docket the set is 75 marks hand-written by the owner over real postings and fictional resumes.
Here it is 15 marks over three invented postings.

## The noise verdict

A pass is one run of the model over the set. A change is measured as paired passes: several of the
control, several of the candidate. `compare()` reports the delta in mean marks met and a 95% percentile
interval from a two-level bootstrap: resample the marks, then resample each arm's passes. The first
level covers "which marks happen to be in the set", the second covers run-to-run variation. With four
passes an arm, the second level has only four values to draw from, so treat the interval as a guard
against shipping noise, not as a precise error bar.

- **Beats the noise**: the interval leaves out 0.
- **Inside the noise**: it does not. Not shipped.
- **One pass on an arm**: the spread is unmeasured, so it never beats the noise.

The sample output shows why this matters. `make_data.py` makes the candidate better by construction
(right on 78% of marks against 74%), yet with 15 marks and 4 passes this run measures it 1.5 marks
*worse*, and the interval (-5.00 to +1.75) correctly says the set cannot tell them apart:

```
control   pass 1: 12 of 15 marks met
...
candidate pass 4: 11 of 15 marks met
delta -1.50 marks, 95% interval -5.00 to +1.75: inside the noise
```

On docket's 75 marks, the recorded scale is that a change must move about 4 to 5 marks before it
stands out (run-to-run alone is about 2).
