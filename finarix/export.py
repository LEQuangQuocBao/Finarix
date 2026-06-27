import glob
import json
import os
import tempfile
import webbrowser
import zipfile

from finarix import i18n


def export_html(payload, year, month, is_bilan):
    field     = "reel" if is_bilan else "prevoir"
    mode_lbl  = i18n.t("html_bilan") if is_bilan else i18n.t("html_prevision")
    month_lbl = f"{i18n.months()[month]} {year}"

    def fmt(v):
        s = "-" if v < 0 else ""
        return f"{s}{abs(v):,.2f}&nbsp;€".replace(",", "&nbsp;")

    def color(v, invert=False):
        pos = v >= 0 if not invert else v <= 0
        return "#27AE60" if pos else "#E74C3C"

    rev  = sum(r[field] for r in payload["revenu"])
    fix  = sum(r[field] for r in payload["fixe"])
    var  = sum(r[field] for r in payload["variable"])
    dep  = fix + var
    epg  = rev - dep
    si   = payload["solde_initial"]
    sf   = si + epg

    cb = payload.get("compte_bancaire", payload.get("solde_initial", 0.0))
    actifs_list = payload.get("actifs", [])
    if isinstance(actifs_list, dict):  # legacy format
        actifs_list = [{"label": k, "montant": v} for k, v in actifs_list.items()]
    ta     = cb + sum(a["montant"] for a in actifs_list)
    dettes = payload.get("dettes", [])
    td     = sum(d["montant"] for d in dettes)
    pat    = ta - td

    ecart_html = ""
    if is_bilan:
        ecart      = cb - sf
        ecart_col  = "#27AE60" if abs(ecart) < 0.005 else "#E74C3C"
        ecart_html = (
            f'<span>{i18n.t("html_cb")} '
            f'<b style="color:{color(cb)}">{fmt(cb)}</b></span>'
            f'<span>{i18n.t("html_cb_ecart")} '
            f'<b style="color:{ecart_col}">{fmt(ecart)}</b></span>'
        )

    mode_bg = "#1A5276" if is_bilan else "#784212"

    def rows_html(items):
        out = ""
        for r in items:
            v = r.get(field, 0)
            out += (f"<tr><td>{r['label']}</td>"
                    f"<td style='text-align:right'>{fmt(v)}</td></tr>\n")
        return out

    note_html = ""
    note_val  = payload.get("note", "")
    if note_val:
        note_html = (f"<h3>{i18n.t('html_notes')}</h3>"
                     f"<p style='white-space:pre-wrap'>{note_val}</p>")

    cb_row = (f"<tr style='background:#EBF5FB'>"
              f"<td><b>{i18n.t('html_cb')}</b></td>"
              f"<td style='text-align:right'><b>{fmt(cb)}</b></td></tr>")
    actifs_rows = cb_row + "".join(
        f"<tr><td>{a['label']}</td>"
        f"<td style='text-align:right'>{fmt(a['montant'])}</td></tr>"
        for a in actifs_list)
    dettes_rows = "".join(
        f"<tr><td>{d['label']}</td>"
        f"<td style='text-align:right'>{fmt(d['montant'])}</td></tr>"
        for d in dettes)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Finarix {month_lbl}</title>
