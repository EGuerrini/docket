"""The pipeline side's single source of truth for the fit read: which prompt, which model, which
effort. In docket the pipeline (Python, batch jobs) and the app (TypeScript, live calls) both run the
fit read, so both must send exactly the same request. The app never reads this file; it reads the
JSON that emit.py writes from it."""

VERSION_FILE = "fit_v2"
MODEL = "claude-sonnet-5-5"
EFFORT = "low"
