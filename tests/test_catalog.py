from app.catalog import CATALOG, PRICE_NOTE


def test_catalog_ids_unique_and_prices_sane():
    ids = [p.id for p in CATALOG]
    assert len(ids) == len(set(ids))
    for p in CATALOG:
        assert 100 <= p.mrp <= 2000, p
        assert 1 <= p.months <= 6, p
        assert p.slot in {"cleanser", "moisturizer", "sunscreen", "serum", "eye"}


def test_every_sunscreen_is_spf50_pa4():
    for p in CATALOG:
        if p.slot == "sunscreen":
            assert "SPF 50" in p.name and "PA++++" in p.name


def test_product_dict_has_search_link_and_monthly():
    d = CATALOG[0].to_dict()
    assert d["search_url"].startswith("https://www.amazon.in/s?k=")
    assert d["monthly"] == round(CATALOG[0].mrp / CATALOG[0].months)


def test_price_note_says_approximate():
    assert "approximate" in PRICE_NOTE.lower()
