---
name: night
description: Run the night sitting - land one spec's tickets through the gate, ticket by ticket, and leave the founder a morning handover.
disable-model-invocation: true
argument-hint: "<spec slug>"
---

# The night sitting

You coordinate one unattended night. Your goal is to land the tickets in ~/.docket/briefs/<slug> one by one,
through the gate, and leave the founder a morning handover. Nobody is watching and nobody answers questions until
morning.

## What you do and never do
- You pick tickets and rewrite the fix notes of failed ones. Build sessions do the work: each ticket is one session,
  started by the dispatcher (`.claude/lead/dispatch.py`), that builds, runs `tools/dk/dk land` and lands itself.
- You never edit code, read a diff, or open a file under app/, pipeline/ or scripts/ yourself. Every read (a verdict,
  a log, a run, a spec section) goes through a subagent that answers in a few lines. The ticket files under
  ~/.docket/briefs/<slug>/ are the only files you read and write directly. Your context has to last the night.
- Brief subagents by pointer (a path, a commit, a run id), never by pasting what a file holds.
- Improvements to the environment that you notice (a missing check, a vague ticket line) go into the handover as
  recommendations, not into the repository.
- One ticket of the spec is in flight at a time, and the dispatcher refuses a ticket that shares a file with one in
  flight. A ticket that fails the gate gets its fix notes rewritten by a subagent and one restart; a second failure
  ends the night.

## When you stop
Stop at the first of these:
- no ticket is left that can be started;
- a ticket failed (a second failure at the gate, or a session that stopped without landing);
- the next pick needs a decision only the founder makes (CLAUDE.md, "Who decides");
- your context passes 150k tokens;
- the night's $20 cap at list prices, counting this session, its subagents, the sessions it started and the judges'
  recorded costs. The dispatcher refuses a pick once the cap is reached; treat that refusal as a stop.

Then write the handover to ~/.docket/briefs/<slug>/handover-<date>.md, in plain English with every count as x of y:
1. **Landed**: each ticket with its master commit and its gate verdict.
2. **Blocked**: each ticket not landed and why (failed, with its fix notes; waiting on another ticket or a decision;
   or still running, with its session's name). A session still in flight keeps running.
3. **Decisions waiting**: each with the options, what each means for the user, your recommendation, and what waits
   on it.
Then the night's spend, your recommendations for the environment, and the output of `tools/dk/dk why --week` (the
checks that blocked work this week). End the sitting with `python3 .claude/lead/dispatch.py <slug> --sitting end`.
