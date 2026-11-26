# Secrets in BEAT

This repository is **public**. Anything committed to it, including in an old
commit later "removed", can be read and copied by anyone, permanently.

This page lists every secret setting BEAT uses **by name only**, where it is
kept, and how to change it safely. It never contains a value, and nor should
anything else in this repository.

## The rules

1. **Never commit a secret value** — not in code, config files, docs,
   notebooks, test fixtures, commit messages or pull request text.
2. **Never print, paste or screenshot a value**, not even part of one
   (a "masked" prefix still identifies the key). Refer to a secret by its
   setting name, e.g. `FIELD_ENCRYPTION_KEY`.
3. **Secrets live only in the server's environment** (Heroku config vars for
   the live tool) or in a local `.env` file. `.env` is listed in `.gitignore`;
   keep it that way.
4. **If a value is ever exposed, rotate it.** Deleting it from the code does
   not help: git history keeps it. Treat an exposed secret as known to
   everyone and replace it.
5. **Report an exposure privately** — see [SECURITY.md](../SECURITY.md). Do not
   open a public issue that describes or quotes it.

## Secret settings

| Setting | What it protects | If it leaks | Live tool keeps it in |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Signs sessions, password-reset links and cookies | Someone could forge logins | Heroku config var |
| `FIELD_ENCRYPTION_KEY` | Encrypts users' stored email addresses | Stored emails can be decrypted | Heroku config var |
| `SUPABASE_DATABASE_URL` | Full access to the production database (hosted on Supabase) | Total data loss or theft | Heroku config var |
| `EMAIL_HOST_PASSWORD` | The mail account that sends sign-up and reset emails | Spam or phishing sent as BEAT | Heroku config var |
| `NEW_RELIC_LICENSE_KEY` | Performance monitoring account | Fake data sent to our monitoring | Heroku config var |
| `HONEYBADGER_API_KEY` | Error-tracking account | Fake error reports | Heroku config var |
| `ECO_PLATFORM_TOKEN` | ECO Platform EPD API access (data loading only) | Our API quota used by others | Local `.env` of whoever loads EPDs |
| `REPORT_API_KEY` | AI report generation (feature currently off) | Charges on our account | Not set while the feature is off |
| `LOAD_TESTING_PASSWORD` | Test account used by the load tests | Login as that test user | Local `.env` only |
| `DJANGO_ADMIN_URL` | Hides the admin login path | Admin page easier to find (it still needs a login) | Heroku config var |

Not secret, but set the same way: `EMAIL_HOST_USER`, `DEFAULT_FROM_EMAIL`,
`SITE_DOMAIN`, `SITE_NAME`, `NOMINATIM_AGENT_STRING`, `NEW_RELIC_APP_NAME`.

When you add a new secret setting, add a row here in the same pull request.

## Checking a secret without showing it

To confirm a setting exists, ask for its **length**, never its value:

```bash
heroku config:get NEW_RELIC_LICENSE_KEY -a beat-qa | tr -d '\n' | wc -c   # 0 = missing
```

To compare two values, compare them in a script that prints only
`SAME` or `DIFFERENT`.

## How to rotate

Do this from a maintainer's machine with Heroku access. Setting a config var
restarts the app (a few seconds of downtime).

### Most keys (New Relic, Honeybadger, email password, ECO Platform, report API)

1. Create a new key in the provider's dashboard.
2. Set it on Heroku: `heroku config:set NAME=<new value> -a beat-qa`. Type
   or paste the value only into this command, nowhere else.
3. Check the service still works (monitoring receives data, an email sends).
4. **Revoke the old key** in the provider's dashboard. Until you do, the
   leaked one still works.

### `DJANGO_SECRET_KEY`

Set a new random value as above. Everyone is logged out and old
password-reset links stop working. Nothing is lost.

### `FIELD_ENCRYPTION_KEY` — ⚠️ do not just replace it

Users' email addresses are stored **encrypted with this key**. BEAT is
configured with exactly one key (`EJF_ENCRYPTION_KEYS` in
`django_project/settings.py`), so if you swap the value, **every stored email
becomes unreadable** and nobody can log in or reset a password.

A safe rotation needs a code change first:

1. Change the setting to accept a list: the new key first (used to encrypt),
   the old key second (still able to decrypt). The library already supports
   this (`MultiFernet`).
2. Deploy with both keys set.
3. Re-save every encrypted record so it is re-encrypted with the new key.
4. Verify that every record decrypts using the new key alone.
5. Only then remove the old key.

Take a database backup before step 2, and keep the old key somewhere safe
(not in this repository) until step 4 has passed. Rehearse on a copy of the
database first.

### `SUPABASE_DATABASE_URL`

The production database is hosted on **Supabase**, not Heroku, so nothing
updates automatically. Reset the database password in the Supabase dashboard,
then set the new connection string on Heroku with `heroku config:set` as
above, and check the app loads. (A comment in `settings.py` still mentions
Heroku's `DATABASE_URL`; the code reads `SUPABASE_DATABASE_URL`.)

## Before you commit

A quick check for anything that looks like a key in your change:

```bash
git diff --cached | grep -iE "(key|token|secret|password)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}"
```

No output means nothing obvious. It is a safety net, not a guarantee.
