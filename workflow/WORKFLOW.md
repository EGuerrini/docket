# How docket is built with AI coding agents

docket is built by one person with Claude Code. Agent sessions write nearly all of the code; the founder
decides product and tests every feature himself on a phone. In the private repository that came to 2,238 commits
between 2026-09-16 and 2026-10-22. This page describes the system that makes that workable, with a line on why each
rule exists. Examples are paraphrased from the repository's history.

The files under workflow/.claude are addressed to programs: "never" and "refuses" there are instructions to an
agent.

Every rule below is a file in this folder or in the private repo. The ones copied here:

| File | What it does |
| --- | --- |
| [CLAUDE.md](CLAUDE.md) | Loaded into every session: hard rules, product invariants, who decides what, how work runs |
| [.claude/skills/](.claude/skills/) | Procedures, loaded only for the step they cover (build, land, eval, schema-change, ...) |
| [.claude/hooks/guard.py](.claude/hooks/guard.py) | A hook that checks every tool call before it runs and refuses the dangerous ones |
| [.claude/hooks/tests/](.claude/hooks/tests/) | The guard's tests: each refusal seen refusing, each allowed shape seen passing |
| [.claude/lead/models.json](.claude/lead/models.json) | Which model and effort each kind of session gets |
| [ticket-format.md](ticket-format.md) | The ticket file format that the dispatcher and the landing gate parse |

## 1. Plan: spec first, decisions on top

A feature starts as a spec, `docs/features/<name>.md`, written from one template. Open questions go at
the top as decisions, each with options, what each means for the user, and a recommendation. Product
decisions go to the founder, however small; everything else the session decides and records in the
spec's "Decisions" section with the reason.

- **Why:** an agent that guesses at product intent builds the wrong thing quickly. A written decision
  with a reason stops the next session from undoing it.

Decisions that reverse an earlier one get an entry in a numbered log (884 entries by late October; ids are not
contiguous, so the latest is D-1116), never an edit of the old entry. Example: D-972 records why the resume tailor
stopped rewording bullets, with the numbers, what was rejected, and how to reverse it.

- **Why:** the log is how a fresh session learns what was already tried. Without it, agents re-propose
  rejected ideas.

## 2. Split: tracer-bullet tickets with blocking edges

`/to-tickets` cuts a spec into tickets. Each ticket is a narrow path through every layer it needs,
sized for one fresh session, with the files it may touch, the tests it must add, the user journeys a
person can walk, and the tickets that block it. See [ticket-format.md](ticket-format.md).

- A ticket that changes the database schema goes first and alone; every ticket that uses it is blocked
  by it. **Why:** two sessions editing the schema at once produce migrations that do not replay.
- One ticket per spec in flight, and no two in-flight tickets may share a file. Different specs run in
  parallel. **Why:** parallel sessions on the same files produce merge conflicts that cost more than the
  parallelism saves.
- The model for a session is set by the ticket's kind ([models.json](.claude/lead/models.json)): a
  smaller model for trivial and mechanical work, a larger one for builds, and the largest for planning
  and review only, never for building. **Why:** cost and speed follow the work; the planning model's
  value is judgement, and keeping it out of the build keeps its reviews independent.

## 3. Build: every test seen failing first

Each session takes one ticket on its own branch in its own git worktree. Every behaviour change needs a
test that was seen failing on the broken code before the fix. The ticket must quote the failing run;
the landing gate refuses a ticket without one, and `dk verify --red` re-runs the ticket's tests on the
code before the change to prove they fail there.

- **Why:** an agent can easily write a test that passes whatever the code does. A test that was seen
  failing at least shows it can catch the bug.

A bug planted to force a failure is tagged, and a check fails the build if the tag is still there. **Why:** a
planted bug that is never removed is worse than no test.

