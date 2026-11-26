# Import template review — diagnosis, corrections, and what remains

**Source**: Africus Co., Ltd., *ALCBT | Excel template review notes*, Rev. 2026-11-11,
from Kongkun Charoenvisal. Copied to GGGI (Lattawan Niyomtham, Piyawan
Suwattanathum, Julie Robles), Maxine Chan and Dietram Oppelt.

**This document**: every claim in that review tested against the live code and
the shipped template, what was corrected, and what still needs a decision.

**Scope of the fix**: `static/docs/import-template.xlsx`, plus a new
plausibility warning on the assembly save path. Branch `rohit-qa`. Not merged.

---

## 1. Verdict on each claim

| # | Africus claim | Verdict | Status |
|---|---|---|---|
| 1.1 | Required fields not marked in the template | Not tested | Open |
| 1.2 | No data validation; room area must be whole number; room names must match the UI dropdown | Not tested | Open |
| 2.1.1 | No sheet for cassette / ceiling-mounted air conditioners | **Correct** | Open — see §4.1 |
| 2.1.2 | "Ventilation System - CeilingWa" is inconsistent with the UI | **Correct in substance** | Partly fixed |
| 2.2.1 | VRF and both chiller sheets carry an extra "Type of cooling system" column | **Correct** | Already fixed in the importer, template unchanged |
| 2.2.2 | Fan Coil sheet inputs differ from the Web UI | **Correct** | Open — see §4.2 |
| 2.2.3 | By-Component sheet misaligned: UI uses percentages, template uses quantities | **Correct** | Mitigated — see §3.3 |
| 3.1 | No Bill of Quantity sheet | **Correct** | Open — see §4.3 |
| 3.2 | No connection to the BEAT EPD database | **Correct** | Open — see §4.4 |
| — | Request for the BEAT input data model and documentation | **Outstanding on HEAT's side** | See §5 |

---

## 2. Corrections to my own first assessment

Recorded because both errors were reported before they were checked properly.

**I said the cassette sheet exists and there is no data loss. That was wrong.**
The importer maps `'ceilingwa' → VentilationType.CASSETTE_AC`, which is what I
read first. But `CoolingSystemAirConditioner.ac_type` also offers
`("cassette", "Cassette / Ceiling-mounted Air Conditioners")`, and
`cooling-system.html` wires `'cassette-ac'` to the split-AC form, which
collects refrigerant type, refrigerant quantity, leakage factor and year of
installation. There are two different cassette concepts in BEAT, and only the
ventilation one has a sheet. See §4.1.

**I said the template's dropdowns still offer 13 retired component names.**
They do not. The 14 retired names are **section headings** on the List sheet.
Every dropdown range was checked and not one of them includes a heading cell.
The component dropdown (`List!$I$2:$I$15`) carries the correct post-migration
names. This was a documentation defect, not a broken dropdown, and it has been
corrected anyway.

---

## 3. What was corrected

### 3.1 Ten sheet names

| Was | Now |
|---|---|
| Ventillation System - Air Handl | Ventilation System - AHU |
| Ventillation System - Fan Coil | Ventilation System - Fan Coil |
| Ventillation System - CeilingWa | **Ventilation - Cassette AC** |
| Ventillation System - Dedicated | Ventilation System - DOAS |
| Ventillation System - CeilingEx | **Ventilation - Exhaust Fan** |
| Lightning System - LED | Lighting System - LED |
| Lightning System - Fluorescent | Lighting System - Fluorescent |
| Lightning System - CFL | Lighting System - CFL |
| Lightning System - Incandescent | Lighting System - Incandescent |
| Lightning System - Metal Halide | Lighting System - Metal Halide |

"Ventillation" and "Lightning" are misspellings that shipped to partners.
"CeilingWa" and "CeilingEx" are internal shorthand: Africus reported the
cassette sheet as missing partly because the word cassette appears nowhere on
it.

**Why this is safe.** `import-dialog.html` matches sheets on `'cassette'` as
well as `'ceilingwa'`, on `'lighting'` as well as `'lightning'`, and on
`'ahu'` / `'fancoil'` / `'doas'` / `'exhaustfan'` rather than on the word
"Ventillation". Files users already saved under the old names still import.
Verified: no cross-sheet formula references and no defined names point at any
renamed sheet.

### 3.2 Fourteen retired taxonomy section headings

Migration 0046 consolidated 19 building components into 14 in July 2026. The
List sheet headings that group the construction techniques were never updated.
Where several old components merged into one, the new name now carries the old
grouping in brackets so the blocks stay distinguishable.

