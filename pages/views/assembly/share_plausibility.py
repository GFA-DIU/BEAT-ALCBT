"""Warn when the material shares of a structural component cannot be right.

For a mass or volume assembly the UI asks each material for a SHARE of the
component, in percent - "Share of mass", "Share of volume". The import
template asks the same question a different way: it takes the raw m3 or kg per
material and the importer converts those to shares. Someone who learns the
template first and then types a building into the UI carries the absolute
habit across, and the percent box accepts it without complaint.

That is not hypothetical. In the Uttar Pradesh building registry, ATS Rhapsody
has its foundation entered as 50% ready-mix concrete and 50% reinforcement
steel. Correcting that single component to a realistic ratio moved the
building's embodied carbon from 686.1 to 765.5 kgCO2e/m2. Nothing in BEAT
objected, because 50 + 50 = 100 and both materials are real.

So the sum check is not enough on its own. The second check below is about
whether the SPLIT is physically possible, not whether it adds up.

Nothing here blocks a save. These are warnings on a judgement call, and a user
with an unusual but genuine component must be able to enter it.
"""
import re
from decimal import Decimal

# Reinforcement in reinforced concrete, by volume, is on the order of 1-2% in
# ordinary members and reaches perhaps 4-6% in heavily reinforced sections.
# Steel is 7850 kg/m3 against roughly 2400 kg/m3 for concrete, so 6% by volume
# is about 17% by mass.
#
# ⚠️ ASSUMPTION - the two thresholds below are not published limits. They are
# set well above the heavily reinforced case on purpose, so the warning fires
# on a data-entry mistake rather than on an unusual but real design. A lower,
# more "accurate" threshold would be the wrong trade: a warning users learn to
# dismiss protects nothing. 25% by mass is roughly 9% by volume, already
# beyond any normal section; 10% by volume is beyond it the other way.
REBAR_MAX_MASS_SHARE = Decimal("25")
REBAR_MAX_VOLUME_SHARE = Decimal("10")

# Shares are stored to two decimals and the importer resolves its own rounding
# residual onto the largest share, so an exact 100 is not guaranteed. A
# tolerance of half a percentage point passes real rounding and still catches
# someone who entered 11.76 and 0.24 believing they were cubic metres.
SUM_TOLERANCE = Decimal("0.5")

_REBAR = re.compile(
    r"\b(rebar|reinforc\w*\s+(steel|bar|wire)|steel\s+(bar|rod|wire|mesh)"
    r"|tmt\b|deformed\s+bar)", re.I)

_CONCRETE = re.compile(
    r"\b(concrete|cement|mortar|grout|screed)\b", re.I)


def _is_rebar(name):
    return bool(_REBAR.search(name or ""))


def _is_concrete(name):
    return bool(_CONCRETE.search(name or "")) and not _is_rebar(name or "")


def check_material_shares(materials, dimension_label=""):
    """Return a list of human-readable warnings. Empty list means nothing odd.

    `materials` is an iterable of (name, quantity, is_percent) triples. Only
    the percent ones are examined; a component measured in layers or
    centimetres is a different question and is left alone.

    `dimension_label` is "mass" or "volume" where known. It only chooses which
    rebar threshold applies, and the mass one is used when it is not known,
    because mass is the more permissive of the two.
    """
    shares = [(n, Decimal(str(q))) for n, q, pct in materials if pct]
    if not shares:
        return []

    warnings = []
    total = sum(q for _, q in shares)

    if abs(total - Decimal("100")) > SUM_TOLERANCE:
        warnings.append(
            "The material shares add up to %s%%, not 100%%. These fields are a "
            "share of the component, in percent, not the quantity of each "
            "material. If you have the quantities, use the Excel import, which "
            "converts them for you."
            % total.normalize())

    # Only meaningful once the component actually holds both, which is what
    # makes an implausible split recognisable. A component of nothing but
    # rebar at 100% is a modelling choice, not an error we can call.
    has_concrete = any(_is_concrete(n) for n, _ in shares)
    if not has_concrete:
        return warnings

    limit = (REBAR_MAX_VOLUME_SHARE if dimension_label == "volume"
             else REBAR_MAX_MASS_SHARE)

    for name, share in shares:
        if _is_rebar(name) and share > limit:
            warnings.append(
                "'%s' is %s%% of this component. Reinforcement is normally a "
                "few percent of reinforced concrete, so this is almost "
                "certainly the quantity rather than the share. Check it before "
                "relying on the carbon figure."
                % (name, share.normalize()))

    return warnings
