---
name: retro
description: "Conduct a retrospective on a coding session."
disable-model-invocation: true
---

The user has asked for a **retrospective**. You are suggesting improvements to the agents' **environment** so the
next sessions go better.

## Steps

1. Write for agents: short, concrete instructions, each with the reason it exists.
2. Read the primary sources for the session the user names: its transcript under ~/.claude/projects/, its branch,
   its verdict (~/.docket/dod/<branch>.json), its report. If no session is named, use the current one.
3. Look for candidates in these categories:
   - **Navigation**: did the agent struggle to find a file or a fact? Would a pointer in CLAUDE.md or in a skill
     have saved it?
   - **Automated checks**: did the agent make a mistake a deterministic check could catch? Read the existing checks
     first (tools/dk/checks.yaml, scripts/check.py, .github/workflows/), so that a check that exists but is unwired
     or broken is the finding, not a reinvention. A mechanical violation (a pattern, a banned API, a file location,
     an invariant) gets a check, never a rule in prose.
   - **Friction**: did a check or the guard block legitimate work? `tools/dk/dk why --week` lists the blocks; a
     check whose blocks were all worked around is a candidate to demote or narrow.
   - **No-ops**: instructions that change no behaviour.
   - **Tool economy**: expensive tool calls that a command or a narrower read would replace.
   - **Information access**: a fact the agent needed and could not reach (a log, a run, a read-only query).
4. For each candidate, say where the fix goes, in this order of preference:
   1. a check in the registry (tools/dk/checks.yaml, run by `dk check`), with its origin (this session) and a
      test built from the real violation;
   2. a guard case in .claude/hooks/guard.py, with its cases added to .claude/hooks/tests/test_guards.py first and
      seen failing;
   3. a gate check in scripts/dod.py;
   4. a line in the skill that holds that procedure;
   5. a line in CLAUDE.md, as a last resort, because it loads into every session.
5. Present the candidates to the user, in order of severity, each with its fix location and a recommendation.
   Anything that loosens the security or compliance posture is the founder's decision.

## Reference

- CLAUDE.md is loaded into every agent's context. Use it sparingly: what docket is, the invariants, judgment lines,
  pointers.
- Skills hold procedures; their one-line description is always loaded, their body only when needed.
- Docs are reference files, pointed to by CLAUDE.md or a skill. Look for an existing doc before writing a new one.
