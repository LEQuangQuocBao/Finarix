import copy
import tkinter as tk

from finarix.config import (
    BG, CARD_BG, LOCK_BG, LOCK_FG, HDR_FG,
    GREEN, RED, MONTHS_FR, DEFAULT_DATA,
)
from finarix.storage import load_month_file, save_month_file, next_ym, prev_ym
from finarix.finance import to_float, compute_solde_final
from finarix import export
from finarix.dialogs.forward import ApplyForwardDialog


class AppLogicMixin:

    # ── predicates ────────────────────────────────────────────────────────────

    def _is_bilan(self):
        return (self.view_year, self.view_month) < (self._today.year, self._today.month)

    def _is_locked(self):
        return self._is_bilan() and not self._bilan_editing

    # ── data collection ───────────────────────────────────────────────────────

    def _collect(self, key):
        return [{"label":   r["label"].get(),
                 "prevoir": to_float(r["prevoir"].get()),
                 "reel":    to_float(r["reel"].get())}
                for r in self._row_widgets[key]]

    def _collect_actifs(self):
        return {k: to_float(v.get()) for k, v in self._actifs_vars.items()}

    def _collect_dettes(self):
        return [{"label":   r["label"].get(),
                 "montant": to_float(r["montant"].get())}
                for r in self._dette_rows]

    def _get_note(self):
        if self._note_text is None:
            return ""
        try:
            return self._note_text.get("1.0", tk.END).strip()
        except Exception:
            return ""

    def _build_payload(self):
        return {
            "solde_initial": to_float(self._solde_var.get()),
            "actifs":        self._collect_actifs(),
            "dettes":        self._collect_dettes(),
            "revenu":        self._collect("revenu"),
            "fixe":          self._collect("fixe"),
            "variable":      self._collect("variable"),
            "note":          self._get_note(),
        }

    def _carry_balance(self, payload):
        solde_final = compute_solde_final(payload, use_reel=self._is_bilan())
        ny, nm = next_ym(self.view_year, self.view_month)
        nxt = load_month_file(ny, nm) or copy.deepcopy(DEFAULT_DATA)
        nxt["solde_initial"] = solde_final
        save_month_file(ny, nm, nxt)

    def _save_silent(self):
        payload = self._build_payload()
        save_month_file(self.view_year, self.view_month, payload)
        self._carry_balance(payload)

    # ── button actions ────────────────────────────────────────────────────────

    def _on_save_click(self):
        payload = self._build_payload()
        save_month_file(self.view_year, self.view_month, payload)
        self._carry_balance(payload)
        if self._is_bilan():
            self._bilan_editing = False
            self._load_month()
        else:
            ApplyForwardDialog(self, payload, self.view_year, self.view_month)

    def _on_modifier_click(self):
        data = self._build_payload()
        self._bilan_editing = True
        self._rebuild_body(data)
        self._update_solde_lock()
        self._update_buttons()
        self._recalculate()

    def _update_buttons(self):
        if self._is_locked():
            self._btn_save.pack_forget()
            self._btn_modifier.pack(side=tk.RIGHT, padx=12)
        else:
            self._btn_modifier.pack_forget()
            self._btn_save.pack(side=tk.RIGHT, padx=12)

    def _update_solde_lock(self):
        locked = self._is_locked()
        self._solde_entry.config(
            state=tk.DISABLED if locked else tk.NORMAL,
            bg=LOCK_BG if locked else CARD_BG,
            fg=LOCK_FG if locked else "#333",
            disabledbackground=LOCK_BG, disabledforeground=LOCK_FG)

    # ── navigation ────────────────────────────────────────────────────────────

    def _go_prev(self):
        self._bilan_editing = False
        self._save_silent()
        self.view_year, self.view_month = prev_ym(self.view_year, self.view_month)
        self._load_month()

    def _go_next(self):
        self._bilan_editing = False
        self._save_silent()
        self.view_year, self.view_month = next_ym(self.view_year, self.view_month)
        self._load_month()

    def _load_month(self):
        data = load_month_file(self.view_year, self.view_month) \
               or copy.deepcopy(DEFAULT_DATA)
        self._bilan_editing = False
        self._solde_var.set(f"{data.get('solde_initial', 0.0):.2f}")
        self._rebuild_body(data)
        self._update_solde_lock()
        self._update_header()
        self._update_buttons()
        self._recalculate()
        self._canvas.yview_moveto(0)

    # ── display ───────────────────────────────────────────────────────────────

    def _update_header(self):
        self._lbl_month.config(
            text=f"{MONTHS_FR[self.view_month]} {self.view_year}")
        if self._is_bilan():
            self._lbl_mode.config(text="  Bilan  ",     bg="#1A5276", fg=HDR_FG)
        else:
            self._lbl_mode.config(text="  Prévision  ", bg="#784212", fg=HDR_FG)

    def _recalculate(self):
        def totals(key):
            ps = rs = 0.0
            for r in self._row_widgets[key]:
                ps += to_float(r["prevoir"].get())
                rs += to_float(r["reel"].get())
            return ps, rs

        rev_p, rev_r = totals("revenu")
        fix_p, fix_r = totals("fixe")
        var_p, var_r = totals("variable")
        dep_p, dep_r = fix_p + var_p, fix_r + var_r
        epg_p, epg_r = rev_p - dep_p, rev_r - dep_r

        bilan      = self._is_bilan()
        solde_init = to_float(self._solde_var.get())
        rv, dv, ev = (rev_r, dep_r, epg_r) if bilan else (rev_p, dep_p, epg_p)

        def fmt(v):
            s = "-" if v < 0 else ""
            return f"{s}{abs(v):,.2f} €".replace(",", " ")

        self._card_rev._val.config(text=fmt(rv), fg=GREEN if rv >= 0 else RED)
        self._card_dep._val.config(text=fmt(dv), fg=RED   if dv >  0 else GREEN)
        self._card_epg._val.config(text=fmt(ev), fg=GREEN if ev >= 0 else RED)

        for key, pv, rv2 in (("revenu",   rev_p, rev_r),
                              ("fixe",     fix_p, fix_r),
                              ("variable", var_p, var_r)):
            if key in self._section_total_labels:
                self._section_total_labels[key].config(
                    text=fmt(rv2 if bilan else pv))

        solde_final = solde_init + ev
        self._lbl_solde_final.config(
            text=fmt(solde_final),
            fg=GREEN if solde_final >= 0 else RED)

        total_actifs = sum(to_float(v.get()) for v in self._actifs_vars.values())
        total_dettes = sum(to_float(r["montant"].get()) for r in self._dette_rows)
        patrimoine   = total_actifs - total_dettes

        if self._lbl_total_actifs:
            self._lbl_total_actifs.config(text=fmt(total_actifs),
                                          fg=GREEN if total_actifs >= 0 else RED)
        if self._lbl_total_dettes:
            self._lbl_total_dettes.config(text=fmt(total_dettes), fg=RED)
        if self._lbl_patrimoine_net:
            self._lbl_patrimoine_net.config(text=fmt(patrimoine),
                                            fg=GREEN if patrimoine >= 0 else RED)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _export_html(self):
        export.export_html(self._build_payload(), self.view_year, self.view_month,
                           self._is_bilan())
