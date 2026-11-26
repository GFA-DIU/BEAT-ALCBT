# BEAT — Building Life Cycle Assessment Tool

BEAT is a free web tool for calculating the **whole-life carbon footprint of
buildings**: the carbon in the materials a building is made of (embodied
carbon) and the carbon from the energy it uses (operational carbon).

**Live tool:** <https://beat-alcbt.gggi.org> · **Licence:** [Apache 2.0](LICENSE)

It is built for the **ALCBT** project run by GGGI in five countries:
**Cambodia, India, Indonesia, Thailand and Viet Nam**. Users there enter a
building — its materials and quantities, and its energy systems — and BEAT
reports the carbon with country-specific data.

## What BEAT calculates

| Life-cycle stage (EN 15978) | What it covers | Data source |
|---|---|---|
| **A1–A3** Product | Carbon to make the materials | EPDs (Environmental Product Declarations) |
| **A4** Transport | Getting materials to site | Distance × freight emission factor |
| **A5** Construction | Site energy and construction waste | Project assumptions |
| **B6** Operational energy | Electricity and fuels used by the building | National grid and fuel emission factors |

Results are shown per building and per m² of floor area. Each figure is traced
to its EPD or emission factor, and values BEAT has to assume are labelled as
assumptions on screen. Stages BEAT does not model (for example B4 replacement
and C1–C4 end of life) are listed in the methodology documents.

### Main features

- **EPD library** with several thousand EPDs from international programme
  registries (EPD International, Ökobaudat, ECO Platform and others) plus
  national and generic datasets for the ALCBT countries
- **Building editor** by component (walls, floors, roofs, foundations …) with
  a material picker, or **Excel/BoQ import** for many buildings at once
- **Operational systems**: air conditioners, chillers, ventilation, lighting,
  on-site renewables and refrigerant leakage
- **Dashboard** per building, with carbon rating labels and benchmarks
- Interface translation files for Hindi, Indonesian, Khmer, Thai, Vietnamese and
  other regional languages (see [LOCALIZATION_GUIDE.md](LOCALIZATION_GUIDE.md))

## Documentation

**Methodology — for users, reviewers and researchers**

| Document | What it explains |
|---|---|
| [Carbon calculation methodology](docs/carbon_calculation_methodology.md) | Standards basis, what is and is not counted. *Its module table predates A4–A5 going live; see the next row.* |
| [A4–A5 upfront carbon](docs/a4_a5_upfront_carbon_scope.md) | Transport and construction-stage carbon |
| [Operational carbon (B6)](docs/operational_carbon_methodology.md) | Energy use and the 50-year operational figure |
| [Energy carriers](docs/operational_energy_carriers.md) | Electricity, fuels and what each must account for |
| [Thailand emission factors](docs/thailand_operational_ef.md) | Thai grid and fuel factors |
| [Carbon rating labels](docs/carbon_rating_labels.md) | How the A–G labels are assigned |
| [Benchmark sources](docs/layer2_benchmark_sources.md) | What each country publishes for benchmarks |
| [Component taxonomy](docs/taxonomy_mapping.md) | How building components and techniques are classified |
| [BIM integration](docs/bim_beat_integration_methodology.md) | Importing quantities from IFC models (planned) |

**For maintainers** — the rest of [`docs/`](docs) (handovers, deploy runbooks,
review notes and working spreadsheets), [AGENTS.md](AGENTS.md) (rules for
anyone changing the code) and
[FRONTEND_SYSTEMS_INTEGRATION.md](FRONTEND_SYSTEMS_INTEGRATION.md). These are
internal working notes: they record decisions and incidents and may be out of
date. They are not user documentation.

---

## Run BEAT locally

You need **Python 3.11**, **Docker** (for the PostgreSQL database) and
**Node.js** (for the front-end build).

### 1. Start the database

```Bash
docker compose up db
```

The Django settings detect whether they run in production; locally they use
this Docker database.

### 2. Install and run

Next, start the Django application

**Note:** Create a `.env` file in the root directory with the following environment variables:

```bash
# Site Configuration (for email confirmation links)
SITE_DOMAIN="127.0.0.1:8000"  # For production, use actual domain (e.g., "beat.yourdomain.com")
SITE_NAME="BEAT Local"         # For production, use "BEAT"

# Email Configuration (optional for local development)
EMAIL_HOST_USER="your-email@example.com"
EMAIL_HOST_PASSWORD="your-password"
DEFAULT_FROM_EMAIL="your-email@example.com"
```

Then install and run:

