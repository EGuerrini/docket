---
name: land
description: Land a finished ticket on master through dk land, and handle a failing gate or a failing master. Load when the build is done and every test passes.
---

# Land a ticket

```
tools/dk/dk land <ticket path>
```

It runs, in order: `dk check`, then `dk verify` for the features whose files changed, then the definition-of-done
gate (scripts/dod.py, with the diff and the evidence). It commits with the subject `<spec> NN: <what changed>`,
pushes HEAD to master as a fast-forward, and watches the CI run for that commit. The verdict is written to
~/.docket/dod/<branch>.json. It works from a worktree too: dk land starts the gate with the main checkout's
credentials wrapper, so its Playwright runs have the test credentials.

The guard refuses every other push to master. Do not push master by hand, from a script, or with `--dry-run`.

## A failing gate
- Read the findings. Each names a check id; `tools/dk/dk why <id>` says why the check exists and how to fix it.
- Fix, then run `dk land` again. Any commit after a gate run means running the gate again, which `dk land` does.
- If the gate fails twice, stop and report the findings to the founder with a recommendation. Never work around a
  check.

## A failing master
`dk land` refuses to commit while master's last CI run is failing, and prints the failing commit. Revert the commit
that broke it (`git revert <sha>` on a branch, then `dk land`; a change made only of reverts goes through), or land
the fix from a ticket whose Kind line says `hotfix of <sha>`. A verdict file is not evidence against CI.

## After landing
- Read the CI run for the commit (`dk land` prints it; `gh run view <id>` for detail).
- A job source change: the checks prove the change is consistent, not that the source answers. Read the next
  scheduled run's health line for that source (`gh run view <id> --log | grep -i <source>`) and revert on a refusal
  or a 404.
- Then write the session report (`build`, step 6).
