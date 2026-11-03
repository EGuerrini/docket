import unittest

from golden_eval import compare, score

MARKS = [
    {"id": "a", "job": "P", "line": 1, "label": "SQL reporting", "expect": ["tick"]},
    {"id": "b", "job": "P", "line": 2, "label": "Payments domain", "expect": ["confirm"], "bundle": "pay"},
    {"id": "c", "job": "P", "line": 3, "label": "Card scheme rules", "expect": ["confirm"], "bundle": "pay"},
]


def page(a="tick", b="confirm", c="confirm", gb="g1", gc="g1", line_a=1):
    return {"P": [
        {"line": line_a, "label": "SQL for reporting", "verdict": a, "question_group": "q"},
        {"line": 2, "label": "Payments domain knowledge", "verdict": b, "question_group": gb},
        {"line": 3, "label": "Card scheme rules", "verdict": c, "question_group": gc},
    ]}


class Score(unittest.TestCase):
    def test_all_met(self):
        self.assertEqual(score(MARKS, page()), (3, 3))

    def test_wrong_verdict_is_not_met(self):
        self.assertEqual(score(MARKS, page(a="cross")), (2, 3))

    def test_a_shifted_line_still_matches(self):
        self.assertEqual(score(MARKS, page(line_a=2)), (3, 3))

    def test_a_bundle_split_over_two_questions_meets_neither(self):
        self.assertEqual(score(MARKS, page(gc="g2")), (1, 3))

    def test_a_missing_item_is_not_met(self):
        self.assertEqual(score(MARKS, {"P": []}), (0, 3))


class Compare(unittest.TestCase):
    def test_identical_arms_are_inside_the_noise(self):
        r = compare(MARKS, [page(), page(a="cross")], [page(), page(a="cross")], boots=500)
        self.assertEqual(r["delta"], 0)
        self.assertEqual(r["verdict"], "inside the noise")

    def test_one_pass_never_beats_the_noise(self):
        r = compare(MARKS, [page(a="cross", b="cross")], [page()], boots=500)
        self.assertIn("never beats", r["verdict"])

    def test_a_consistent_large_gain_beats_the_noise(self):
        # twelve distinct marks, so the bootstrap resamples real marks rather than copies of three
        marks = [{"id": "m%d" % k, "job": "Q", "line": k, "label": "Skill %d" % k, "expect": ["tick"]} for k in range(12)]

        def arm(wrong):
            return {"Q": [{"line": k, "label": "Skill %d" % k, "verdict": "cross" if k < wrong else "tick",
                           "question_group": "g%d" % k} for k in range(12)]}

        r = compare(marks, [arm(6)] * 3, [arm(0)] * 3, boots=500)
        self.assertEqual(r["verdict"], "beats the noise")


if __name__ == "__main__":
    unittest.main()
