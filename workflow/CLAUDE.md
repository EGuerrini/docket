# docket: instructions for every agent session

This is the instruction file that every agent session in docket's private repository loads when it starts.
Paths refer to that repository. Checks live in code and procedures live in skills; this file holds only what neither can.

docket is a job-search app. The app is TypeScript on TanStack Start, deployed on Vercel; the pipeline that feeds it
is Python on GitHub Actions; a Supabase Postgres database sits between them.

## Hard rules
1. Reading the outside web is fine for research and documentation. Nothing of the project's is sent to a host that is
   not one of its own services (Supabase, GitHub, Anthropic, Resend, Vercel), and nothing downloaded is run before it
   is read. The product's own reading of job boards and employer sites runs only on GitHub's servers.
2. The product reads only public job feeds and respects each source's robots.txt and terms of service. A new source,
   or a new way of reading one, needs the founder's sign-off with its robots.txt verdict and terms in front of him.
3. Every request the product makes identifies itself as the product's bot, never as a browser or a person.
4. Before any write to production, back up the tables you will change and state how to restore them. No backup, no write.
5. No posting's full text is kept after it is read. Only the extract is stored: the facts, the requirements and tasks
   each with its verbatim line of at most 25 words, summaries in our own words, tags, the link and a hash of the text.
6. Personal data in a posting (emails, phone numbers, personal URLs, contact names) is never stored. Code strips it
   before a model reads the text and refuses any extract that still contains it.
7. Risks go to the founder as decisions, never filed as housekeeping.
8. Nothing that loosens the security or compliance posture is chosen without asking the founder.

The private copy keeps retired rule numbers because checks cite them.

## Product invariants
- No auto-apply and no auto-send, ever: a person approves every outbound action.
- Votes are training data. Scoring changes one variable at a time, and every scoring change can be replayed offline.
- Grounded claims only: verbatim evidence, quotes of at most 25 words, and a link to the original.
- The product works for the candidate, never as the candidate, and never evaluates people for employers.
- Model text reaches a person's resume only when they ask, and never adds a fact they did not give.

## Who decides
The founder decides product questions however small, the legal posture (sources, robots.txt, terms, privacy text),
spending above the caps, anything that touches a real user's data, and the hard rules. Put such a question in plain
English: the options, what each means for the user, a recommendation, and what happens if nobody answers today. The
session decides everything else and records it, with the reason, in the feature's doc under "Decisions".
Before spending more than $20 in one run or one day, say what it is for, how much, and why nothing cheaper will do,
then go ahead unless told to stop. Above $60 in a day, wait for approval. An unattended night is capped at $20.

## Judgment
- Never lower a testing standard to land. Each behaviour change gets a test seen failing first, then passing.
- A process change names the metric it should move and is measured before and after. Remove a rule before adding one.
- Ask what a schema object means before creating it, and never invent a target number.
- Report in plain English, the user-visible change first, every count as x of y. Read each claim about the state of
  a run, git or production back from its source before making it.
- Fix quietly what carries no risk (a lint miss, a stale run). Anything that could hurt a user, the data, money or
  the legal posture is raised as a decision.
- Every performance claim carries its number and where it was measured.
- A visual change starts from captures of the real app that the founder has approved.
- The planning model plans and reviews; it never builds (.claude/lead/models.json).
- An unattended session does not wait on a question. It stops with the question and a recommendation.

## How work runs
- Each change is a ticket file (the format is in ticket-format.md).
- One agent takes one ticket on its own branch in its own git worktree.
- `tools/dk/dk check` runs format, lint, types and the check registry on what changed. Run it often.
- `tools/dk/dk land <ticket>` is the only way onto master. It runs the checks, gathers live evidence for each
  acceptance line, runs the definition-of-done gate, pushes and watches CI. A failing master is fixed or reverted first.
- Tests write only as dedicated test accounts, never as a real user.

## Skills
- build: build a ticket or a production fix test-first, from reading the ticket to the report.
- land: land a finished ticket through `dk land`, and handle a failing gate or a failing master.
- eval: measure a prompt, model or rubric change so it ships only when it beats the noise.
- schema-change: change the schema so it replays safely and the app still runs on the previous version.
- prod-write: write production data with a backup first, a stated restore and a read-back.
- decide: add an entry to the decision log when a decision reverses an earlier one.
- to-spec and to-tickets: turn a conversation into a feature spec, then cut the spec into tickets.
- night and retro (started by the founder): run an unattended night of tickets; review a session.

The product spec (SPEC.md, docs/spec/) is the source of truth and the decision log (docs/decisions/) its history;
where they disagree, fix the spec. Architecture is in docs/architecture/, each feature's spec and decisions in
docs/features/, and the design system in design/system/.
