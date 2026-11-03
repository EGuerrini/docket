import json
import os
import shutil
import tempfile
import unittest

import emit


class Drift(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.target = os.path.join(self.dir, "fit_prompt.json")
        with open(self.target, "w", encoding="utf-8") as f:
            f.write(emit.build())

    def tearDown(self):
        shutil.rmtree(self.dir)

    def edit(self, **fields):
        doc = json.load(open(self.target, encoding="utf-8"))
        doc.update(fields)
        with open(self.target, "w", encoding="utf-8") as f:
            f.write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    def test_freshly_emitted_is_in_sync(self):
        self.assertIsNone(emit.check(self.target))

    def test_the_committed_copy_is_in_sync(self):
        self.assertIsNone(emit.check())

    def test_a_hand_edited_model_is_drift(self):
        self.edit(model="claude-haiku-5-5")
        self.assertIn("model", emit.check(self.target))

    def test_a_hand_edited_prompt_is_drift(self):
        self.edit(system="You are helpful.")
        self.assertIn("system", emit.check(self.target))

    def test_whitespace_alone_is_drift(self):
        with open(self.target, "a", encoding="utf-8") as f:
            f.write(" ")
        self.assertIn("formatting", emit.check(self.target))

    def test_a_missing_file_is_drift(self):
        os.remove(self.target)
        self.assertIn("missing", emit.check(self.target))


if __name__ == "__main__":
    unittest.main()
