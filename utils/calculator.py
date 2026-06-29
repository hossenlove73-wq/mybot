from config import UNIT_PRICES

WASTE = 1.05

COEFFICIENTS = {
    "RC": {
        "RESIDENTIAL": (0.45, 2.80, 110, 0.32, 45),
        "COMMERCIAL":  (0.55, 3.40, 130, 0.38, 40),
        "OFFICE":      (0.50, 3.10, 120, 0.35, 42),
    },
    "STEEL": {
        "RESIDENTIAL": (0.25, 1.55, 45, 0.20, 55),
        "COMMERCIAL":  (0.30, 1.85, 55, 0.24, 50),
        "OFFICE":      (0.28, 1.70, 50, 0.22, 52),
    },
    "LBM": {
        "RESIDENTIAL": (0.15, 1.10, 18, 0.18, 110),
        "COMMERCIAL":  (0.18, 1.30, 22, 0.21, 100),
        "OFFICE":      (0.16, 1.20, 20, 0.19, 105),
    },
}


def calculate(floor_area, floors, skeleton, usage):
    total = floor_area * floors
    c, cem, reb, sand, brk = COEFFICIENTS[skeleton][usage]
    p = UNIT_PRICES

    concrete = total * c   * WASTE
    cement   = total * cem * WASTE
    rebar_kg = total * reb * WASTE
    sand_m3  = total * sand* WASTE
    bricks   = total * brk * WASTE

    return {
        "total_area": total,
        "concrete":   round(concrete, 1),
        "cement":     round(cement, 0),
        "rebar_ton":  round(rebar_kg / 1000, 2),
        "rebar_kg":   round(rebar_kg, 0),
        "sand":       round(sand_m3, 1),
        "bricks":     round(bricks),
        "cost_concrete": round(concrete  * p["concrete"], 0),
        "cost_cement":   round(cement    * p["cement"],   0),
        "cost_rebar":    round(rebar_kg  * p["rebar"],    0),
        "cost_sand":     round(sand_m3   * p["sand"],     0),
        "cost_bricks":   round(bricks    * p["brick"],    0),
        "total_cost":    round(
            concrete * p["concrete"] +
            cement   * p["cement"]   +
            rebar_kg * p["rebar"]    +
            sand_m3  * p["sand"]     +
            bricks   * p["brick"],   0),
    }