Example commit subject: *"hotfix-tailor-ask-clock: tailor-ask.check.ts passes its own clock to clearAsk
... (seen red on origin/master ... and in dk land's gate); a test fix, no product change."*

## 4. Check: rules live in code, not in prose

`dk check` runs format, lint, types and a registry of named checks on the changed files in about 5
seconds. Each failure prints a check id; `dk why <id>` prints why the check exists, the past failure it
came from, and how to fix it. The registry had 35 checks in late October.

When a session makes a mistake that a deterministic check could catch, the fix goes in this order of
preference: a check in the registry, a guard case, a gate check, a line in a skill, and last a line in
CLAUDE.md (see the [retro skill](.claude/skills/retro/SKILL.md)).

- **Why:** CLAUDE.md loads into every session, so every line costs context and attention in every
  session. A check runs every time and never gets skimmed.

A process change names the metric it should move and is measured before and after. Example: the guard
used to refuse any command that named the secrets file. The block log showed 68 of 68 such refusals in
two weeks were harmless (a listing, an existence test, a test fixture), so the rule was narrowed to
actual reads, writes and sources, and the narrowed shapes became test cases.

## 5. Review: a gate, AI judges, and the founder's own testing

`dk land <ticket>` is the only way an agent session can reach master. It runs `dk check`, gathers live
evidence for each acceptance line, runs the definition-of-done gate, commits, rebases, pushes as a
fast-forward and watches CI. The guard refuses every other push to master an agent types. It is a hook on
the agent's tools, so it binds agents, not a person at their own terminal.

The gate checks, in code: the full offline check suite; every acceptance line traced to a passing test;
the ticket's own tests run and their earlier failing run quoted. Two model judges also run in the gate. A diff
judge reads the change against the ticket, the spec and the standards, and, when a ticket changes a screen, a
screen judge compares each captured state with its approved design. A third, the journey judge, is planned: it
will walk the ticket's user journeys as a person would, reading nothing else about the feature. **The judges
advise and do not block yet.** A judge gates only once its agreement with the founder's own verdicts is measured
above chance (the same rule the tailor's quality judge had to pass).

- **Why:** the founder found bugs after most landings when the building session alone decided it was
  done. A second reader that has not seen the session's reasoning catches what the author rationalises.
- **Why judges must earn the right to block:** an uncalibrated judge that blocks is a source of noise
  that agents will learn to work around.

The diff judge's findings show up in commit subjects. Examples:
*"dk 05: the diff judge's findings: --red counts a test that did not run on the merge-base as not shown
red"*; *"definition-of-done 03: the live diff judge's four findings fixed ..."*.

A ticket that fails the gate twice stops and is reported; no session works around a check. A failing master is
fixed or reverted before anything else lands.

## 6. Evals: no ship inside the noise

Any change to a prompt, a model or a rubric loads the [eval skill](.claude/skills/eval/SKILL.md). The
rule: every quality delta is reported with its sample size and its run-to-run spread, measured with
paired, repeated passes, and it ships only if it beats the noise. The method is shown in
[examples/golden-set-eval](../examples/golden-set-eval/).

- **Why:** on a 75-mark golden set, run-to-run variation alone is about 2 marks, so a single run of a
  new prompt that scores 1 mark higher says nothing.

Real outcomes from the decision log (paraphrased). Production reads and scoring run on Haiku 4.5; the fit read,
which checks a resume against a posting's requirements, runs on Sonnet 5.5.
- On 2026-10-08 the cheaper Haiku 5.5 was tried as the fit read's model. It scored 48 and 47 of 75 against
  Sonnet 5.5's 52 and 54. The bar, set before the run, was 49 or more of 75 on both passes, within three marks of
  Sonnet, so it was not shipped.
- Later that day five golden-set marks were relabelled, and Sonnet 5.5's baseline became a mean of 57.5 over four
  runs. Against that baseline, medium reasoning effort instead of low scored a mean of 54.75, a looser rule for
  matching the parts of a requirement scored 53.5, and a "the job title decides" prompt scored +1.00 marks with an
  interval of -2.50 to +4.75, inside the noise. None was shipped.
- Rewritten resume bullets lost to the originals in a blind pairwise test (26 wins against 38), so the
  feature was cut back to never rewording a bullet.

These quality evals are run by hand before shipping; CI runs only the harness's self-tests on planted
inputs. Evals do not gate deploys.

## 7. Safety rails for an agent with a shell

- **The guard** ([guard.py](.claude/hooks/guard.py)) runs before every tool call. It refuses reading or
  printing secrets, sending data to a host that is not one of the project's own services, running a
  downloaded script, force pushes, `git add -A`, and any typed push to master. It fails closed: if it
  crashes, the call is refused. **Why:** the threat model is a prompt injection in a web page or a
  posting the agent reads, not the agent's intent.
- **Production writes** go through one tool that refuses to apply without a same-day backup and prints
  the restore command. **Why:** an agent that can write production can also destroy it.
- **Unattended sessions** never ask questions, because nobody is there to answer; they stop with the question and
  a recommendation. **Why:** a session waiting for an answer at 3am burns its context and the night.
- **Spend:** a night of unattended sessions is capped at $20 at list prices, enforced by the
  dispatcher. **Why:** a loop that retries a failing ticket can spend without limit.

## 8. Night sittings

At night the founder starts one coordinating session with `/night <spec>`. It never reads or edits code
itself. It picks from the tickets ready to start, a dispatcher starts one build session per ticket, each
session lands itself through the gate, and the coordinator rewrites a failed ticket's fix notes once
before giving up. It leaves a morning handover: what landed with its commit, what is blocked and why,
and the decisions only the founder can make.

- **Why the coordinator never reads code:** its context is the scarce resource for the whole night;
  every read goes through a subagent that answers in a few lines.

## Skills in this folder

Copied from the private repository: build (with its TDD reference), land, eval, decide, night, to-spec, to-tickets,
schema-change, prod-write and retro. Not copied: the skill for adding a job source (it holds the source policy), the
skills for design boards and handovers, and the generic skills (debugging, grilling, prototyping, codebase design,
writing for agents) that are adapted from [Matt Pocock's public skills](https://github.com/mattpocock/skills).

Paths inside these files (`docs/...`, `scripts/...`, `tools/dk/...`, `~/.docket/...`) name files in the
private repository or on the founder's laptop; they are not in this repository.
