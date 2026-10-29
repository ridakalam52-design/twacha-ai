import itertools

import pytest

from app.catalog import BY_ID
from app.routine import BUDGETS, CLIMATES, build_routine, ingredient_needs, skin_profile
from tests.conftest import scores_from

KEYS = ["moisture", "oiliness", "acne", "pores", "redness", "texture", "dark_circles", "spots"]
PROFILES = {
    "all_good": {k: 90 for k in KEYS},
    "all_bad": {k: 15 for k in KEYS},
    "oily_acne": dict(moisture=72, oiliness=45, acne=42, pores=52, redness=80, texture=66, dark_circles=70, spots=58),
    "dry_sensitive": dict(moisture=40, oiliness=85, acne=86, pores=82, redness=50, texture=55, dark_circles=62, spots=64),
    "mid": {k: 68 for k in KEYS},
}


@pytest.mark.parametrize("profile,budget,climate", list(itertools.product(PROFILES, BUDGETS, CLIMATES)))
def test_monthly_cost_never_exceeds_budget(profile, budget, climate):
    r = build_routine(scores_from(PROFILES[profile]), budget, climate)
    assert r["within_budget"] is True
    assert r["monthly_total"] <= budget
    recomputed = sum(BY_ID[p["id"]].monthly for p in r["products"])
    assert recomputed <= budget
    assert round(recomputed) == r["monthly_total"]


@pytest.mark.parametrize("profile,budget,climate", list(itertools.product(PROFILES, BUDGETS, CLIMATES)))
def test_core_steps_always_present(profile, budget, climate):
    r = build_routine(scores_from(PROFILES[profile]), budget, climate)
    slots = [p["slot"] for p in r["products"]]
    assert slots.count("sunscreen") == 1 and slots.count("cleanser") == 1 and slots.count("moisturizer") == 1
    sunscreen = next(p for p in r["products"] if p["slot"] == "sunscreen")
    assert "SPF 50" in sunscreen["name"] and "PA++++" in sunscreen["name"]
    assert r["am"][-1]["slot"] == "sunscreen"  # sunscreen is always the last AM step
    assert all(s["slot"] != "sunscreen" for s in r["pm"])  # never at night


def test_deterministic(oily_acne):
    assert build_routine(oily_acne, 1500, "humid") == build_routine(oily_acne, 1500, "humid")


def test_acne_gets_salicylic_acid(oily_acne):
    r = build_routine(oily_acne, 1500, "humid")
    ings = {BY_ID[p["id"]].ingredient for p in r["products"] if p["slot"] == "serum"}
    assert "salicylic_acid" in ings
    assert "niacinamide" in ings  # oiliness is the other top concern
    sa_step = next(s for s in r["pm"] if s["product_id"] == "t_min_sa")
    assert sa_step["label"]["en"].startswith("Salicylic")


def test_oily_profile_gets_oily_friendly_core(oily_acne):
    r = build_routine(oily_acne, 1500, "humid")
    assert r["profile"]["type"] == "oily"
    for p in r["products"]:
        if p["slot"] in ("cleanser", "moisturizer"):
            assert "oily" in p["tags"] or "normal" in p["tags"]


def test_sensitive_skin_avoids_lactic_acid_and_flags_patch_test(dry_sensitive):
    r = build_routine(dry_sensitive, 3000, "dry")
    assert r["profile"] == {"type": "dry", "sensitive": True, "climate": "dry"}
    assert all(BY_ID[p["id"]].ingredient != "lactic_acid" for p in r["products"])
    assert "patch_test" in r["flags"]
    # spots on sensitive skin -> alpha arbutin rather than vitamin C
    assert any(BY_ID[p["id"]].ingredient == "alpha_arbutin" for p in r["products"])


