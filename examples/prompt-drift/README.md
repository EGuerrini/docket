# Versioned prompts with a CI drift check

In docket the fit read runs in two places: the Python pipeline (batched, on a schedule) and the
TypeScript app (live, when a person opens a card). Both must send the same prompt, model and effort,
or an eval of one says nothing about the other.

The rule: prompts are versioned files that are never edited in place (`prompts/fit_v1.md`,
`fit_v2.md`, ...). One config names the live version, the model and the effort. A script emits the
app's copy as JSON, and CI rebuilds that JSON and byte-compares it on every push.

```
python3 emit.py            # write app/fit_prompt.json from fit_config.py and prompts/
python3 emit.py --check    # exit 1 if the committed JSON differs from a fresh build
python3 -m unittest -v test_drift
```

Changing `EFFORT = "low"` to `"medium"` in `fit_config.py` without re-emitting:

```
$ python3 emit.py --check
app/fit_prompt.json drifted from fit_config.py and prompts/ (effort): run python3 emit.py and commit both
$ echo $?
1
```

Why byte-compare rather than compare parsed fields: whitespace in a prompt is part of the prompt.

In docket the same pattern guards two other generated copies: the posting-read export and the price
table the pipeline and the app both use for metering.

The CI step in this repository is `.github/workflows/examples.yml`, step "prompt drift check".
