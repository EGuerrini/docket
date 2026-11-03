---
name: prod-write
description: Write to production data safely (backup first, restore stated, read back). Load before any write to the production database, and before running a script that needs secrets.
---

# A production write

Before any write to production, back up the tables you will change and say how to restore them.

1. **Go through the tool.** `pipeline/prod_writes.py` does the backup in code: a dry run first, the day's backup
   run, the rows saved, the restore stated. It refuses `--apply` without a same-day backup. Do not write production
   any other way.
2. **Secrets.** They live in .env (never read it), GitHub secrets and Vercel env. Run a script that needs them
   through the credentials wrapper, `.claude/lead/run_with_env.py`. Never print a secret or the environment.
3. **Read through the read-only door.** Read the corpus and any rows through `pipeline/readonly.py query`.
4. **A real user's rows** (votes, scores, profile, record) are never changed while debugging. Reproduce, report,
   and wait for the founder's approval with the values spelled out. The approval covers exactly those values.
5. **Read back after.** Read the changed rows back from production and quote them in the report, with the backup's
   name and the restore command.

The report says what was written (table, rows, values), the backup and how to restore it, and the read-back.
