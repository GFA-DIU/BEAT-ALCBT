# Contributing to BEAT

Thank you for helping. BEAT's carbon figures end up in reports and policy
decisions, so the bar for a change is less "does it run" and more "is every
number right and traceable". This page explains how to get a change in.

## Ways to help

- **Report a bug** if something breaks or a page shows the wrong thing.
- **Report a calculation or data problem** if a carbon figure looks wrong, an
  EPD is mislabelled or an emission factor is out of date. These are the most
  valuable reports we get. Please include the building or EPD and the figure
  you expected, with its source.
- **Translate** the interface. See [LOCALIZATION_GUIDE.md](LOCALIZATION_GUIDE.md).
- **Write code or documentation**, as described below.

Use the [issue templates](https://github.com/GFA-DIU/BEAT-ALCBT/issues/new/choose).
For a security problem, **do not open an issue**: follow [SECURITY.md](SECURITY.md).

## Branches

| Branch | Purpose |
|---|---|
| `main` | Production: what runs at beat-alcbt.gggi.org |
| everything else | Work in progress |

Open pull requests against `main`. Merging does **not** deploy; a maintainer
deploys separately (see the README).

## Making a change

1. Fork the repository (or create a branch if you have write access).
2. Set up BEAT locally. See [Run BEAT locally](README.md#run-beat-locally).
3. Make your change, with tests.
4. Run the checks:

   ```bash
   pytest -q                      # full suite, about 10 minutes
   python manage.py check
   ```

5. Open a pull request and fill in the template.

## Rules for changes that touch a carbon number

These come from [AGENTS.md](AGENTS.md), which explains each one with the
mistake that caused it. The short form:

1. **No unsourced numbers.** Every factor, default or threshold needs a source.
   If you must assume a value, say so in the code, on screen and in the docs.
2. **One calculation, one place.** Manual entry and Excel import must use the
   same code. If you change one, change the other in the same pull request.
3. **Round only for display**, never inside a shared function.
4. **Refuse rather than guess.** If an input cannot be converted honestly,
   return nothing and say why instead of substituting a default.
5. **Show the effect.** In the pull request, say how many records the change
   affects and how the figures move, before and after.
6. **A test must be able to fail.** Check that your new test fails without
   your fix.

## Secrets

The repository is public. Never commit a key, password, token or connection
string, not even in a test or a comment. Use environment variables; see
[docs/SECRETS.md](docs/SECRETS.md).

## Code style

- Python: follow the existing style; keep functions small and named for what
  they do.
- Templates live in `/templates` (not `pages/templates`).
- Comments and commit messages explain **why**, not what.

## Licence

By contributing you agree that your contribution is licensed under the
[Apache License 2.0](LICENSE), the same as the rest of BEAT.
