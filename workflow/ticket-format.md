<!-- Public copy of docket's ticket format (docs/agents/issue-tracker.md in the private repository), edited for readers outside the project. Paths name files in the private repository. -->

# Ticket format

docket keeps its specs and tickets as plain files rather than in an issue tracker.

- **Specs** (written with `/to-spec`): docs/features/<feature-slug>.md, from docs/features/TEMPLATE.md, committed
  with the first build.
- **Tickets** (cut with `/to-tickets`): one file per ticket at ~/.docket/briefs/<feature-slug>/<NN>-<slug>.md,
  numbered from 01 and never committed. The dispatcher starts a session on a ticket with
  `dispatch.py <feature> --pick NN`, and the session lands it with `tools/dk/dk land <path>`, whose
  definition-of-done gate (scripts/dod.py) reads the fields below.
- **Backlog**: docs/BACKLOG.md lists the specs by product area, one line each. Work that is not a spec yet is in
  docs/backlog-later.md, and a spec that ships moves its line to docs/backlog-archive.md.

## A ticket's fields
One field per line, `Name: value`; a value runs until the next field or a blank line (a ``` fence keeps its blank
lines).

~~~
# <feature> NN: <title>
Status: open
Blocked by: none
Kind: build. Spec: docs/features/<feature>.md ("<section>", "<section>").

What to build: the behaviour, from the user's side.

Journeys:
1. Pick a template.
   - Open a job's Tailor page; tap Export. -> The details step shows, Phone empty, the switch off.
   - Tap Continue. -> The strip shows four thumbnails; Classic first.
States: asking, ready
Files: app/src/lib/x.ts, app/tests/x.spec.ts
Setup: <the fixture script> (a test account), or none
Tests:
- app/tests/x.spec.ts::the strip shows four thumbnails
- scripts/tests/test_x.py::test_refuses_a_bad_row
Seen red:
```
  [FAIL] the strip shows four thumbnails
FAIL: test_refuses_a_bad_row (test_x.X)
```

- [ ] acceptance line
~~~

- `Status:` one of open; claimed (by which session, and when); red (failed the gate, with the gate's findings below
  it); failed (stopped without landing, or failed the gate twice); done; landed (the dispatcher treats it as done).
  A ticket closed by hand says "done by hand".
- `Blocked by:` the numbers of the tickets that must be done first, or none.
- `Kind:` trivial, mechanical, build, design or deep. It picks the session's model and effort
  (.claude/lead/models.json). A design ticket gets a plan first and then builds, on the build model; a deep ticket
  is planning and review only, because the planning model never builds. The same line names the spec and its
  sections, and the gate finds the feature's acceptance trace (evals/<feature>/trace.json) from the spec's name.
- `Journeys:` what a person does to use the change, one journey per entry point: its name, then each step as a tap
  and, after `->`, what must then be true on screen. The journey judge, still to be built, will walk these and read
  nothing else about the feature. Write `none (why)` when nothing on a screen changes (a script, a schema change, a
  pipeline change). `/to-tickets` writes them from the spec's Flows and Acceptance criteria.
- `States:` the rows of the spec's States table that the ticket builds, by name. The screen judge compares each
  state's capture with its approved design and the spec's copy. If the field is missing, naming the spec's "States"
  section covers every row; if it says `none`, or neither is given, the screen judge is skipped.
- `Setup:` the fixture script a journey needs (a scored deck, a saved resume), run as a dedicated test account and
  reset afterwards; or none.
- `Files:` what the diff may touch. The diff judge treats a change outside this list as beyond the ticket.
- `Tests:` the ticket's own tests, one `<file>::<title>` per line, as in the trace. The gate runs each one and reads
  the runner's own report; a test the runner never reported did not run, and counts as a failure. Tests that need
  Postgres run in CI: `dk land` pushes the branch, and the gate reads their results from the CI run of the ticket's
  commit.
- `Seen red:` the failing run of each test in `Tests:`, quoted by the session (each title must appear in it).
  Without it the gate refuses with "no red run quoted".

## When a skill says "publish to the issue tracker"
Write the file above, creating the directory if needed.

## When a skill says "fetch the relevant ticket"
Read the file at the path given.