<style>
  body{{font-family:'Segoe UI',sans-serif;max-width:720px;margin:0 auto;padding:20px;color:#222}}
  h1{{background:#1E2D3D;color:#fff;padding:12px 20px;border-radius:4px;display:flex;align-items:center;gap:14px}}
  .badge{{font-size:11px;padding:3px 12px;background:{mode_bg};border-radius:4px}}
  .summary{{display:flex;gap:10px;margin:16px 0}}
  .card{{flex:1;border:1px solid #ddd;border-radius:6px;padding:12px;text-align:center}}
  .card .t{{color:#888;font-size:12px;margin-bottom:4px}}
  .card .v{{font-size:18px;font-weight:700}}
  .solde-bar{{background:#EBF5FB;padding:10px 14px;border-radius:4px;margin:10px 0;display:flex;gap:30px}}
  .solde-bar span{{font-size:13px;color:#555}} .solde-bar b{{font-size:15px}}
  h3{{border-left:4px solid #1A5276;padding-left:10px;font-size:14px;margin-top:22px}}
  h3.fixe{{border-color:#145A32}} h3.var{{border-color:#784212}} h3.pat{{border-color:#17202A}}
  table{{width:100%;border-collapse:collapse;margin-bottom:6px;font-size:13px}}
  tr:nth-child(odd){{background:#f9f9f9}}
  td{{padding:6px 10px}}
  .tot td{{font-weight:700;border-top:2px solid #ddd}}
  .pat-box{{border:1px solid #ddd;border-radius:6px;padding:12px;margin:12px 0}}
  .pat-net{{font-size:15px;font-weight:700;margin-top:8px}}
  @media print{{body{{max-width:100%}}}}
</style></head><body>
<h1>Finarix — {month_lbl} <span class="badge">{mode_lbl}</span></h1>

<div class="summary">
  <div class="card"><div class="t">{i18n.t('html_revenus')}</div>
    <div class="v" style="color:{color(rev)}">{fmt(rev)}</div></div>
  <div class="card"><div class="t">{i18n.t('html_depenses')}</div>
    <div class="v" style="color:{color(dep, invert=True)}">{fmt(dep)}</div></div>
  <div class="card"><div class="t">{i18n.t('html_epargne')}</div>
    <div class="v" style="color:{color(epg)}">{fmt(epg)}</div></div>
</div>

<div class="solde-bar">
  <span>{i18n.t('html_solde_debut')} <b style="color:{color(si)}">{fmt(si)}</b></span>
  <span>{i18n.t('html_solde_fin')} <b style="color:{color(sf)}">{fmt(sf)}</b></span>
  {ecart_html}
</div>

<div class="pat-box">
  <h3 class="pat" style="margin-top:0">{i18n.t('html_patrimoine')}</h3>
  <table>{actifs_rows}
    <tr class="tot"><td>{i18n.t('html_total_actifs')}</td><td style="text-align:right;color:{color(ta)}">{fmt(ta)}</td></tr>
  </table>
  <table>{dettes_rows}
    <tr class="tot"><td>{i18n.t('html_total_dettes')}</td><td style="text-align:right;color:#E74C3C">{fmt(td)}</td></tr>
  </table>
  <div class="pat-net" style="color:{color(pat)}">{i18n.t('html_pat_net')} {fmt(pat)}</div>
</div>

<h3>{i18n.t('html_sec_revenu')}</h3>
<table>{rows_html(payload['revenu'])}
<tr class="tot"><td>{i18n.t('html_total')}</td><td style="text-align:right">{fmt(rev)}</td></tr></table>

<h3 class="fixe">{i18n.t('html_sec_fixe')}</h3>
<table>{rows_html(payload['fixe'])}
<tr class="tot"><td>{i18n.t('html_total')}</td><td style="text-align:right">{fmt(fix)}</td></tr></table>

<h3 class="var">{i18n.t('html_sec_variable')}</h3>
<table>{rows_html(payload['variable'])}
<tr class="tot"><td>{i18n.t('html_total')}</td><td style="text-align:right">{fmt(var)}</td></tr></table>

{note_html}
<p style="color:#bbb;font-size:11px;margin-top:40px">Finarix</p>
</body></html>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html',
                                     delete=False, encoding='utf-8') as f:
        f.write(html)
        tmp = f.name
    webbrowser.open(f"file:///{tmp.replace(os.sep, '/')}")


def export_data_zip(key: bytes, data_directory: str, save_path: str) -> int:
    """Export all month files as decrypted JSON inside a ZIP. Returns file count."""
    from cryptography.fernet import Fernet, InvalidToken

    fernet = Fernet(key)
    count  = 0
    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(glob.glob(os.path.join(data_directory, "*.json"))):
            with open(path, 'rb') as f:
                raw = f.read()
            try:
                plain = fernet.decrypt(raw)
            except InvalidToken:
                plain = raw  # already plaintext (legacy)
            try:
                json.loads(plain)  # validate before including
            except Exception:
                continue
            zf.writestr(os.path.basename(path), plain)
            count += 1
    return count


def import_data_zip(key: bytes, zip_path: str, data_directory: str) -> int:
    """Import month files from a ZIP, encrypt them, and save. Returns file count."""
    from cryptography.fernet import Fernet

    fernet = Fernet(key)
    count  = 0
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.endswith('.json'):
                continue
            plain = zf.read(name)
            try:
                json.loads(plain)  # validate JSON
            except Exception:
                continue
            encrypted = fernet.encrypt(plain)
            dest = os.path.join(data_directory, os.path.basename(name))
            with open(dest, 'wb') as f:
                f.write(encrypted)
            count += 1
    return count
