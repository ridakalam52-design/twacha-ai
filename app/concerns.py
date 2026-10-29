"""Skin concerns: YouCam action names, score normalisation and plain-language copy (EN + HI).

YouCam scores run 1-100 where HIGHER means healthier-looking skin for that concern
(docs: "A higher score indicates healthier and more aesthetically pleasing skin
condition"). `ui_score` is a friendlier calibrated value for display; `raw_score` is
the model's direct prediction. We display ui_score and rank priorities on raw_score.
"""
from __future__ import annotations

from typing import Any

# key -> (SD action, HD action). SD and HD actions can never be mixed in one task.
CONCERNS: dict[str, tuple[str, str]] = {
    "moisture": ("moisture", "hd_moisture"),
    "oiliness": ("oiliness", "hd_oiliness"),
    "acne": ("acne", "hd_acne"),
    "pores": ("pore", "hd_pore"),
    "redness": ("redness", "hd_redness"),
    "texture": ("texture", "hd_texture"),
    "dark_circles": ("dark_circle_v2", "hd_dark_circle"),
    "spots": ("age_spot", "hd_age_spot"),
}

ACTION_TO_CONCERN = {a: k for k, (sd, hd) in CONCERNS.items() for a in (sd, hd)}

# Priority thresholds on raw_score (1-100, higher = better).
FOCUS_BELOW = 60
WATCH_BELOW = 75


def actions_for(quality: str) -> list[str]:
    idx = 1 if quality == "hd" else 0
    return [pair[idx] for pair in CONCERNS.values()]


def level_for(raw: float) -> str:
    if raw < FOCUS_BELOW:
        return "focus"
    if raw < WATCH_BELOW:
        return "watch"
    return "good"


def normalize_output(output: list[dict[str, Any]]) -> dict[str, Any]:
    """Turn YouCam `results.output` into {scores: {concern: {...}}, overall, skin_age}.

    Region-aware actions (hd_pore, hd_acne, hd_texture, ...) return one entry per
    region; the `whole` region (or an entry without a region) is the headline.
    """
    scores: dict[str, dict[str, Any]] = {}
    regions: dict[str, dict[str, float]] = {}
    overall = skin_age = None
    for item in output:
        t = item.get("type")
        if t == "all":
            overall = item.get("score")
            continue
        if t == "skin_age":
            skin_age = item.get("score")
            continue
        key = ACTION_TO_CONCERN.get(t or "")
        if key is None or item.get("ui_score") is None:
            continue
        region = item.get("region") or "whole"
        if region != "whole":
            regions.setdefault(key, {})[region] = item.get("ui_score")
            continue
        raw = float(item.get("raw_score", item["ui_score"]))
        masks = item.get("mask_urls") or []
        scores[key] = {
            "ui_score": int(round(item["ui_score"])),
            "raw_score": round(raw, 1),
            "level": level_for(raw),
            "mask_url": masks[0] if masks else None,
        }
    for key, reg in regions.items():
        if key in scores:
            scores[key]["regions"] = reg
    if overall is None and scores:
        overall = sum(s["ui_score"] for s in scores.values()) / len(scores)
    return {
        "scores": scores,
        "overall": round(float(overall)) if overall is not None else None,
        "skin_age": skin_age,
    }


