import unittest

from grounding import check_fit_rows, check_quote, told_line_gate

LONG = ("Comfortable running workshops with operations managers, finance and the engineering team to agree on "
        "definitions, priorities and the order in which reports and data products are delivered over the year.")
LINES = ["Strong SQL for reporting.", LONG, "Contact [email removed]."]


class Quote(unittest.TestCase):
    def test_a_short_line_is_quoted_whole(self):
        self.assertEqual(check_quote({"line": 1}, LINES), ("Strong SQL for reporting.", None))

    def test_a_span_inside_a_long_line_is_kept(self):
        span = "running workshops with operations managers"
        self.assertEqual(check_quote({"line": 2, "span": span}, LINES), (span, None))

    def test_a_paraphrased_span_is_dropped(self):
        self.assertEqual(check_quote({"line": 2, "span": "running workshops with stakeholders"}, LINES),
                         (None, "span not in its line"))

    def test_a_span_over_25_words_is_dropped(self):
        span = " ".join(LONG.split()[:26])
        self.assertEqual(check_quote({"line": 2, "span": span}, LINES), (None, "span over 25 words"))

    def test_a_line_that_does_not_exist_is_dropped(self):
        self.assertEqual(check_quote({"line": 9}, LINES), (None, "line out of range"))

    def test_a_quote_holding_a_removal_is_dropped(self):
        self.assertEqual(check_quote({"line": 3}, LINES), (None, "quote carries a removal"))


class FitRows(unittest.TestCase):
    RESUME = {"r1": "Built SQL reporting."}

    def test_a_tick_citing_a_real_line_is_kept(self):
        kept, drops = check_fit_rows([{"label": "SQL", "verdict": "tick", "line": "r1"}], self.RESUME)
        self.assertEqual((len(kept), drops), (1, []))

    def test_a_tick_citing_a_missing_line_is_dropped(self):
        kept, drops = check_fit_rows([{"label": "German", "verdict": "tick", "line": "r9"}], self.RESUME)
        self.assertEqual(kept, [])
        self.assertEqual(drops, ["German: a tick cites no line that exists"])

    def test_a_cross_cites_no_line(self):
        kept, drops = check_fit_rows([{"label": "German", "verdict": "cross", "line": "r1"}], self.RESUME)
        self.assertEqual(drops, ["German: a cross cites a line"])


class ToldLineGate(unittest.TestCase):
    SAID = "I ran monthly workshops with finance to agree report definitions"
    LABEL = "workshops with stakeholders"

    def test_the_persons_own_words_pass(self):
        self.assertIsNone(told_line_gate("Ran monthly workshops with finance to agree report definitions.",
                                         self.SAID, self.LABEL))

    def test_the_labels_words_may_be_added(self):
        self.assertIsNone(told_line_gate("Ran monthly workshops with finance stakeholders.", self.SAID, self.LABEL))

    def test_an_invented_number_is_refused(self):
        self.assertEqual(told_line_gate("Ran 12 monthly workshops with finance.", self.SAID, self.LABEL),
                         "number 12 was not said")

    def test_an_invented_word_is_refused(self):
        self.assertEqual(told_line_gate("Led monthly workshops with finance.", self.SAID, self.LABEL),
                         "word 'Led' was not said")

    def test_a_dropped_negation_is_refused(self):
        self.assertEqual(told_line_gate("Used dbt and plain SQL.", "I have not used dbt, only plain SQL", "dbt"),
                         "a negation the person said is missing")

    def test_a_line_without_a_full_stop_is_refused(self):
        self.assertIn("shape", told_line_gate("Ran workshops with finance", self.SAID, self.LABEL))


if __name__ == "__main__":
    unittest.main()
