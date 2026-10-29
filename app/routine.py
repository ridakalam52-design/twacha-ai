"""Deterministic AM/PM routine engine + budget fitting.

Same scores + budget + climate always produce the same routine. No LLM, no randomness.

1. Skin profile from oiliness / moisture / redness (+ climate nudge).
2. Concerns that are not "good" become ingredient needs, ranked by severity (100 - raw).
3. Core steps (cleanser, moisturiser, SPF 50 PA++++ sunscreen) are always included,
   cheapest suitable product first so they always fit.
4. Treatments are added in priority order while the MONTHLY cost (MRP / months a unit
   lasts) stays within the budget. Anything that doesn't fit is listed as "add later".
5. Leftover budget upgrades core products to better-matched picks.
"""
from __future__ import annotations

from typing import Any

from .catalog import PRICE_NOTE, Product, products_for

BUDGETS = (500, 1500, 3000)
CLIMATES = ("humid", "dry", "polluted")
MAX_SERUMS = {500: 1, 1500: 2, 3000: 3}
SEE_DERM_ACNE_RAW = 40  # very low acne score -> recommend a dermatologist

CLIMATE_TAG = {"humid": "humid", "dry": "dry_climate", "polluted": "polluted"}

INGREDIENTS: dict[str, dict[str, Any]] = {
    "salicylic_acid": {
        "label": {"en": "Salicylic acid (BHA)", "hi": "सैलिसिलिक एसिड (BHA)"},
        "concerns": ("acne", "pores"), "when": "pm",
        "how": {"en": "Thin layer on clean, dry skin. Start 3 nights a week.", "hi": "साफ़, सूखी त्वचा पर पतली परत। शुरुआत हफ़्ते में 3 रात से करें।"},
    },
    "niacinamide": {
        "label": {"en": "Niacinamide", "hi": "नियासिनामाइड"},
        "concerns": ("oiliness", "pores", "spots"), "when": "am",
        "how": {"en": "2-3 drops before moisturiser.", "hi": "मॉइस्चराइज़र से पहले 2-3 बूंदें।"},
    },
    "vitamin_c": {
        "label": {"en": "Vitamin C", "hi": "विटामिन C"},
        "concerns": ("spots",), "when": "am",
        "how": {"en": "3-4 drops in the morning, always followed by sunscreen.", "hi": "सुबह 3-4 बूंदें, उसके बाद हमेशा सनस्क्रीन।"},
    },
    "alpha_arbutin": {
        "label": {"en": "Alpha arbutin", "hi": "अल्फ़ा आर्बुटिन"},
        "concerns": ("spots",), "when": "pm",
        "how": {"en": "2-3 drops at night on spots and uneven areas.", "hi": "रात में धब्बों पर 2-3 बूंदें।"},
    },
    "lactic_acid": {
        "label": {"en": "Lactic acid (gentle AHA)", "hi": "लैक्टिक एसिड (हल्का AHA)"},
        "concerns": ("texture",), "when": "pm",
        "how": {"en": "2 nights a week, never on the same night as salicylic acid.", "hi": "हफ़्ते में 2 रात, सैलिसिलिक एसिड वाली रात नहीं।"},
    },
    "hyaluronic_acid": {
        "label": {"en": "Hyaluronic acid", "hi": "हायल्यूरोनिक एसिड"},
        "concerns": ("moisture",), "when": "pm",
        "how": {"en": "On slightly damp skin, then seal with moisturiser.", "hi": "हल्की गीली त्वचा पर लगाएं, फिर मॉइस्चराइज़र।"},
    },
    "caffeine": {
        "label": {"en": "Caffeine eye cream", "hi": "कैफ़ीन आई क्रीम"},
        "concerns": ("dark_circles",), "when": "pm",
        "how": {"en": "Pat a rice-grain amount under each eye.", "hi": "चावल के दाने जितनी मात्रा आँखों के नीचे थपथपाएं।"},
    },
}

