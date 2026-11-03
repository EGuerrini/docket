---
name: schema-change
description: Change the database schema (pipeline/schema.sql) so it replays safely and the app still runs on the previous version. Load before editing schema.sql or creating any schema object.
---

# A schema change

1. **Ask the semantics first.** Before creating a table, column or constraint, ask what it means (who writes it,
   what null means, what a row stands for). A plain yes, without those answers, is not enough to create a column.
2. **schema.sql is replayed on every run.** So:
   - add a constraint once, by name, behind a `pg_constraint` lookup;
   - change one by a new name, or by a DROP guarded on the old definition;
   - no drop-and-re-add, no unguarded data statement.
3. **Lint.** `python pipeline/schema_replay.py --lint` stays at 0.
4. **Bump the version.** Every edit bumps `-- schema_version: N` (CI's schema version gate refuses a changed file
   with the old number).
5. **The previous schema still runs the app.** Vercel deploys before the scheduled migrate, so the app must work
   on the schema before your change (CI: "the app on the previous schema").
6. **One at a time.** One session edits schema.sql at a time. A ticket that touches it lands first and alone; the
   tickets that use it are blocked by it.
7. **Production.** The migrate is a production write: load `prod-write` (backup named before the migrate).

Before you land: `python pipeline/schema_replay.py --lint`, then `tools/dk/dk check`. The replay itself and the
previous-schema check run in CI against its Postgres service.
