---
name: eval
description: Measure an AI-quality change (prompt, model, rubric, judge) so it ships only outside the noise. Load before changing a prompt or model and before reporting any quality delta.
---

# An AI-quality change

## Measure before you claim
- Every quality delta is reported with its run-to-run spread and its sample size, and says whether it beats the
  spread. `scripts/fit_noise.py` measures the spread.
- Nothing ships inside the noise. Use paired comparisons and repeated passes, and grow the measure before shipping a
  prompt change.
- The spec's boundary rules for model calls are in docs/spec/llm-boundary.md.

## Rating sheets
- A sheet must count: many jobs and resumes, held out by resume and by job with no shared source line, the split
  fixed before generation, a repeated subset, controls across the scale, and a "Both bad" button.
- Keep new sheets small: at most 30 pairs, and only with the founder's agreement, since he does the rating.

## Testers' resumes, used with their consent
Get explicit consent first. A resume is usable only once names, emails, phones and personal URLs are stripped by a
script that prints counts only. These resumes live in the evals folder outside the repository, never in git.

## Report
The change, the measure (n, spread, delta), whether it beats the noise, the cost, and what you would ship.