```
List!V3    Bottom Floor Construction       → Ground Floor
List!V14   Intermediate Floor Construction → Beams & Slabs (Intermediate Floors)
List!V25   Floor Finish                    → Finishes (Floor)
List!V40   Roof Construction               → Roof
List!N46   Roof Construction               → Roof
List!V69   Beams                           → Beams & Slabs (Beams)
List!V74   Exterior Walls                  → External Walls
List!V90   Interior Walls                  → Internal Walls & Partitions
List!V110  Window Frames                   → Windows (Frames)
List!V120  Window Glazing                  → Windows (Glazing)
List!V127  Roof Insulation                 → Insulation (Roof)
List!V141  Wall Insulation                 → Insulation (Wall)
List!V155  Floor Insulation                → Insulation (Floor)
List!V196  Staircases and Ramps            → Staircases & Ramps
```

### 3.3 A warning when material shares cannot be right

New: `pages/views/assembly/share_plausibility.py`, with
`pages/tests/test_share_plausibility.py` (10 tests), wired into
`save_to_assembly.py`.

This is the response to claim 2.2.3. The template asks for raw m³ per
material; the UI asks for a **percentage share** of the component. Someone who
learns the template first carries the absolute habit into the UI, and the
percent box accepts it silently.

**This has already cost us data.** ATS Rhapsody in the Uttar Pradesh registry
has its foundation entered as 50% ready-mix concrete and 50% reinforcement
steel. Correcting that one component moves the building from 686.1 to
765.5 kgCO2e/m². Nothing objected, because 50 + 50 = 100 and both materials
are real. So a sum check alone would not have caught it; the second check is
about whether the **split** is physically possible.

Two checks, both warnings, neither blocks a save:

1. Shares that do not sum to 100 ± 0.5.
2. Reinforcement above 25% by mass or 10% by volume in a component that also
   contains concrete.

Those two thresholds are **assumptions, labelled as such in the code**. They
are not published limits. Real reinforcement is roughly 1–2% by volume and up
to 4–6% in heavily reinforced sections; the thresholds sit well above that on
purpose, so the warning fires on a data-entry mistake rather than on an
unusual but genuine design. A warning users learn to dismiss protects nothing.

### 3.4 Four test files updated

`test_template_file.py`, `test_template_imports_end_to_end.py` and
`test_ventilation_sfp_guard.py` referenced the old sheet names. Only the names
were changed; no assertion was weakened or removed. AGENTS.md rule 9 normally
forbids editing tests another agent wrote, so it is flagged here: the rename
was the task, and these were name references, not decisions.

### 3.5 How the template was edited, and why it matters

**openpyxl cannot round-trip this file.** It warns
`Data Validation extension is not supported and will be removed` and would
have silently dropped all 30 dropdowns on save. Every edit was therefore made
as a string replacement inside the xlsx zip, with every other part copied
through byte for byte.

**Verification after the rebuild:**

| Check | Result |
|---|---|
| x14 dropdowns | 30 before, 30 after |
| Sheets | 26 before, 26 after |
| Cells compared | 152,654 |
| Cells differing | **14** — every one intended |
| Full test suite | **1096 passed, 10 skipped, 0 failed** |

The 10 skips are pre-existing: they need the post-0046 taxonomy, which the
local dev database does not carry.

---

## 4. What still needs correcting

### 4.1 Cassette air conditioners cannot be imported (claim 2.1.1)

**The defect.** BEAT has two cassette concepts:

- `CoolingSystemAirConditioner.ac_type = "cassette"` — a **cooling** system.
  The UI gives it the split-AC form: refrigerant type, refrigerant quantity,
  leakage factor, year of installation, EER/ISEER/COP.
- `VentilationType.CASSETTE_AC` — a **ventilation** type. Airflow and fan
  power only. No refrigerant fields.

The template has a sheet only for the second. `COOLING_TAB_MAP` has no
cassette entry. So a cassette AC entered through the UI counts refrigerant
leakage; the same unit imported from Excel cannot express refrigerant data at
all.

**Correction needed.** Add a "Cooling System - Cassette AC" sheet with the
split-AC column layout, and a `'cassette ac'` entry in `COOLING_TAB_MAP`
mapping to `('air_conditioner', 'cassette', None, None)`. The AC column
indices already match the split layout, so the parser needs no change.

**Impact if left.** Refrigerant leakage emissions are missing from every
imported building that uses cassettes. Cassettes are common in the ALCBT
countries.

### 4.2 Fan Coil sheet does not match the UI (claim 2.2.2)

The template's Fan Coil sheet has 9 columns. Africus's appendix records the UI
form as 12, with `Part of which cooling system`, `Power input per unit` and a
computed total that the sheet lacks. The sheet cannot express which cooling
system a fan coil belongs to, so that link is lost on import.