SLOT_LABEL = {
    "cleanser": {"en": "Cleanser", "hi": "क्लींज़र"},
    "serum": {"en": "Treatment", "hi": "ट्रीटमेंट"},
    "eye": {"en": "Eye care", "hi": "आँखों की देखभाल"},
    "moisturizer": {"en": "Moisturiser", "hi": "मॉइस्चराइज़र"},
    "sunscreen": {"en": "Sunscreen SPF 50 PA++++", "hi": "सनस्क्रीन SPF 50 PA++++"},
}

CORE_HOW = {
    "cleanser": {"en": "Massage on damp skin for 30 seconds, rinse.", "hi": "गीली त्वचा पर 30 सेकंड मालिश करें, धो लें।"},
    "moisturizer": {"en": "A pea-sized amount over face and neck.", "hi": "मटर के दाने जितना चेहरे और गर्दन पर।"},
    "sunscreen": {"en": "Two finger-lengths for face and neck, 15 min before going out. Reapply every 2-3 hours outdoors.", "hi": "चेहरे और गर्दन के लिए दो उंगली भर, बाहर जाने से 15 मिनट पहले। बाहर हों तो हर 2-3 घंटे में दोबारा लगाएं।"},
}


def _bi(en: str, hi: str) -> dict[str, str]:
    return {"en": en, "hi": hi}


def skin_profile(scores: dict[str, dict[str, Any]], climate: str) -> dict[str, Any]:
    def lvl(key: str) -> str:
        return scores.get(key, {}).get("level", "good")

    oily = lvl("oiliness") == "focus" or (lvl("oiliness") == "watch" and climate == "humid")
    dry = lvl("moisture") == "focus" or (lvl("moisture") == "watch" and climate == "dry")
    if oily and dry:
        kind = "combination"
    elif oily:
        kind = "oily"
    elif dry:
        kind = "dry"
    else:
        kind = "normal"
    return {"type": kind, "sensitive": lvl("redness") == "focus", "climate": climate}