def test_low_acne_score_recommends_dermatologist():
    r = build_routine(scores_from({"acne": 30, "oiliness": 60}), 1500, "humid")
    assert "see_dermatologist" in r["flags"]
    r2 = build_routine(scores_from({"acne": 55}), 1500, "humid")
    assert "see_dermatologist" not in r2["flags"]


def test_small_budget_lists_skipped_treatments(oily_acne):
    r = build_routine(oily_acne, 500, "humid")
    assert len([p for p in r["products"] if p["slot"] == "serum"]) <= 1
    assert r["skipped"], "treatments that don't fit should be listed as 'add later'"
    assert {s["reason"] for s in r["skipped"]} <= {"budget", "routine_cap"}
    assert all("label" in s for s in r["skipped"])


def test_bigger_budget_never_gets_fewer_treatments(oily_acne):
    counts = [len(build_routine(oily_acne, b, "humid")["products"]) for b in BUDGETS]
    assert counts == sorted(counts)


def test_serum_cap_per_budget():
    r = build_routine(scores_from(PROFILES["all_bad"]), 3000, "polluted")
    assert len([p for p in r["products"] if p["slot"] == "serum"]) <= 3


def test_vitamin_c_moves_niacinamide_to_night():
    s = scores_from(dict(oiliness=50, spots=40, moisture=80, acne=80, pores=80, redness=85, texture=85, dark_circles=85))
    r = build_routine(s, 3000, "humid")
    am_ids = [BY_ID[x["product_id"]].ingredient for x in r["am"]]
    pm_ids = [BY_ID[x["product_id"]].ingredient for x in r["pm"]]
    assert "vitamin_c" in am_ids
    assert "niacinamide" in pm_ids and "niacinamide" not in am_ids


def test_acids_alternate_nights():
    s = scores_from(dict(acne=45, texture=45, redness=85, moisture=80, oiliness=80, pores=80, dark_circles=85, spots=85))
    r = build_routine(s, 3000, "humid")
    sa = next(x for x in r["pm"] if BY_ID[x["product_id"]].ingredient == "salicylic_acid" and x["slot"] == "serum")
    assert "lactic" in sa["how"]["en"].lower()


def test_needs_ranked_by_severity(oily_acne):
    needs = ingredient_needs(oily_acne, skin_profile(oily_acne, "humid"))
    priorities = [n["priority"] for n in needs]
    assert priorities == sorted(priorities, reverse=True)
    assert needs[0]["ingredient"] in ("salicylic_acid", "niacinamide")


def test_climate_nudges():
    good = scores_from({k: 90 for k in KEYS})
    assert [n["ingredient"] for n in ingredient_needs(good, skin_profile(good, "polluted"))] == ["vitamin_c"]
    assert [n["ingredient"] for n in ingredient_needs(good, skin_profile(good, "dry"))] == ["hyaluronic_acid"]
    assert ingredient_needs(good, skin_profile(good, "humid")) == []


def test_skin_profile_types():
    assert skin_profile(scores_from({"oiliness": 50, "moisture": 50}), "humid")["type"] == "combination"
    assert skin_profile(scores_from({"oiliness": 70}), "humid")["type"] == "oily"  # watch + humid
    assert skin_profile(scores_from({"oiliness": 70}), "dry")["type"] == "normal"
    assert skin_profile(scores_from({"moisture": 70}), "dry")["type"] == "dry"


def test_bilingual_copy_everywhere(oily_acne):
    r = build_routine(oily_acne, 3000, "polluted")
    for step in r["am"] + r["pm"]:
        assert step["how"]["en"] and step["how"]["hi"]
        assert step["label"]["en"] and step["label"]["hi"]
    for n in r["notes"]:
        assert n["en"] and n["hi"]
    assert "approximate" in r["price_note"].lower()


@pytest.mark.parametrize("budget,climate", [(999, "humid"), (1500, "snowy")])
def test_invalid_inputs_raise(oily_acne, budget, climate):
    with pytest.raises(ValueError):
        build_routine(oily_acne, budget, climate)
