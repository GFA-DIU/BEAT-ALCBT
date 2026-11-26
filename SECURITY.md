# Security policy

BEAT is a live web application that stores user accounts and building data.
If you find a security problem, please tell us privately so we can fix it
before it is misused.

## How to report

**Do not open a public issue, pull request or discussion.**

Use one of these instead:

1. **GitHub private reporting:** on the repository's **Security** tab, choose
   **Report a vulnerability** (if the button is available).
2. **Email:** write to <kontakt@heat-international.de> with the subject
   "BEAT security".

Please include:

- what the problem is and where (URL, file, or feature)
- the steps to reproduce it
- what an attacker could do with it

## What happens next

- We acknowledge your report within **5 working days**.
- We keep you informed while we fix it.
- We credit you when the fix is published, unless you prefer not to be named.

## Scope

In scope: the code in this repository and the live tool at
<https://beat-alcbt.gggi.org>.

Please **do not** run automated scanners or load tests against the live tool,
access other users' data, or send spam. Test against your own local copy
instead (see the README).

## Exposed secrets

If you find a key, password or token in this repository or its history,
report it privately as above and do not quote it anywhere. Maintainers rotate
it following [docs/SECRETS.md](docs/SECRETS.md).

## Supported versions

Only the current `main` branch is supported. There are no older releases.
