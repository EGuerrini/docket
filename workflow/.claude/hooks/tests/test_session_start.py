"""The SessionStart text: pure compose(), a few short lines, no roles. Offline."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import session_start  # noqa: E402


class Compose(unittest.TestCase):
    def test_master_says_branch_first(self):
        text = "\n".join(session_start.compose("/main", "master", "0", 2))
        self.assertIn("make a branch", text)
        self.assertIn("Uncommitted changes: 2 files", text)

    def test_a_branch_behind_master_is_told(self):
        text = "\n".join(session_start.compose("/wt", "x", "3", 0))
        self.assertIn("3 commits behind", text)
        self.assertNotIn("Uncommitted", text)

    def test_the_guard_line_is_the_guards_own_list(self):
        """The line once said "only" and missed the landing rule, so it is now built from the guard's own list."""
        import guard
        text = "\n".join(session_start.compose("/wt", "x", "0", 0))
        for phrase in guard.REFUSES:
            self.assertIn(phrase, text)
        self.assertIn("dk land", text)

    def test_short(self):
        self.assertLess(len("\n".join(session_start.compose("/wt", "x", "3", 4))), 500)


if __name__ == "__main__":
    unittest.main()
