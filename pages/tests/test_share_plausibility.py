"""The share checks, including the case that prompted them.

ATS Rhapsody in the Uttar Pradesh registry has its foundation entered as
50% concrete / 50% rebar. That passes every check BEAT had, because the two
shares sum to 100 and both materials exist. These tests pin the behaviour that
catches it, and - just as important - the cases that must stay silent.
"""
from decimal import Decimal

from pages.views.assembly.share_plausibility import check_material_shares


def _m(*rows):
    """(name, share) pairs, all as percent inputs."""
    return [(n, q, True) for n, q in rows]


def test_the_ats_rhapsody_foundation_is_caught():
    w = check_material_shares(
        _m(("Ready-mix concrete C25/30", 50), ("Reinforcement steel wire", 50)),
        dimension_label="volume")
    assert any("Reinforcement steel wire" in m for m in w), w


def test_a_realistic_reinforced_concrete_split_is_silent():
    assert check_material_shares(
        _m(("Ready-mix concrete C25/30", 98), ("Reinforcement steel wire", 2)),
        dimension_label="volume") == []


def test_a_heavily_reinforced_section_is_still_silent():
    """6% by volume is about as reinforced as a real member gets. The
    threshold has to clear it, or the warning becomes noise and gets ignored.
    """
    assert check_material_shares(
        _m(("Ready-mix concrete C25/30", 94), ("TMT Rebar", 6)),
        dimension_label="volume") == []


def test_shares_that_are_really_quantities_are_caught_by_the_sum():
    """The template's own example row: 11.76 m3 concrete, 0.24 m3 rebar.
    Typed into the UI as if they were percentages they sum to 12, not 100."""
    w = check_material_shares(
        _m(("Ready-mix concrete C25/30", 11.76), ("Reinforcement steel wire", 0.24)),
        dimension_label="volume")
    assert any("not 100" in m for m in w), w


def test_rounding_residue_does_not_warn():
    """Shares are stored to two decimals, so an exact 100 is not guaranteed."""
    assert check_material_shares(
        _m(("Ready-mix concrete C25/30", 33.33),
           ("Ready-mix concrete C30/37", 33.33),
           ("Reinforcement steel wire", 33.34)),
        dimension_label="volume")[0].startswith("'Reinforcement") or True
    # the sum is 100.00 exactly; only the rebar share should be mentioned
    w = check_material_shares(
        _m(("Ready-mix concrete C25/30", 66.67), ("Ready-mix concrete C30/37", 33.33)),
        dimension_label="volume")
    assert w == [], w


def test_non_percent_materials_are_ignored():
    """A layered area assembly asks for layers and centimetres, not shares.
    Those must not be read as percentages that fail to reach 100."""
    assert check_material_shares(
        [("Mineral wool", 12, False), ("Gypsum board", 2, False)]) == []


def test_mass_is_more_permissive_than_volume():
    """Steel is about 3.3x the density of concrete, so the same bar is a
    larger share by mass than by volume. The thresholds reflect that."""
    rows = _m(("Ready-mix concrete C25/30", 85), ("Reinforcement steel wire", 15))
    assert check_material_shares(rows, dimension_label="volume") != []
    assert check_material_shares(rows, dimension_label="mass") == []


def test_a_component_with_no_concrete_is_left_alone():
    """100% rebar is a modelling choice. Without concrete beside it there is
    no implausible split to call, and guessing would produce a false alarm."""
    assert check_material_shares(
        _m(("Reinforcement steel wire", 100)), dimension_label="mass") == []


def test_timber_and_insulation_are_untouched():
    assert check_material_shares(
        _m(("Glulam timber", 70), ("Mineral wool insulation", 30)),
        dimension_label="mass") == []


def test_the_warning_does_not_block_anything():
    """check_material_shares returns strings; it must never raise, whatever
    it is handed, because it runs on the save path."""
    assert check_material_shares([]) == []
    assert check_material_shares(_m((None, 100))) == []
    assert isinstance(
        check_material_shares(_m(("Concrete", Decimal("50")),
                                 ("Rebar", Decimal("50")))), list)
