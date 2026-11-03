"""Run the three grounding checks over the synthetic cases and print what is kept and why the rest
is dropped. python3 demo.py"""
import json
import os

from grounding import check_fit_rows, check_quote, told_line_gate

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "data", "posting.txt"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    with open(os.path.join(HERE, "data", "cases.json"), encoding="utf-8") as f:
        cases = json.load(f)

    print("1. Quotes from the posting")
    for item in cases["quotes"]:
        quote, why = check_quote(item, lines)
        print("   %-26s %s" % (item["label"], ("kept: " + quote) if quote else "dropped: " + why))

    print("2. Fit verdicts cite real resume lines")
    kept, drops = check_fit_rows(cases["fit_rows"], cases["resume_lines"])
    for row in kept:
        print("   %-26s kept: %s%s" % (row["label"], row["verdict"], " cites " + row["line"] if row["line"] else ""))
    for why in drops:
        print("   dropped: " + why)

    print("3. The told-line gate")
    for case in cases["told"]:
        why = told_line_gate(case["line"], case["said"], case["label"])
        print("   %s\n      %s" % (case["line"], "passes" if why is None else "refused: " + why))


if __name__ == "__main__":
    main()
