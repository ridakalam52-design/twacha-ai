from app.concerns import ACTION_TO_CONCERN, CONCERNS, COPY, actions_for, level_for, normalize_output, report_card

# Shape copied from the docs' format=json success example (HD, region-aware).
DOCS_HD_OUTPUT = [
    {"type": "hd_pore", "region": "whole", "raw_score": 35.2, "ui_score": 35, "mask_urls": ["https://x/hd_pore_whole.jpg"]},
    {"type": "hd_pore", "region": "forehead", "raw_score": 30, "ui_score": 30, "mask_urls": ["https://x/f.jpg"]},
    {"type": "hd_pore", "region": "nose", "raw_score": 45.7, "ui_score": 46, "mask_urls": ["https://x/n.jpg"]},
    {"type": "hd_acne", "region": "whole", "raw_score": 12.5, "ui_score": 13, "mask_urls": ["https://x/acne.jpg"]},
    {"type": "hd_moisture", "raw_score": 80.2, "ui_score": 78, "mask_urls": []},
    {"type": "hd_skin_type", "region": "whole", "skin_type": "Combination", "mask_urls": []},
    {"type": "skin_age", "score": 29},
    {"type": "all", "score": 28.5},
    {"type": "resize_image", "mask_urls": ["https://x/resized.jpg"]},
]


def test_sd_and_hd_actions_never_mix():
    sd, hd = actions_for("sd"), actions_for("hd")
    assert len(sd) == len(hd) == 8
    assert all(not a.startswith("hd_") for a in sd)
    assert all(a.startswith("hd_") for a in hd)
    assert "dark_circle_v2" in sd and "hd_dark_circle" in hd  # SD dark-circle action name per docs


def test_action_map_round_trips():
    for key, (sd, hd) in CONCERNS.items():
        assert ACTION_TO_CONCERN[sd] == key == ACTION_TO_CONCERN[hd]


def test_level_thresholds():
    assert level_for(59.9) == "focus"
    assert level_for(60) == "watch"
    assert level_for(74.9) == "watch"
    assert level_for(75) == "good"


def test_normalize_docs_example():
    n = normalize_output(DOCS_HD_OUTPUT)
    assert set(n["scores"]) == {"pores", "acne", "moisture"}
    assert n["scores"]["pores"]["ui_score"] == 35
    assert n["scores"]["pores"]["regions"] == {"forehead": 30, "nose": 46}
    assert n["scores"]["pores"]["mask_url"] == "https://x/hd_pore_whole.jpg"
    assert n["scores"]["acne"]["level"] == "focus"
    assert n["scores"]["moisture"]["level"] == "good"  # entry without region counts as whole
    assert n["skin_age"] == 29
    assert n["overall"] == 28  # round(28.5) -> banker's rounding gives 28


def test_overall_falls_back_to_mean():
    n = normalize_output([{"type": "acne", "ui_score": 80, "raw_score": 80}, {"type": "pore", "ui_score": 60, "raw_score": 60}])
    assert n["overall"] == 70
    assert n["skin_age"] is None


def test_report_card_sorted_worst_first_and_bilingual():
    rows = report_card(normalize_output(DOCS_HD_OUTPUT))
    assert [r["key"] for r in rows] == ["acne", "pores", "moisture"]
    for r in rows:
        assert r["explain"]["en"] and r["explain"]["hi"]
        assert r["label"]["hi"]


def test_copy_complete_for_every_concern():
    for key in CONCERNS:
        for lvl in ("good", "watch", "focus"):
            assert COPY[key][lvl]["en"] and COPY[key][lvl]["hi"]
    assert "dermatologist" in COPY["acne"]["focus"]["en"]
