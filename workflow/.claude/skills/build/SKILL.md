---
name: build
description: Build a ticket or a hotfix test-first, from reading the ticket to the session report. Load at the start of every build ticket or production fix.
---

# Build a ticket

A ticket is a file, ~/.docket/briefs/<spec>/NN-<slug>.md (format: docs/agents/issue-tracker.md), or a message from
the founder. One session takes it on its own branch and worktree, through to master.

## 1. Understand
- Read the ticket, then the spec sections its `Spec:` line names. Read the rest only when needed.
- A design question (product, schema, a new flow) gets a plan first: the decisions on top, each with a
  recommendation, put to the founder before any code. Product questions go to the founder, however small.
- Touching schema.sql: load `schema-change`. A production write: `prod-write`. An AI-quality change: `eval`. The
  private repository also has skills for job sources, visual changes and debugging, which are not copied here.

## 2. Test first
Each behaviour change gets a test seen failing on the broken input, then passing. Paste each failing run into the
ticket's `Seen red:` field (each title in `Tests:` must appear in it). The loop and its rules are in [tdd.md](tdd.md).

## 3. Check often
`tools/dk/dk check` runs format, lint, types and the check registry on the changed files. It prints a check id and a
fix message for each failure; `tools/dk/dk why <id>` says why the check exists. Run your own Playwright specs when
the UI changed.

## 4. Document in the same commit
- SPEC (docs/spec/) when behaviour changes; ARCHITECTURE when a boundary, table, workflow or invariant changes;
  design/system/ when a look or behaviour rule changes.
- Decisions go in the feature's docs/features/<name>.md under "Decisions". One that reverses a standing entry in the
  decision log: load `decide`.
- docs/BACKLOG.md: a new spec adds its line, a shipped one moves it to docs/backlog-archive.md. Work you defer goes
  into the spec's tickets or docs/backlog-later.md under its own heading.

## 5. Land
Load `land`.

## 6. Report
Plain English, the user-visible change first, every count as x of y, every claim of state read back from its source:
1. What changed for the user.
2. The tests seen failing, each with its failure.
3. What was deferred, and where it went.
4. How to undo.

## Unattended (dispatched or at night)
Nobody answers questions, so never stop to ask one. Put the question and a recommendation in the report. If the
session must stop with work left, add a `Resume:` section under the ticket's `Status:` line: the branch, the last
passing state, what is left and the next step. Push the branch first.

## A production fix
A reported live failure stops the plan. Open `hotfix-<what>` from origin/master in its own worktree, then:
1. Read-only: list the affected rows; change nothing.
2. Make the minimal fix, with a comment.
3. See the test fail first on CI's Postgres service, then add a check so the class of bug cannot recur.
4. Check and land, confirm a scheduled run passes, and report the master sha and run id, read back.
Then resume the plan with the failure's class added to its scope.
