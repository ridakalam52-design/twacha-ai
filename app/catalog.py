"""Curated catalog of widely sold Indian-market skincare products.

Prices are APPROXIMATE MRPs in INR (late 2025 / 2026 listings) and change often;
the UI says so. `months` is a conservative estimate of how long one unit lasts
with the routine's daily use (sunscreen used generously, ~1 g per morning).

Tags describe who a product suits:
  oily | dry | normal | sensitive   (skin profile)
  humid | dry_climate | polluted    (climate fit, optional)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from urllib.parse import quote_plus

PRICE_NOTE = "Prices are approximate MRPs and may differ by seller, size and offers."


@dataclass(frozen=True)
class Product:
    id: str
    brand: str
    name: str
    slot: str          # cleanser | moisturizer | sunscreen | serum | eye
    ingredient: str    # key active, used by the routine engine
    size: str
    mrp: int           # approx MRP in INR
    months: float      # approx months one unit lasts
    tags: tuple[str, ...] = ()

    @property
    def monthly(self) -> float:
        return self.mrp / self.months

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tags"] = list(self.tags)
        d["monthly"] = round(self.monthly)
        d["search_url"] = "https://www.amazon.in/s?k=" + quote_plus(f"{self.brand} {self.name}")
        return d


CATALOG: list[Product] = [
    # --- Cleansers ------------------------------------------------------
    Product("c_min_sa", "Minimalist", "Salicylic Acid + LHA 2% Cleanser", "cleanser", "salicylic_acid", "100 ml", 299, 3, ("oily", "normal", "humid", "polluted")),
    Product("c_dco_sa", "The Derma Co", "1% Salicylic Acid Gel Face Wash", "cleanser", "salicylic_acid", "100 ml", 349, 3, ("oily", "humid", "polluted")),
    Product("c_plum_gt", "Plum", "Green Tea Pore Cleansing Face Wash", "cleanser", "green_tea", "75 ml", 345, 2.5, ("oily", "normal", "humid")),
    Product("c_cet_gentle", "Cetaphil", "Gentle Skin Cleanser", "cleanser", "gentle", "125 ml", 449, 3.5, ("dry", "normal", "sensitive", "dry_climate", "polluted")),
    Product("c_cet_oily", "Cetaphil", "Oily Skin Cleanser", "cleanser", "gentle_foam", "125 ml", 549, 3.5, ("oily", "sensitive", "humid")),
    Product("c_simple", "Simple", "Kind to Skin Refreshing Facial Wash", "cleanser", "gentle", "150 ml", 375, 4, ("normal", "sensitive", "dry")),
    # --- Moisturisers ---------------------------------------------------
    Product("m_ponds_gel", "Pond's", "Super Light Gel Oil-Free Moisturiser", "moisturizer", "hyaluronic_acid", "100 g", 349, 4, ("oily", "normal", "humid")),
    Product("m_min_b5", "Minimalist", "Vitamin B5 10% Moisturizer", "moisturizer", "panthenol", "50 g", 349, 2, ("oily", "normal", "humid", "sensitive")),
    Product("m_plum_gt", "Plum", "Green Tea Oil-Free Moisturizer", "moisturizer", "green_tea", "50 ml", 375, 2, ("oily", "humid")),
    Product("m_min_sepi", "Minimalist", "Sepicalm 3% + Oat Moisturizer", "moisturizer", "soothing", "50 ml", 349, 2, ("sensitive", "normal", "dry", "polluted")),
    Product("m_lakme_peach", "Lakmé", "Peach Milk Moisturiser", "moisturizer", "milk_peptides", "120 ml", 225, 4, ("normal", "dry", "dry_climate")),
    Product("m_reequil_cer", "Re'equil", "Ceramide & Hyaluronic Acid Moisturiser", "moisturizer", "ceramides", "100 g", 595, 4, ("dry", "normal", "sensitive", "dry_climate", "polluted")),
    Product("m_cet_cream", "Cetaphil", "Moisturising Cream", "moisturizer", "ceramides", "80 g", 499, 2.5, ("dry", "sensitive", "dry_climate")),
    Product("m_dk_vitc", "Dot & Key", "Vitamin C + E Super Bright Moisturizer", "moisturizer", "vitamin_c", "60 ml", 445, 2, ("normal", "oily", "polluted")),
    # --- Sunscreens (all SPF 50 PA++++) ---------------------------------
    Product("s_min_spf50", "Minimalist", "SPF 50 PA++++ Multi-Vitamin Sunscreen", "sunscreen", "spf50", "50 g", 399, 1.5, ("oily", "normal", "dry", "humid", "polluted")),
    Product("s_dco_aqua", "The Derma Co", "1% Hyaluronic Sunscreen Aqua Gel SPF 50 PA++++", "sunscreen", "spf50", "50 g", 499, 1.5, ("oily", "normal", "humid")),
    Product("s_dk_wm", "Dot & Key", "Watermelon Cooling Sunscreen SPF 50 PA++++", "sunscreen", "spf50", "50 g", 495, 1.5, ("oily", "normal", "humid")),
    Product("s_reequil", "Re'equil", "Oxybenzone & OMC Free Sunscreen SPF 50 PA++++", "sunscreen", "spf50", "50 g", 595, 1.5, ("dry", "normal", "sensitive", "dry_climate", "polluted")),
    # --- Treatment serums -----------------------------------------------
    Product("t_min_nia", "Minimalist", "Niacinamide 10% Face Serum", "serum", "niacinamide", "30 ml", 599, 3, ("oily", "normal")),
    Product("t_dco_nia", "The Derma Co", "10% Niacinamide Face Serum", "serum", "niacinamide", "30 ml", 599, 3, ("oily", "normal")),
    Product("t_min_sa", "Minimalist", "Salicylic Acid 2% Face Serum", "serum", "salicylic_acid", "30 ml", 549, 3.5, ("oily", "normal")),
    Product("t_min_vitc", "Minimalist", "Vitamin C 10% Face Serum", "serum", "vitamin_c", "30 ml", 699, 3, ("normal", "oily", "dry", "polluted")),
    Product("t_plum_vitc", "Plum", "15% Vitamin C Face Serum with Mandarin", "serum", "vitamin_c", "20 ml", 849, 2, ("normal", "oily", "polluted")),
    Product("t_min_aa", "Minimalist", "Alpha Arbutin 2% Face Serum", "serum", "alpha_arbutin", "30 ml", 549, 3, ("normal", "oily", "dry", "sensitive")),
    Product("t_min_ha", "Minimalist", "Hyaluronic + PGA 2% Face Serum", "serum", "hyaluronic_acid", "30 ml", 599, 3, ("dry", "normal", "sensitive", "dry_climate")),
    Product("t_min_la", "Minimalist", "Lactic Acid 5% + HA Exfoliating Serum", "serum", "lactic_acid", "30 ml", 599, 4, ("normal", "dry", "oily")),
    # --- Eye ------------------------------------------------------------
    Product("e_mcaf_coffee", "mCaffeine", "Coffee Under Eye Cream", "eye", "caffeine", "30 ml", 499, 3, ("normal", "oily", "dry")),
]

BY_ID = {p.id: p for p in CATALOG}


def products_for(slot: str, ingredient: str | None = None) -> list[Product]:
    return [p for p in CATALOG if p.slot == slot and (ingredient is None or p.ingredient == ingredient)]
