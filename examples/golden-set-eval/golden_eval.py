"""A golden-set eval with a noise verdict, reduced from docket's fit eval (standard library only).

docket's fit read takes a job posting's requirement lines and a person's resume, and gives each
requirement a verdict:
  tick     the resume shows it (and cites the resume line)
  confirm  plausible, so the app asks the person
  cross    a gap

The golden set is a list of hand-written "marks": for one requirement line of one posting, the
verdicts the owner accepts. A bundle is a group of marks that must be asked together, in one
question. A run of the model over the postings is a "pass"; its score is "N of M marks met".

A prompt or model change is compared with paired passes: several passes of the control and of the
candidate. The verdict uses a two-level bootstrap (resample the marks, then each arm's passes), so
it accounts both for which marks happen to be in the set and for run-to-run variation. A change
"beats the noise" only when the 95% interval of the delta leaves out 0, and never on one pass.

Usage:
  python3 golden_eval.py data/marks.json data/control.json data/candidate.json
"""
import json
import random
import re
import sys

BOOTS = 4000
SEED = 7


def stems(text):
    """Crude word stems, enough to match a mark's label to a model item's label."""
    return {w[:5] for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


def find_item(page, mark):
    """The model's item for a mark: same posting, the same line (or one either side, since line
    splits can shift), and a label that shares a stem with the mark's."""
    best = None
    for item in page.get(mark["job"], []):
        if abs(item["line"] - mark["line"]) > 1 or not stems(item["label"]) & stems(mark["label"]):
            continue
        if best is None or abs(item["line"] - mark["line"]) < abs(best["line"] - mark["line"]):
            best = item
    return best


def mark_results(marks, page):
    """{mark id: met?}. A bundle's marks are met only when every member is met and all were put in
    the same question group."""
    found = {m["id"]: find_item(page, m) for m in marks}
    met = {m["id"]: bool(found[m["id"]]) and found[m["id"]]["verdict"] in m["expect"] for m in marks}
    bundles = {}
    for m in marks:
        if m.get("bundle"):
            bundles.setdefault(m["bundle"], []).append(m["id"])
    for ids in bundles.values():
        groups = {(found[i] or {}).get("question_group") for i in ids}
        whole = all(met[i] for i in ids) and len(groups) == 1 and None not in groups
        for i in ids:
            met[i] = whole
    return met


def score(marks, page):
    met = mark_results(marks, page)
    return sum(met.values()), len(marks)


def compare(marks, control_passes, candidate_passes, boots=BOOTS, seed=SEED):
    """Paired comparison: delta of mean marks met, with a 95% interval from a two-level bootstrap."""
    ids = [m["id"] for m in marks]
    ctrl = [mark_results(marks, p) for p in control_passes]
    cand = [mark_results(marks, p) for p in candidate_passes]

    def mean_total(passes, units):
        return sum(sum(p[u] for u in units) for p in passes) / len(passes)

    delta = mean_total(cand, ids) - mean_total(ctrl, ids)
    rng = random.Random(seed)
    draws = []
    for _ in range(boots):
        units = [rng.choice(ids) for _ in ids]
        pc = [rng.choice(ctrl) for _ in ctrl]
        pk = [rng.choice(cand) for _ in cand]
        draws.append(mean_total(pk, units) - mean_total(pc, units))
    draws.sort()
    lo, hi = draws[int(0.025 * boots)], draws[int(0.975 * boots) - 1]
    if min(len(ctrl), len(cand)) < 2:
        verdict = "spread unmeasured (one pass on an arm): never beats the noise"
    else:
        verdict = "beats the noise" if (lo > 0 or hi < 0) else "inside the noise"
    return {"delta": delta, "lo": lo, "hi": hi, "verdict": verdict,
            "control": [sum(p.values()) for p in ctrl], "candidate": [sum(p.values()) for p in cand]}


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    marks = json.load(open(argv[1]))["marks"]
    control = json.load(open(argv[2]))["passes"]
    candidate = json.load(open(argv[3]))["passes"]
    for name, passes in (("control", control), ("candidate", candidate)):
        for i, page in enumerate(passes, 1):
            met, total = score(marks, page)
            print("%-9s pass %d: %d of %d marks met" % (name, i, met, total))
    r = compare(marks, control, candidate)
    print("delta %+.2f marks, 95%% interval %+.2f to %+.2f: %s" % (r["delta"], r["lo"], r["hi"], r["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