**Correction needed.** Align the sheet to the UI form, and confirm what the
importer should do with the parent-system link.

### 4.3 No Bill of Quantity sheet (claim 3.1)

Worth stating plainly in the reply: **BOQ is fully built in BEAT.** There is
`pages/views/boq/boq.py`, a `BOQAssemblyForm`, an `is_boq` flag on `Assembly`
and its own test suite. The gap is in the Excel template only.

Africus's underlying point is the stronger one: real BOQs give aggregated
quantities by material across the whole structure, not split by foundation,
column, beam and slab. The By-Component sheet cannot take that shape. The BOQ
path in the UI can.

**Correction needed.** A BOQ sheet (material, country, quantity, unit,
classification) plus an importer branch creating `is_boq=True` assemblies.
Larger than the other items: new sheet, new endpoint, new tests.

### 4.4 No EPD database connection (claim 3.2)

Materials are matched by name plus country text. The importer records that
**37 of 100 plausible material names resolve across a border**, and those
import with another country's localised carbon factor and a warning rather
than being refused.

**Correction needed.** Either embed a generated EPD list in the template as a
dropdown, or publish an export endpoint the template can be regenerated from.
Embedding goes stale; regeneration needs an owner.

### 4.5 The technique dropdown is bound to row position, not to the component

Not in the Africus review. Found while checking it, and more serious than
anything they listed.

Column B (Building Component) offers all 14 components on every row from 3 to
59. Column C (Construction Technique) is bound to **fixed row blocks**:

```
C3:C5   → List!W4:W8      (Ground Floor techniques)
C6:C8   → List!W15:W23    (Beams & Slabs)
C9:C11  → List!W57:W59    (Foundations)
C12:C14 → List!W15:W23    (Beams & Slabs)
...
```

The blocks line up with the template's own example rows, so the file is
internally consistent **as long as nobody changes the row layout**. Add a row,
delete a row, or enter components in a different order, and the technique
dropdown offers another component's techniques. Column C validation also stops
at row 59 while B runs to 59 and D, F and J run to 61–63.

**Correction needed.** Dependent dropdowns via named ranges and `INDIRECT`,
keyed on the component chosen in column B. Not attempted here: it means
restructuring the List sheet, and openpyxl cannot write these validations, so
it has to be done by hand in Excel or by generating the XML.

**Impact if left.** A technique that does not belong to its component imports
without a classification. The material, quantity and carbon are still correct;
only the technique label is lost. So this corrupts classification, not carbon.

### 4.6 Not tested (claims 1.1 and 1.2)

Required-field colour coding, whole-number room areas, and room-name matching
against the UI dropdown are UI behaviours rather than code that can be read
off. They need someone to sit with the tool and the template.

---

## 5. The data model request

Africus asked twice for the BEAT input data model and documentation, did not
receive it, and reverse-engineered it. They need it for the BIM/IFC exchange
feature and have now put the request in writing with GGGI copied.

**Their appendix was validated against the live template and is accurate.**
Spot checks:

| Sheet | Their field list | Actual | Match |
|---|---|---|---|
| S02 Building Details | 10 fields, A1–J1 | 10 columns | exact |
| S12 Cassette (CeilingWa) | 10 fields, A1–J1 | 10 columns | exact |
| S25 Structural By-Component | A1–G1 + I2–L2 | A–G, I–L | exact |
| S11 Fan Coil (template) | 9 fields | 9 columns | exact |
| S11 Fan Coil (UI) | 12 fields | — | the 2.2.2 discrepancy |

Their `S26 | List` note — "it is not an EPD catalogue with stable IDs" and "do
not treat row position as a confirmed join" — is exactly right, and §4.5 above
is the proof of it.

**Recommendation**: adopt their appendix as the agreed reference, correct the
two places where they describe UI forms rather than template sheets, and
return it to them. It is faster than writing one from scratch, it credits
their work, and it unblocks the IFC feature.

---

## 6. Decisions needed

1. **§4.1 cassette import** — refrigerant data is missing from imported
   buildings today. This is the one with a carbon consequence.
2. **§4.3 BOQ sheet** — needs a developer and a decision on who.
3. **§4.4 EPD connection** — embed and go stale, or publish an endpoint and
   give it an owner.
4. **§4.5 dependent dropdowns** — needs hand work in Excel.
5. **§5 data model** — adopt the Africus appendix, or commission our own.

---

*Prepared 2026-11-11. Branch `rohit-qa`, not merged. Template changes verified
cell-for-cell against the previous file; full suite green.*