def ingredient_needs(scores: dict[str, dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Ingredient needs ranked by summed severity (100 - raw) of the concerns they treat."""
    sev: dict[str, float] = {}
    because: dict[str, list[str]] = {}

    def add(ing: str, concern: str, amount: float) -> None:
        sev[ing] = sev.get(ing, 0.0) + amount
        because.setdefault(ing, [])
        if concern not in because[ing]:
            because[ing].append(concern)

    sensitive = profile["sensitive"]
    for key, s in scores.items():
        if s.get("level", "good") == "good":
            continue
        weight = 100 - float(s["raw_score"])
        if key == "acne":
            add("salicylic_acid", key, weight)
        elif key == "oiliness":
            add("niacinamide", key, weight)
        elif key == "pores":
            add("niacinamide", key, weight * 0.6)
            add("salicylic_acid", key, weight * 0.4)
        elif key == "spots":
            add("alpha_arbutin" if sensitive else "vitamin_c", key, weight)
        elif key == "texture":
            if not sensitive:  # skip acids on a stressed, red barrier
                add("lactic_acid", key, weight)
        elif key == "moisture":
            add("hyaluronic_acid", key, weight)
        elif key == "dark_circles":
            add("caffeine", key, weight * 0.8)  # cosmetic, lower priority
        # redness: handled by soothing core products, no extra active

    # Climate nudges (small, so real concerns still lead).
    if profile["climate"] == "polluted" and not sensitive:
        add("vitamin_c", "pollution", 12)
    if profile["climate"] == "dry":
        add("hyaluronic_acid", "dry_climate", 12)

    needs = [{"ingredient": i, "priority": round(p, 1), "because": because[i]} for i, p in sev.items()]
    needs.sort(key=lambda n: (-n["priority"], n["ingredient"]))
    return needs


def _fit(p: Product, profile: dict[str, Any], slot_pref: str | None = None) -> int:
    kind = profile["type"]
    want = {"combination": {"normal", "oily"}, "normal": {"normal"}}.get(kind, {kind})
    score = 2 * len(want & set(p.tags))
    if CLIMATE_TAG[profile["climate"]] in p.tags:
        score += 1
    if profile["sensitive"]:
        score += 2 if "sensitive" in p.tags else -1
    if slot_pref and p.ingredient == slot_pref:
        score += 2
    return score


def _suitable(p: Product, profile: dict[str, Any]) -> bool:
    kind = profile["type"]
    want = {"combination": {"normal", "oily"}}.get(kind, {kind})
    return bool(want & set(p.tags)) or "normal" in p.tags


def _ranked(slot: str, profile: dict[str, Any], ingredient: str | None = None, pref: str | None = None) -> list[Product]:
    cands = [p for p in products_for(slot, ingredient) if _suitable(p, profile)] or products_for(slot, ingredient)
    return sorted(cands, key=lambda p: (-_fit(p, profile, pref), p.monthly, p.id))


def _cleanser_pref(scores: dict[str, Any], profile: dict[str, Any]) -> str | None:
    if profile["sensitive"] or profile["type"] == "dry":
        return "gentle"
    acne = scores.get("acne", {}).get("level", "good")
    if acne != "good" or profile["type"] in ("oily", "combination"):
        return "salicylic_acid"
    return None


def _moisturizer_pref(profile: dict[str, Any]) -> str | None:
    if profile["sensitive"]:
        return "soothing"
    if profile["type"] == "dry" or profile["climate"] == "dry":
        return "ceramides"
    return None


def build_routine(scores: dict[str, dict[str, Any]], budget: int, climate: str) -> dict[str, Any]:
    if budget not in BUDGETS:
        raise ValueError(f"budget must be one of {BUDGETS}")
    if climate not in CLIMATES:
        raise ValueError(f"climate must be one of {CLIMATES}")

    profile = skin_profile(scores, climate)
    needs = ingredient_needs(scores, profile)
    prefs = {"cleanser": _cleanser_pref(scores, profile), "moisturizer": _moisturizer_pref(profile), "sunscreen": None}

    # 1) Core: cheapest suitable first, so the essentials always fit.
    core: dict[str, Product] = {}
    for slot in ("sunscreen", "cleanser", "moisturizer"):
        ranked = _ranked(slot, profile, pref=prefs[slot])
        core[slot] = min(ranked, key=lambda p: (p.monthly, p.id))

    def total(items: list[Product]) -> float:
        return sum(p.monthly for p in items)

    chosen: list[Product] = list(core.values())
    treatments: list[tuple[Product, dict[str, Any]]] = []
    skipped: list[dict[str, Any]] = []
    serum_cap = MAX_SERUMS[budget]

    # 2) Treatments by priority.
    for need in needs:
        ing = need["ingredient"]
        slot = "eye" if ing == "caffeine" else "serum"
        n_serums = sum(1 for p, _ in treatments if p.slot == "serum")
        if slot == "serum" and n_serums >= serum_cap:
            skipped.append({**need, "reason": "routine_cap"})
            continue
        pick = None
        for cand in sorted(_ranked(slot, profile, ingredient=ing), key=lambda p: (p.monthly, p.id)):
            if total(chosen) + cand.monthly <= budget:
                pick = cand
                break
        if pick is None:
            skipped.append({**need, "reason": "budget"})
            continue
        chosen.append(pick)
        treatments.append((pick, need))

    # 3) Upgrade core picks with leftover budget (best fit first).
    for slot in ("sunscreen", "moisturizer", "cleanser"):
        current = core[slot]
        for cand in _ranked(slot, profile, pref=prefs[slot]):
            if _fit(cand, profile, prefs[slot]) <= _fit(current, profile, prefs[slot]):
                break
            if total(chosen) - current.monthly + cand.monthly <= budget:
                chosen[chosen.index(current)] = cand
                core[slot] = cand
                break

    am, pm = _assemble_steps(core, treatments)
    monthly = round(total(chosen))
    flags = []
    acne = scores.get("acne")
    if acne and float(acne["raw_score"]) < SEE_DERM_ACNE_RAW:
        flags.append("see_dermatologist")
    if profile["sensitive"]:
        flags.append("patch_test")

    products = []
    for p in chosen:
        d = p.to_dict()
        need = next((n for t, n in treatments if t.id == p.id), None)
        d["for"] = need["because"] if need else [p.slot]
        products.append(d)

    return {
        "profile": profile,
        "budget": budget,
        "monthly_total": monthly,
        "upfront_total": sum(p.mrp for p in chosen),
        "within_budget": monthly <= budget,
        "am": am,
        "pm": pm,
        "products": products,
        "needs": needs,
        "skipped": [
            {**s, "label": INGREDIENTS[s["ingredient"]]["label"]} for s in skipped
        ],
        "notes": _notes(profile),
        "flags": flags,
        "price_note": PRICE_NOTE,
    }


def _step(slot: str, p: Product, how: dict[str, str], ingredient: str | None = None) -> dict[str, Any]:
    label = INGREDIENTS[ingredient]["label"] if ingredient else SLOT_LABEL[slot]
    return {"slot": slot, "label": label, "product_id": p.id, "product": f"{p.brand} {p.name}", "how": how}


def _assemble_steps(core: dict[str, Product], treatments: list[tuple[Product, dict[str, Any]]]):
    am = [_step("cleanser", core["cleanser"], CORE_HOW["cleanser"])]
    pm = [_step("cleanser", core["cleanser"], CORE_HOW["cleanser"])]
    ings = {p.ingredient for p, _ in treatments}
    for p, need in treatments:
        ing = need["ingredient"]
        meta = INGREDIENTS[ing]
        when = meta["when"]
        how = dict(meta["how"])
        # Niacinamide moves to PM when vitamin C already owns the morning.
        if ing == "niacinamide" and "vitamin_c" in ings:
            when = "pm"
        if ing == "salicylic_acid" and "lactic_acid" in ings:
            how = _bi("Alternate nights with lactic acid (e.g. Mon/Wed/Fri).", "लैक्टिक एसिड के साथ बारी-बारी रातों में (जैसे सोम/बुध/शुक्र)।")
        (am if when == "am" else pm).append(_step(p.slot, p, how, ing))
    am.append(_step("moisturizer", core["moisturizer"], CORE_HOW["moisturizer"]))
    pm.append(_step("moisturizer", core["moisturizer"], CORE_HOW["moisturizer"]))
    am.append(_step("sunscreen", core["sunscreen"], CORE_HOW["sunscreen"]))
    return am, pm


def _notes(profile: dict[str, Any]) -> list[dict[str, str]]:
    notes = [_bi(
        "Sunscreen every morning, even indoors or on cloudy days. It does more for spots and ageing than any serum.",
        "हर सुबह सनस्क्रीन लगाएं, घर के अंदर या बादल वाले दिन भी। धब्बों और उम्र के असर के लिए यह किसी भी सीरम से ज़्यादा असरदार है।",
    ), _bi(
        "Introduce one new product at a time, a week apart, and patch-test on the jawline first.",
        "एक बार में एक ही नया प्रोडक्ट शुरू करें, एक हफ़्ते के अंतर पर, और पहले जबड़े के पास पैच टेस्ट करें।",
    )]
    climate = profile["climate"]
    if climate == "humid":
        notes.append(_bi("Humid weather: stick to gel textures and blot instead of re-washing midday.",
                         "उमस वाला मौसम: जेल वाले प्रोडक्ट चुनें और दिन में बार-बार धोने के बजाय ब्लॉटिंग पेपर इस्तेमाल करें।"))
    elif climate == "dry":
        notes.append(_bi("Dry climate: apply moisturiser on damp skin and skip very hot water.",
                         "सूखा मौसम: मॉइस्चराइज़र हल्की गीली त्वचा पर लगाएं और बहुत गर्म पानी से बचें।"))
    else:
        notes.append(_bi("Polluted city: cleanse properly every night to remove sunscreen, dust and smog.",
                         "प्रदूषित शहर: रोज़ रात अच्छे से चेहरा साफ़ करें ताकि सनस्क्रीन, धूल और धुआं हट जाए।"))
    return notes
