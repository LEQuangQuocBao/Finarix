import copy
import tkinter as tk
from tkinter import filedialog, messagebox

from finarix.config import (
    BG, CARD_BG, LOCK_BG, LOCK_FG, HDR_FG,
    GREEN, RED, DEFAULT_DATA,
)
from finarix.storage import load_month_file, save_month_file, next_ym, prev_ym, data_dir, get_key
from finarix import i18n
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
        return [{"label":   r["label"].get(),
                 "montant": to_float(r["montant"].get())}
                for r in self._actif_rows]

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
        cb = to_float(self._compte_bc_var.get()) if self._compte_bc_var else 0.0
        return {
            "solde_initial":   to_float(self._solde_var.get()),
            "compte_bancaire": cb,
            "actifs":          self._collect_actifs(),
            "dettes":          self._collect_dettes(),
            "revenu":          self._collect("revenu"),
            "fixe":            self._collect("fixe"),
            "variable":        self._collect("variable"),
            "note":            self._get_note(),
        }

    def _carry_balance(self, payload):
        if self._is_bilan():
            # Next month opens at the real bank balance (not the calculated figure)
            solde_next = payload.get("compte_bancaire",
                                      compute_solde_final(payload, use_reel=True))
        else:
            solde_next = compute_solde_final(payload, use_reel=False)
        ny, nm = next_ym(self.view_year, self.view_month)
        nxt = load_month_file(ny, nm) or copy.deepcopy(DEFAULT_DATA)
        nxt["solde_initial"] = solde_next
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
        # solde_initial is always read-only — it is set automatically by saving
        # the previous month's bilan (compte bancaire réel → next solde_initial)
        self._solde_entry.config(
            state=tk.DISABLED,
            bg=LOCK_BG, fg=LOCK_FG,
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
        # Migrate old actifs dict format {"compte": 0.0, ...} → list format
        if isinstance(data.get("actifs"), dict):
            _map = {"compte": "Compte bancaire", "tricount": "Tricount", "etoro": "eToro"}
            data["actifs"] = [{"label": _map.get(k, k), "montant": v}
                              for k, v in data["actifs"].items()]
        # Migrate "Compte bancaire" from actifs list → dedicated compte_bancaire field
        if "compte_bancaire" not in data:
            new_actifs, cb_val = [], None
            for a in data.get("actifs", []):
                if a.get("label") == "Compte bancaire":
                    cb_val = a.get("montant", 0.0)
                else:
                    new_actifs.append(a)
            if cb_val is None:
                cb_val = compute_solde_final(data, use_reel=True)
            data["compte_bancaire"] = cb_val
            data["actifs"] = new_actifs
        # In bilan mode, if compte_bancaire equals solde_initial it was never explicitly
        # confirmed — replace with the calculated closing balance as a better estimate
        si = data.get("solde_initial", 0.0)
        if self._is_bilan() and abs(data.get("compte_bancaire", si) - si) < 0.005:
            data["compte_bancaire"] = compute_solde_final(data, use_reel=True)
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
            text=f"{i18n.months()[self.view_month]} {self.view_year}")
        if self._is_bilan():
            self._lbl_mode.config(text=i18n.t("mode_bilan"),    bg="#1A5276", fg=HDR_FG)
        else:
            self._lbl_mode.config(text=i18n.t("mode_prevision"),bg="#784212", fg=HDR_FG)

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

        # Compte bancaire: update display in prévision, show écart in bilan
        if self._compte_bc_var is not None:
            if bilan:
                cb_reel = to_float(self._compte_bc_var.get())
                ecart   = cb_reel - solde_final
                if self._lbl_cb_calcule:
                    self._lbl_cb_calcule.config(text=fmt(solde_final))
                if self._lbl_ecart:
                    self._lbl_ecart.config(text=fmt(ecart),
                                           fg=GREEN if abs(ecart) < 0.005 else RED)
            else:
                # Auto-fill compte_bc = forecast solde_fin
                self._compte_bc_var.set(f"{solde_final:.2f}")

        cb_fin       = to_float(self._compte_bc_var.get()) if self._compte_bc_var else 0.0
        total_actifs = cb_fin + sum(to_float(r["montant"].get()) for r in self._actif_rows)
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

    def _export_data(self):
        path = filedialog.asksaveasfilename(
            title=i18n.t("dlg_backup_title"),
            defaultextension=".zip",
            filetypes=[(i18n.t("ft_zip"), "*.zip")],
            initialfile=i18n.t("dlg_backup_file"),
        )
        if not path:
            return
        try:
            n = export.export_data_zip(get_key(), data_dir(), path)
            messagebox.showinfo(i18n.t("dlg_backup_ok"),
                                i18n.t("dlg_backup_msg").format(n=n, path=path))
        except Exception as e:
            messagebox.showerror(i18n.t("dlg_error"), str(e))

    def _import_data(self):
        path = filedialog.askopenfilename(
            title=i18n.t("dlg_restore_title"),
            filetypes=[(i18n.t("ft_zip"), "*.zip")],
        )
        if not path:
            return
        if not messagebox.askyesno(i18n.t("dlg_confirm_title"),
                                    i18n.t("dlg_confirm_msg")):
            return
        try:
            n = export.import_data_zip(get_key(), path, data_dir())
            messagebox.showinfo(i18n.t("dlg_restore_ok"),
                                i18n.t("dlg_restore_msg").format(n=n))
            self._load_month()
        except Exception as e:
            messagebox.showerror(i18n.t("dlg_error"), str(e))

    def _change_lang(self, lang: str):
        if i18n.get_lang() == lang:
            return
        i18n.set_lang(lang)
        i18n.save_lang(data_dir())
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        self._load_month()
