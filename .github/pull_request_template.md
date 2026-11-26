## What this changes

<!-- One or two sentences. Link the issue: "Fixes #123". -->

## Why

<!-- The reason, and why the obvious alternative was not chosen. -->

## Effect on carbon figures

- [ ] No carbon figure changes
- [ ] Figures change: say which, how many records are affected, and the before/after values below

<!-- Example: "Chiller plants: 4 buildings, 945,000 -> 63,000 kWh/yr, each was multiplied by its chiller count twice." -->

## Checklist

- [ ] Every new number has a source, or is labelled as an assumption in code, on screen and in docs
- [ ] If the calculation exists in both manual entry and Excel import, both are changed
- [ ] Rounding only happens at display
- [ ] New tests fail without this change
- [ ] `pytest -q` and `python manage.py check` pass
- [ ] No secrets, personal data or production data in the diff
