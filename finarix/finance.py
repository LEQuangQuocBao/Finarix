def to_float(s):
    try:
        return float(str(s).replace(',', '.').strip())
    except (ValueError, TypeError):
        return 0.0


def compute_solde_final(payload, use_reel):
    f = "reel" if use_reel else "prevoir"
    rev = sum(r[f] for r in payload["revenu"])
    dep = (sum(r[f] for r in payload["fixe"]) +
           sum(r[f] for r in payload["variable"]))
    return round(payload["solde_initial"] + rev - dep, 2)
