# Test first: the reference

The loop of a failing test, then the code that makes it pass, and what makes those tests worth keeping. Consult it
before and during the loop, not after.

Use the words SPEC.md and docs/spec/ use for test names and interfaces, and respect the decisions in the area
(docs/decisions/INDEX.md, the feature's "Decisions").

## What a good test is

Tests verify behaviour through public interfaces, not implementation details. Code can change entirely; tests
shouldn't. A good test reads like a specification: "the strip shows four thumbnails" says what exists, and it
survives refactors because it does not care about internal structure.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behaviour without reaching inside.
Tests live at seams, never against internals.

Write down the seams under test before the first test, with a one-line note each on what it catches and what it
misses. The ticket's `Tests:` lines name them; a seam the ticket does not name is a choice you state in the report.
When the shape of the interface is itself in question, settle the module and its interface before writing tests.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel
  (querying the database instead of the interface). The tell: it breaks on a refactor that kept behaviour.
- **Tautological**: the assertion recomputes the expected value the way the code does, so it passes by construction.
  Expected values come from an independent source: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: all tests first, then all code. Work in vertical slices: one test, one implementation,
  repeat, each test answering what the last cycle taught you.

## Rules of the loop

- **Failing before passing.** Write the test, run it, see it fail on the broken input, then write only enough code to
  pass it. Paste the failing run into the ticket's `Seen red:` field; the gate refuses a ticket without it.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Clean up a planted bug.** If you forced the failure by changing code or a fixture, tag the change
  `// TEMP mutation`, copy the file to the scratchpad first, revert by edit, and grep for `TEMP mutation` before the
  next build. A check fails the build if the tag is still there.
- **Refactor after the test passes**, in its own step, with the tests still passing.
