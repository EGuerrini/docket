---
name: to-spec
description: Turn the current conversation into a feature spec at docs/features/<slug>.md, decisions on top. Load when a design question or a new feature needs a spec before tickets.
---

# To spec

Write docs/features/<slug>.md from docs/features/TEMPLATE.md, using what the conversation and the code already say
rather than interviewing anyone. First read the code the feature touches and the spec and decision-log entries in
its area, and use their words. Each numbered acceptance criterion must be testable by a person on a phone or by a
test, and the spec names as few test seams as it can, ideally one. Open questions go at the top as decisions, each
with its options, what each means for the user and a recommendation; product questions go to the founder, and the
session decides the rest and records the reason. Keep file paths and code out of the body, since they go stale.
Add the spec's line to docs/BACKLOG.md, run `tools/dk/dk check`, and hand over to `to-tickets`.