COPY: dict[str, dict[str, Any]] = {
    "moisture": {
        "label": {"en": "Hydration", "hi": "नमी"},
        "good": {"en": "Your skin looks well hydrated. Keep a daily moisturiser.", "hi": "आपकी त्वचा में अच्छी नमी है। रोज़ मॉइस्चराइज़र लगाते रहें।"},
        "watch": {"en": "Slightly thirsty skin. Hyaluronic acid and a good moisturiser help.", "hi": "त्वचा थोड़ी रूखी है। हायल्यूरोनिक एसिड और अच्छा मॉइस्चराइज़र मदद करेंगे।"},
        "focus": {"en": "Skin looks dehydrated, which can make it feel tight and dull. Ceramides and hyaluronic acid rebuild moisture.", "hi": "त्वचा में पानी की कमी दिख रही है, जिससे खिंचाव और रूखापन होता है। सेरामाइड और हायल्यूरोनिक एसिड नमी लौटाते हैं।"},
    },
    "oiliness": {
        "label": {"en": "Oil balance", "hi": "तेल संतुलन"},
        "good": {"en": "Oil levels look balanced.", "hi": "तेल का स्तर संतुलित है।"},
        "watch": {"en": "Some shine, likely on the T-zone. A gel moisturiser and niacinamide keep it in check.", "hi": "कुछ चमक है, शायद माथे और नाक पर। जेल मॉइस्चराइज़र और नियासिनामाइड इसे संभालते हैं।"},
        "focus": {"en": "Skin looks quite oily. Niacinamide helps regulate sebum; use light, oil-free textures.", "hi": "त्वचा काफ़ी तैलीय है। नियासिनामाइड तेल नियंत्रित करता है; हल्के, ऑयल-फ़्री प्रोडक्ट चुनें।"},
    },
    "acne": {
        "label": {"en": "Acne", "hi": "मुंहासे"},
        "good": {"en": "Very few visible breakouts.", "hi": "मुंहासे बहुत कम दिख रहे हैं।"},
        "watch": {"en": "A few breakouts. Salicylic acid keeps pores clear.", "hi": "कुछ मुंहासे हैं। सैलिसिलिक एसिड रोमछिद्रों को साफ़ रखता है।"},
        "focus": {"en": "Noticeable breakouts. Salicylic acid can help; if acne is painful, cystic or scarring, please see a dermatologist.", "hi": "मुंहासे साफ़ दिख रहे हैं। सैलिसिलिक एसिड मदद कर सकता है; अगर मुंहासे दर्द वाले, गहरे या दाग़ छोड़ रहे हों तो त्वचा विशेषज्ञ से ज़रूर मिलें।"},
    },
    "pores": {
        "label": {"en": "Pores", "hi": "रोमछिद्र"},
        "good": {"en": "Pores look refined.", "hi": "रोमछिद्र छोटे और साफ़ दिख रहे हैं।"},
        "watch": {"en": "Pores are a little visible, often around the nose. Niacinamide and BHA help.", "hi": "रोमछिद्र थोड़े दिखते हैं, अक्सर नाक के पास। नियासिनामाइड और BHA मदद करते हैं।"},
        "focus": {"en": "Enlarged-looking pores. Regular gentle exfoliation and niacinamide make them less visible.", "hi": "रोमछिद्र बड़े दिख रहे हैं। हल्का एक्सफ़ोलिएशन और नियासिनामाइड इन्हें कम दिखाते हैं।"},
    },
    "redness": {
        "label": {"en": "Redness", "hi": "लालिमा"},
        "good": {"en": "Little visible redness.", "hi": "लालिमा बहुत कम है।"},
        "watch": {"en": "Some redness. Keep products gentle and fragrance-free.", "hi": "थोड़ी लालिमा है। हल्के और बिना ख़ुशबू वाले प्रोडक्ट इस्तेमाल करें।"},
        "focus": {"en": "Visible redness, a sign of a stressed skin barrier. Go gentle, skip strong acids, and patch-test everything.", "hi": "लालिमा साफ़ दिख रही है, यानी त्वचा की सुरक्षा परत कमज़ोर है। तेज़ एसिड से बचें और हर प्रोडक्ट का पैच टेस्ट करें।"},
    },
    "texture": {
        "label": {"en": "Texture", "hi": "बनावट"},
        "good": {"en": "Skin texture looks smooth.", "hi": "त्वचा की बनावट मुलायम है।"},
        "watch": {"en": "Slightly uneven texture. A mild exfoliant a few nights a week helps.", "hi": "बनावट थोड़ी असमान है। हफ़्ते में कुछ रात हल्का एक्सफ़ोलिएंट मदद करेगा।"},
        "focus": {"en": "Rough or bumpy texture. Gentle exfoliation plus moisture smooths it over weeks.", "hi": "त्वचा खुरदरी है। हल्का एक्सफ़ोलिएशन और नमी कुछ हफ़्तों में इसे मुलायम करते हैं।"},
    },
    "dark_circles": {
        "label": {"en": "Dark circles", "hi": "काले घेरे"},
        "good": {"en": "Under-eyes look bright.", "hi": "आँखों के नीचे की त्वचा साफ़ है।"},
        "watch": {"en": "Mild dark circles. Sleep, sunscreen and a caffeine eye cream help.", "hi": "हल्के काले घेरे हैं। नींद, सनस्क्रीन और कैफ़ीन आई क्रीम मदद करते हैं।"},
        "focus": {"en": "Noticeable dark circles. Often genetic or sleep-related; an eye cream helps a little, rest helps more.", "hi": "काले घेरे साफ़ दिखते हैं। ये अक्सर आनुवंशिक या नींद से जुड़े होते हैं; आई क्रीम थोड़ी मदद करती है, आराम ज़्यादा।"},
    },
    "spots": {
        "label": {"en": "Spots & pigmentation", "hi": "दाग़-धब्बे"},
        "good": {"en": "Even tone with few spots.", "hi": "रंगत एक-सी है, धब्बे कम हैं।"},
        "watch": {"en": "Some spots or uneven tone. Daily SPF50 is the biggest fix; vitamin C helps.", "hi": "कुछ धब्बे या असमान रंगत है। रोज़ SPF50 सबसे ज़रूरी है; विटामिन C मदद करता है।"},
        "focus": {"en": "Visible pigmentation. Sunscreen every day plus vitamin C or alpha arbutin fades spots over 8-12 weeks.", "hi": "धब्बे साफ़ दिख रहे हैं। रोज़ सनस्क्रीन और विटामिन C या अल्फ़ा आर्बुटिन 8-12 हफ़्तों में धब्बे हल्के करते हैं।"},
    },
}


def report_card(normalized: dict[str, Any]) -> list[dict[str, Any]]:
    """Ordered report rows, worst (lowest raw score) first."""
    rows = []
    for key, s in normalized["scores"].items():
        copy = COPY[key]
        rows.append({
            "key": key,
            "label": copy["label"],
            "ui_score": s["ui_score"],
            "raw_score": s["raw_score"],
            "level": s["level"],
            "explain": copy[s["level"]],
            "mask_url": s.get("mask_url"),
            "regions": s.get("regions"),
        })
    rows.sort(key=lambda r: (r["raw_score"], r["key"]))
    return rows
