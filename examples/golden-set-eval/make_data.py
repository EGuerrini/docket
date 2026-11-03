"""Writes data/control.json and data/candidate.json: simulated model passes over the synthetic marks.

No model is called. Each pass gives every mark the right verdict with some probability, so the
passes vary the way real runs do. The candidate is slightly better than the control on average, by
less than the noise: the point of the example is that a small gain on a small set does not ship.
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
WRONG = {"tick": "confirm", "confirm": "cross", "cross": "confirm"}


def simulate(marks, p_right, rng):
    page = {}
    for m in marks:
        right = rng.random() < p_right
        verdict = m["expect"][0] if right else WRONG[m["expect"][0]]
        group = m.get("bundle") if (m.get("bundle") and rng.random() < 0.8) else "q-" + m["id"]
        page.setdefault(m["job"], []).append(
            {"line": m["line"], "label": m["label"], "verdict": verdict, "question_group": group})
    return page


def main():
    marks = json.load(open(os.path.join(HERE, "data", "marks.json")))["marks"]
    rng = random.Random(2026)
    for name, p_right in (("control", 0.74), ("candidate", 0.78)):
        passes = [simulate(marks, p_right, rng) for _ in range(4)]
        with open(os.path.join(HERE, "data", name + ".json"), "w") as f:
            json.dump({"about": "Simulated passes, synthetic (make_data.py).", "passes": passes}, f, indent=1)
            f.write("\n")


if __name__ == "__main__":
    main()
