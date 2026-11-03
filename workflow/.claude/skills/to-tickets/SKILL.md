---
name: to-tickets
description: Cut a spec into tracer-bullet ticket files under ~/.docket/briefs/<slug>/, each with its blocking edges. Load when a spec is agreed and needs tickets.
---

# To tickets

The ticket format is docs/agents/issue-tracker.md (ticket-format.md in this folder). The dispatcher and the gate
parse those fields, so read it before writing a ticket.

## Slice into tracer bullets
- Each ticket is a **tracer bullet**: a narrow but complete path through every layer it needs, demoable or
  verifiable on its own, and sized for one fresh session.
- A ticket that touches pipeline/schema.sql goes **first and alone**; every ticket that uses it is blocked by it.
- Prefactoring goes first ("make the change easy, then make the easy change").
- A wide refactor (one mechanical change across many call sites) is split into expand, migrate in batches, and
  contract: each batch is its own ticket, blocked by the expand.
- Give each ticket only the `Blocked by:` edges that truly gate it.

## Procedure
1. Read the whole spec: its Flows, Acceptance criteria, Affected areas and Decisions.
2. Draft the breakdown and fill each ticket's fields. `Journeys:` come from the spec's Flows, each step something a
   person can do on screen (fixtures and test hooks go in `Setup:` or `Tests:`). `Files:` and `Tests:` are required.
3. Review the breakdown with the founder as a numbered list (title, blocked by, what it delivers) and adjust the
   granularity, edges and splits until it is approved.
4. Write one file per ticket at ~/.docket/briefs/<slug>/NN-<slug>.md, numbered from 01 in dependency order, with
   `Status: open`. Ticket files are never committed.
