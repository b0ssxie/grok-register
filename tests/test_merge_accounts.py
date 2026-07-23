import os
import tempfile
import unittest

from account_outputs import merge_account_files


class MergeAccountTests(unittest.TestCase):
    def test_merges_deduplicates_and_writes_output(self):
        with tempfile.TemporaryDirectory() as d:
            f1 = os.path.join(d, "a.txt")
            f2 = os.path.join(d, "b.txt")
            out = os.path.join(d, "merged.txt")
            with open(f1, "w") as h:
                h.write("a@x.com----pw1----tok1\n")
                h.write("b@x.com----pw2----tok2\n")
            with open(f2, "w") as h:
                h.write("b@x.com----pw2----tok2\n")
                h.write("c@x.com----pw3----tok3\n")
            r = merge_account_files([f1, f2], output=out)
            self.assertEqual(r["total"], 4)
            self.assertEqual(r["unique"], 3)
            self.assertEqual(r["duplicates_skipped"], 1)
            with open(out) as h:
                lines = h.read().splitlines()
            self.assertEqual(len(lines), 3)
            self.assertIn("a@x.com----pw1----tok1", lines)
            self.assertIn("b@x.com----pw2----tok2", lines)
            self.assertIn("c@x.com----pw3----tok3", lines)
            self.assertTrue(os.path.exists(r["output"]))

    def test_merge_no_output_returns_summary_only(self):
        with tempfile.TemporaryDirectory() as d:
            f1 = os.path.join(d, "a.txt")
            with open(f1, "w") as h:
                h.write("a@x.com----pw1----tok1\n")
            r = merge_account_files([f1])
            self.assertEqual(r["total"], 1)
            self.assertEqual(r["unique"], 1)
            self.assertIsNone(r["output"])

    def test_merge_nonexistent_file_raises(self):
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "no.txt")
            with self.assertRaises(FileNotFoundError):
                merge_account_files([fake])


if __name__ == "__main__":
    unittest.main()