```Bash
$ python -m venv .venv
$ source .venv/bin/activate        # Windows: .venv\Scriptsctivate

(.venv) $ pip install -r requirements.dev.txt
(.venv) $ python manage.py migrate
(.venv) $ python manage.py update_site # Updates site domain from SITE_DOMAIN env var (Needed for email sending)
(.venv) $ python manage.py createsuperuser
(.venv) $ python manage.py create_email_address # Creates an email_address for the superuser (Needed for all_auth to work)
(.venv) $ python manage.py cities_light
(.venv) $ python manage.py load_country_global # Adds a "Global" country option for EPDs
(.venv) $ python manage.py load_default_cookies # Creates the default cookies
(.venv) $ python manage.py runserver
# Load the site at http://127.0.0.1:8000
```

The basic `BuildingCategory` and `MaterialCategory` data is automatically imported through the migrations.

If `cities_light` is not being loaded, try:

```Bash
(.venv) $ python manage.py cities_light --force-import-all
```

#### Load EPD data

To load the EPD data from Ökobaudat:

```Bash
(.venv) $ python manage.py load_oekobaudat_epds
```

**Note**: The Ecoplatform Loader expects an API Token `ECO_PLATFORM_TOKEN` in an `.env` file.

To load the EPD data from Ecoplatform:

```Bash
(.venv) $ python manage.py load_ecoplatform_epds
```

To load all generic EPDs found under `pages/data`:

```Bash
(.venv) $ python manage.py load_local_epds
```

To load a specific set of local EPDs, name the relevant file with one of the keynames found in `pages/management/commands/load_local_epds.py`. See for example below:

```Bash
(.venv) $ python manage.py load_local_epds --file EDGE_HANDBOOK_EPDs
```

#### Load labels

Load EPD (manual) label mappings from label file

```Bash
(.venv) $ python manage.py map_GCCA_EPD_label
```

### Inspecting and restoring the database

To inspect the data tables in postgres instead of Django admin

```Bash
pgcli -h localhost -p 5432 -U postgres -d postgres
```

To load heroku DB snapshot (custom/tar PostgreSQL), follow these steps:

1. Spin-up the DB and identify the container

```Bash
docker compose up -d db
DB_CID=$(docker compose ps -q db)
echo "$DB_CID"
```

2. Verify snapshot and move into container

```Bash
$ SNAPSHOT=./path/to/snapshot
# custom/tar shows 'PostgreSQL custom database dump' or 'POSIX tar'
$ file "$SNAPSHOT"
$ docker cp "$SNAPSHOT" "$DB_CID":/tmp/snapshot.dump
```

3. Restore custom dump with `pg_restore`

```Bash
# Drop + recreate target DB inside the container (avoid lingering objects)
$ docker exec -i "$DB_CID" bash -lc 'dropdb -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'

# restore from snapshot
$ docker exec -i "$DB_CID" bash -lc 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-privileges -j 4 /tmp/snapshot.dump'
```

4. Smoke test the restore

```Bash
docker exec -it "$DB_CID" psql -U postgres -d postgres -c '\dt'    # list tables
docker exec -it "$DB_CID" psql -U postgres -d postgres -c 'select now();'
```

## Contributing

Contributions are welcome — bug reports, translations, data corrections and
code. Please read **[CONTRIBUTING.md](CONTRIBUTING.md)** first. It explains the
branches, how to run the tests and what a pull request needs.

Because BEAT's numbers go into reports and decisions, changes that touch a
calculation must say where every number comes from (see [AGENTS.md](AGENTS.md)).

### Tests

```Bash
(.venv) $ pytest -q            # the full suite takes about 10 minutes
(.venv) $ python manage.py check
```

### Load testing

Run only against a server you are allowed to load-test:

```Bash
(.venv) $ locust -f load_testing/locust/locustfile.py --host <your-server>
```

### Deploying (maintainers only)

Production is the `main` branch, hosted on Heroku. **Merging to `main` does not
deploy.** A maintainer with Heroku access deploys with:

```Bash
git fetch origin                              # without this you deploy an old commit
git push heroku origin/main:refs/heads/main
```

Database migrations run automatically during the deploy (`release` line in the
`Procfile`). Check afterwards with `heroku releases -a beat-qa -n 1`. See
[AGENTS.md §10](AGENTS.md) for the details that have gone wrong before.

## Security

Please **do not** report security problems in a public issue. See
[SECURITY.md](SECURITY.md) for how to report them privately.

## Support

Questions about using the tool: <kontakt@heat-international.de>.
Bugs and feature requests: [open an issue](https://github.com/GFA-DIU/BEAT-ALCBT/issues).

## Licence

[Apache 2.0](LICENSE). Data loaded into BEAT (EPDs, emission factors) comes
from third-party sources with their own terms; the source of each EPD is shown
in the tool.

The tool was built with the public Django template `wsvincent/lithium`. As requested, the copyright notice is included below:

```Text
djangox: Copyright (c) 2020 William Vincent
django-allauth: Copyright (c) 2010 Raymond Penners and contributors
cookie-cutter-django: Copyright (c) 2013-2020 Daniel Greenfeld

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
```
