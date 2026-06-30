import tkinter as tk

from finarix.config import (
    BG, CARD_BG, HDR_BG, HDR_FG, ACCENT,
    LOCK_BG, LOCK_FG, BORDER, FOOT_BG, SOLDE_BG, ADD_FG,
    GREEN, RED, SECTION_COLORS, DEFAULT_DATA,
)
from finarix.finance import to_float
from finarix import i18n


class UIBuildMixin:

    # ── static UI (built once) ────────────────────────────────────────────────

    def _build_ui(self):
        top = tk.Frame(self, bg=HDR_BG, padx=10, pady=7)
        top.pack(fill=tk.X)

        nav = tk.Frame(top, bg=HDR_BG)
        nav.pack(side=tk.LEFT)
        tk.Button(nav, text="◀", bg=HDR_BG, fg=HDR_FG, relief=tk.FLAT,
                  font=("Segoe UI", 12, "bold"), activebackground="#111e28",
                  activeforeground=HDR_FG, cursor="hand2", bd=0,
                  command=self._go_prev).pack(side=tk.LEFT, padx=(0, 5))
        self._lbl_month = tk.Label(nav, text="", bg=HDR_BG, fg=HDR_FG,
                                   font=("Segoe UI", 14, "bold"), width=22,
                                   anchor="center")
        self._lbl_month.pack(side=tk.LEFT)
        tk.Button(nav, text="▶", bg=HDR_BG, fg=HDR_FG, relief=tk.FLAT,
                  font=("Segoe UI", 12, "bold"), activebackground="#111e28",
                  activeforeground=HDR_FG, cursor="hand2", bd=0,
                  command=self._go_next).pack(side=tk.LEFT, padx=(5, 0))

        self._lbl_mode = tk.Label(top, text="", font=("Segoe UI", 9, "bold"),
                                  fg=HDR_FG, bg=HDR_BG, padx=14, pady=4,
                                  relief=tk.GROOVE)
        self._lbl_mode.pack(side=tk.RIGHT, padx=6)

        # ── ☰ header menu ─────────────────────────────────────────────────────
        mb = tk.Menubutton(top, text="☰", bg=HDR_BG, fg=HDR_FG,
                           font=("Segoe UI", 13), relief=tk.FLAT, bd=0,
                           activebackground="#111e28", activeforeground=HDR_FG,
                           cursor="hand2", padx=10, pady=2, direction="below")
        mb_menu = tk.Menu(mb, tearoff=0, bg="#FFFFFF", fg="#222",
                          activebackground=ACCENT, activeforeground="white",
                          font=("Segoe UI", 10))
        mb_menu.add_command(label=i18n.t("menu_sauvegarde"), command=self._export_data)
        mb_menu.add_command(label=i18n.t("menu_restaurer"),  command=self._import_data)
        mb_menu.add_separator()
        mb_menu.add_command(label=i18n.t("menu_about"),      command=self._show_about)
        mb["menu"] = mb_menu
        mb.pack(side=tk.RIGHT, padx=(0, 6))

        lang_frame = tk.Frame(top, bg=HDR_BG)
        lang_frame.pack(side=tk.RIGHT, padx=10)
        for code, label in i18n.LANGS:
            active = i18n.get_lang() == code
            tk.Button(lang_frame, text=label,
                      bg=ACCENT if active else HDR_BG, fg=HDR_FG,
                      font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                      padx=10, pady=2, cursor="hand2",
                      activebackground=ACCENT, activeforeground=HDR_FG, bd=0,
                      command=lambda c=code: self._change_lang(c)
                      ).pack(side=tk.LEFT, padx=1)

        sb = tk.Frame(self, bg=SOLDE_BG, padx=14, pady=7)
        sb.pack(fill=tk.X)
        tk.Label(sb, text=i18n.t("solde_debut"), bg=SOLDE_BG,
                 font=("Segoe UI", 10, "bold"), fg="#1A5276").pack(side=tk.LEFT)
        self._solde_var = tk.StringVar(value="0.00")
        self._solde_entry = tk.Entry(sb, textvariable=self._solde_var,
                                     font=("Segoe UI", 10), width=12,
                                     justify=tk.RIGHT, relief=tk.SOLID, bd=1,
                                     bg=CARD_BG, fg="#333")
        self._solde_entry.pack(side=tk.LEFT, padx=(6, 4), ipady=3)
        tk.Label(sb, text="€", bg=SOLDE_BG, font=("Segoe UI", 10),
                 fg="#555").pack(side=tk.LEFT, padx=(0, 30))
        self._solde_var.trace_add("write", lambda *_: self._recalculate())
        tk.Label(sb, text=i18n.t("solde_fin"), bg=SOLDE_BG,
                 font=("Segoe UI", 10, "bold"), fg="#1A5276").pack(side=tk.LEFT)
        self._lbl_solde_final = tk.Label(sb, text="0,00 €", bg=SOLDE_BG,
                                         font=("Segoe UI", 13, "bold"), fg="#222")
        self._lbl_solde_final.pack(side=tk.LEFT, padx=(6, 0))

        sumbar = tk.Frame(self, bg=BG, pady=6)
        sumbar.pack(fill=tk.X, padx=12)
        sumbar.columnconfigure((0, 1, 2), weight=1, uniform="card")
        self._card_rev = self._make_card(sumbar, i18n.t("card_revenus"),  0)
        self._card_dep = self._make_card(sumbar, i18n.t("card_depenses"), 1)
        self._card_epg = self._make_card(sumbar, i18n.t("card_epargne"),  2)

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))
        self._canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient=tk.VERTICAL, command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._body = tk.Frame(self._canvas, bg=BG)
        self._canvas_win = self._canvas.create_window((0, 0), window=self._body,
                                                       anchor="nw")
        self._body.bind("<Configure>",
                        lambda e: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(
                              self._canvas_win, width=e.width))
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        bot = tk.Frame(self, bg="#E8EAED", pady=7)
        bot.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(bot, text=i18n.t("btn_pdf"), bg="#566573", fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT, padx=14, pady=5,
                  activebackground="#424949", cursor="hand2",
                  command=self._export_html).pack(side=tk.LEFT, padx=(12, 4))
        self._btn_modifier = tk.Button(bot, text=i18n.t("btn_modifier"),
                                       bg="#F39C12", fg="white",
                                       font=("Segoe UI", 10, "bold"),
                                       relief=tk.FLAT, padx=18, pady=5,
                                       activebackground="#D68910", cursor="hand2",
                                       command=self._on_modifier_click)
        self._btn_save = tk.Button(bot, text=i18n.t("btn_enregistrer"),
                                   bg=ACCENT, fg="white",
                                   font=("Segoe UI", 10, "bold"),
                                   relief=tk.FLAT, padx=18, pady=5,
                                   activebackground="#1f638d", cursor="hand2",
                                   command=self._on_save_click)
        self._btn_save.pack(side=tk.RIGHT, padx=12)

    def _make_card(self, parent, title, col):
        f = tk.Frame(parent, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=10, pady=8)
        f.grid(row=0, column=col, padx=6, sticky="ew")
        tk.Label(f, text=title, bg=CARD_BG, fg="#888", font=("Segoe UI", 9)).pack()
        v = tk.Label(f, text="0,00 €", bg=CARD_BG, fg="#222",
                     font=("Segoe UI", 14, "bold"))
        v.pack()
        f._val = v
        return f

    # ── dynamic body (rebuilt on every month load) ────────────────────────────

    def _rebuild_body(self, data):
        for w in self._body.winfo_children():
            w.destroy()

        self._row_widgets          = {"revenu": [], "fixe": [], "variable": []}
        self._section_frames       = {}
        self._section_total_labels = {}
        self._actif_rows           = []
        self._dette_rows           = []
        self._lbl_total_actifs     = None
        self._lbl_total_dettes     = None
        self._lbl_patrimoine_net   = None
        self._note_text            = None
        self._compte_bc_var        = None
        self._lbl_cb_calcule       = None
        self._lbl_ecart            = None
        self._compte_bc_manual     = False
        self._cb_updating          = False

        self._build_patrimoine(data)

        ch = tk.Frame(self._body, bg=BG)
        ch.pack(fill=tk.X, padx=4, pady=(10, 0))
        tk.Label(ch, text="", bg=BG, width=26).pack(side=tk.LEFT)
        for lbl in (i18n.t("col_prevoir"), i18n.t("col_reel")):
            tk.Label(ch, text=lbl, bg=BG, fg="#666",
                     font=("Segoe UI", 9, "bold"), width=13,
                     anchor="center").pack(side=tk.LEFT, padx=2)

        for key in ("revenu", "fixe", "variable"):
            self._build_section(key)
            for item in data.get(key, []):
                self._add_row(key, item.get("label", ""),
                              item.get("prevoir", 0.0), item.get("reel", 0.0))

        locked = self._is_locked()
        nf = tk.LabelFrame(self._body, text=i18n.t("notes"), bg=BG,
                           font=("Segoe UI", 9, "bold"), fg="#555",
                           padx=6, pady=4, relief=tk.GROOVE, bd=1)
        nf.pack(fill=tk.X, pady=(10, 4))
        self._note_text = tk.Text(nf, height=4, font=("Segoe UI", 10),
                                  relief=tk.SOLID, bd=1, wrap=tk.WORD,
                                  bg=LOCK_BG if locked else CARD_BG,
                                  fg=LOCK_FG if locked else "#333")
        self._note_text.pack(fill=tk.X)
        note_val = data.get("note", "")
        if note_val:
            self._note_text.insert("1.0", note_val)
        if locked:
            self._note_text.config(state=tk.DISABLED)

        self._recalculate()

    def _build_patrimoine(self, data):
        actifs_data = data.get("actifs", DEFAULT_DATA["actifs"])
        dettes_data = data.get("dettes", [])
        locked = self._is_locked()
        bilan  = self._is_bilan()

        pat_wrap = tk.Frame(self._body, bg=BG)
        pat_wrap.pack(fill=tk.X, pady=(4, 0))

        hdr = tk.Frame(pat_wrap, bg="#17202A", padx=10, pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=i18n.t("pat_titre"), bg="#17202A", fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        # ── Compte bancaire ───────────────────────────────────────────────────
        cb_wrap = tk.Frame(pat_wrap, bg=BG)
        cb_wrap.pack(fill=tk.X, pady=(4, 0))

        cb_hdr_f = tk.Frame(cb_wrap, bg="#1B4F72", padx=8, pady=4)
        cb_hdr_f.pack(fill=tk.X)
        tk.Label(cb_hdr_f, text=i18n.t("cb_titre"), bg="#1B4F72", fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        cb_body = tk.Frame(cb_wrap, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=10, pady=8)
        cb_body.pack(fill=tk.X)

        def _fmtv(v):
            return (f"-{abs(v):,.2f} €" if v < 0 else f"{v:,.2f} €").replace(",", " ")

        # Row 1: Début (solde_initial, always read-only)
        r1 = tk.Frame(cb_body, bg=CARD_BG)
        r1.pack(fill=tk.X, pady=(0, 4))
        tk.Label(r1, text=i18n.t("cb_debut"), bg=CARD_BG, fg="#777",
                 font=("Segoe UI", 9), width=22, anchor="w").pack(side=tk.LEFT)
        si_val = data.get("solde_initial", 0.0)
        tk.Label(r1, text=_fmtv(si_val), bg=CARD_BG, fg="#444",
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=6)

        # Row 2: Fin (editable in bilan edit mode, auto-label otherwise)
        r2 = tk.Frame(cb_body, bg=CARD_BG)
        r2.pack(fill=tk.X)
        tk.Label(r2, text=i18n.t("cb_fin"), bg=CARD_BG, fg="#777",
                 font=("Segoe UI", 9), width=22, anchor="w").pack(side=tk.LEFT)

        cb_val = data.get("compte_bancaire", si_val)
        self._compte_bc_var = tk.StringVar(value=f"{cb_val:.2f}")

        if bilan and not locked:
            e = tk.Entry(r2, textvariable=self._compte_bc_var,
                         font=("Segoe UI", 10), relief=tk.SOLID, bd=1,
                         width=14, justify=tk.RIGHT, bg=CARD_BG, fg="#222",
                         highlightthickness=1, highlightbackground=BORDER)
            e.pack(side=tk.LEFT, ipady=4, padx=(0, 4))

            def _on_cb_change(*_):
                if getattr(self, '_cb_updating', False):
                    return  # programmatic update — ignore
                self._compte_bc_manual = True
                self._recalculate()

            self._compte_bc_var.trace_add("write", _on_cb_change)
        else:
            tk.Label(r2, textvariable=self._compte_bc_var,
                     bg=LOCK_BG if locked else CARD_BG,
                     fg=LOCK_FG if locked else "#444",
                     font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=6)
        tk.Label(r2, text="€", bg=CARD_BG, fg="#555",
                 font=("Segoe UI", 10)).pack(side=tk.LEFT)

        # Row 3: Écart (bilan mode only)
        if bilan:
            tk.Frame(cb_body, bg=BORDER, height=1).pack(fill=tk.X, pady=(6, 0))
            r3 = tk.Frame(cb_body, bg=CARD_BG)
            r3.pack(fill=tk.X, pady=(4, 0))
            tk.Label(r3, text=i18n.t("cb_calcule"), bg=CARD_BG, fg="#777",
                     font=("Segoe UI", 9), width=22, anchor="w").pack(side=tk.LEFT)
            self._lbl_cb_calcule = tk.Label(r3, text="0,00 €", bg=CARD_BG,
                                             fg="#444", font=("Segoe UI", 9))
            self._lbl_cb_calcule.pack(side=tk.LEFT, padx=(4, 20))
            tk.Label(r3, text=i18n.t("cb_ecart"), bg=CARD_BG, fg="#777",
                     font=("Segoe UI", 9)).pack(side=tk.LEFT)
            self._lbl_ecart = tk.Label(r3, text="0,00 €", bg=CARD_BG,
                                        fg=GREEN, font=("Segoe UI", 9, "bold"))
            self._lbl_ecart.pack(side=tk.LEFT, padx=6)

        # ── actifs ────────────────────────────────────────────────────────────
        act_wrap = tk.Frame(pat_wrap, bg=BG)
        act_wrap.pack(fill=tk.X, pady=(4, 0))
        tk.Frame(act_wrap, bg="#1A5276", padx=8, pady=4).pack(fill=tk.X)
        tk.Label(act_wrap.winfo_children()[-1], text=i18n.t("pat_actifs"),
                 bg="#1A5276", fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        self._actif_frame = tk.Frame(act_wrap, bg=CARD_BG, relief=tk.SOLID, bd=1)
        self._actif_frame.pack(fill=tk.X)

        self._actif_rows = []
        for a in actifs_data:
            self._add_actif(a.get("label", ""), a.get("montant", 0.0))

        tk.Button(act_wrap, text=i18n.t("btn_add_actif"), bg=BG, fg=ADD_FG,
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#DCE0E5", pady=2,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=self._add_actif).pack(anchor="w", pady=(2, 0))

        act_foot = tk.Frame(act_wrap, bg=FOOT_BG, padx=8, pady=4)
        act_foot.pack(fill=tk.X)
        tk.Label(act_foot, text=i18n.t("pat_total_actifs"), bg=FOOT_BG,
                 font=("Segoe UI", 9, "bold"), fg="#555").pack(side=tk.LEFT)
        self._lbl_total_actifs = tk.Label(act_foot, text="0,00 €", bg=FOOT_BG,
                                          font=("Segoe UI", 9, "bold"), fg=GREEN)
        self._lbl_total_actifs.pack(side=tk.LEFT, padx=6)

        # ── dettes ────────────────────────────────────────────────────────────
        det_wrap = tk.Frame(pat_wrap, bg=BG)
        det_wrap.pack(fill=tk.X, pady=(6, 0))
        tk.Frame(det_wrap, bg="#7B241C", padx=8, pady=4).pack(fill=tk.X)
        tk.Label(det_wrap.winfo_children()[-1], text=i18n.t("pat_dettes"),
                 bg="#7B241C", fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        self._dette_frame = tk.Frame(det_wrap, bg=CARD_BG, relief=tk.SOLID, bd=1)
        self._dette_frame.pack(fill=tk.X)

        self._dette_rows = []
        for d in dettes_data:
            self._add_dette(d.get("label", ""), d.get("montant", 0.0))

        det_foot = tk.Frame(det_wrap, bg=FOOT_BG, padx=8, pady=4)
        det_foot.pack(fill=tk.X)
        tk.Label(det_foot, text=i18n.t("pat_total_dettes"), bg=FOOT_BG,
                 font=("Segoe UI", 9, "bold"), fg="#555").pack(side=tk.LEFT)
        self._lbl_total_dettes = tk.Label(det_foot, text="0,00 €", bg=FOOT_BG,
                                          font=("Segoe UI", 9, "bold"), fg=RED)
        self._lbl_total_dettes.pack(side=tk.LEFT, padx=6)

        tk.Button(det_wrap, text=i18n.t("btn_add_dette"), bg=BG, fg=ADD_FG,
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#DCE0E5", pady=2,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=self._add_dette).pack(anchor="w", pady=(2, 0))

        pat_net = tk.Frame(pat_wrap, bg="#1E2D3D", padx=12, pady=8)
        pat_net.pack(fill=tk.X, pady=(8, 0))
        tk.Label(pat_net, text=i18n.t("pat_net"), bg="#1E2D3D", fg="#AAA",
                 font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self._lbl_patrimoine_net = tk.Label(pat_net, text="0,00 €",
                                            bg="#1E2D3D", fg="white",
                                            font=("Segoe UI", 14, "bold"))
        self._lbl_patrimoine_net.pack(side=tk.LEFT, padx=10)

    def _add_dette(self, label="", montant=0.0):
        locked = self._is_locked()
        rf = tk.Frame(self._dette_frame, bg=CARD_BG)
        rf.pack(fill=tk.X)
        if self._dette_rows:
            tk.Frame(rf, bg=BORDER, height=1).pack(fill=tk.X)
        inner = tk.Frame(rf, bg=CARD_BG, padx=8, pady=3)
        inner.pack(fill=tk.X)

        lbl_var  = tk.StringVar(value=label)
        mont_var = tk.StringVar(value=f"{montant:.2f}")

        def _e(parent, var, width, right=False):
            return tk.Entry(parent, textvariable=var, font=("Segoe UI", 10),
                            relief=tk.FLAT, width=width,
                            justify=tk.RIGHT if right else tk.LEFT,
                            bg=LOCK_BG if locked else CARD_BG,
                            fg=LOCK_FG if locked else "#333",
                            state=tk.DISABLED if locked else tk.NORMAL,
                            disabledbackground=LOCK_BG, disabledforeground=LOCK_FG,
                            highlightthickness=1,
                            highlightbackground=LOCK_BG if locked else BORDER)

        _e(inner, lbl_var, 22).pack(side=tk.LEFT, padx=(0, 4), ipady=4)
        _e(inner, mont_var, 14, right=True).pack(side=tk.LEFT, padx=2, ipady=4)
        tk.Label(inner, text="€", bg=CARD_BG, font=("Segoe UI", 10),
                 fg="#555").pack(side=tk.LEFT, padx=(2, 6))
        tk.Button(inner, text="✕", bg=CARD_BG, fg="#C0392B",
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#FADBD8", bd=0,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=lambda f=rf: self._delete_dette(f)
                  ).pack(side=tk.LEFT, padx=(4, 0))

        mont_var.trace_add("write", lambda *_: self._recalculate())
        self._dette_rows.append({"frame": rf, "label": lbl_var, "montant": mont_var})
        self._recalculate()

    def _delete_dette(self, row_frame):
        self._dette_rows = [r for r in self._dette_rows if r["frame"] is not row_frame]
        row_frame.destroy()
        self._recalculate()

    def _add_actif(self, label="", montant=0.0):
        locked = self._is_locked()
        rf = tk.Frame(self._actif_frame, bg=CARD_BG)
        rf.pack(fill=tk.X)
        if self._actif_rows:
            tk.Frame(rf, bg=BORDER, height=1).pack(fill=tk.X)
        inner = tk.Frame(rf, bg=CARD_BG, padx=8, pady=3)
        inner.pack(fill=tk.X)

        lbl_var  = tk.StringVar(value=label)
        mont_var = tk.StringVar(value=f"{montant:.2f}")

        def _e(parent, var, width, right=False):
            return tk.Entry(parent, textvariable=var, font=("Segoe UI", 10),
                            relief=tk.FLAT, width=width,
                            justify=tk.RIGHT if right else tk.LEFT,
                            bg=LOCK_BG if locked else CARD_BG,
                            fg=LOCK_FG if locked else "#333",
                            state=tk.DISABLED if locked else tk.NORMAL,
                            disabledbackground=LOCK_BG, disabledforeground=LOCK_FG,
                            highlightthickness=1,
                            highlightbackground=LOCK_BG if locked else BORDER)

        _e(inner, lbl_var, 22).pack(side=tk.LEFT, padx=(0, 4), ipady=4)
        _e(inner, mont_var, 14, right=True).pack(side=tk.LEFT, padx=2, ipady=4)
        tk.Label(inner, text="€", bg=CARD_BG, font=("Segoe UI", 10),
                 fg="#555").pack(side=tk.LEFT, padx=(2, 6))
        tk.Button(inner, text="✕", bg=CARD_BG, fg="#C0392B",
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#FADBD8", bd=0,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=lambda f=rf: self._delete_actif(f)
                  ).pack(side=tk.LEFT, padx=(4, 0))

        mont_var.trace_add("write", lambda *_: self._recalculate())
        self._actif_rows.append({"frame": rf, "label": lbl_var, "montant": mont_var})
        self._recalculate()

    def _delete_actif(self, row_frame):
        self._actif_rows = [r for r in self._actif_rows if r["frame"] is not row_frame]
        row_frame.destroy()
        self._recalculate()

    def _build_section(self, key):
        locked = self._is_locked()
        color  = SECTION_COLORS[key]
        wrap   = tk.Frame(self._body, bg=BG)
        wrap.pack(fill=tk.X, pady=4)
        hdr = tk.Frame(wrap, bg=color, padx=8, pady=5)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=i18n.t(f"sec_{key}"), bg=color, fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        rows = tk.Frame(wrap, bg=CARD_BG, relief=tk.SOLID, bd=1)
        rows.pack(fill=tk.X)
        self._section_frames[key] = rows
        foot = tk.Frame(wrap, bg=FOOT_BG, padx=8, pady=4)
        foot.pack(fill=tk.X)
        tk.Label(foot, text=i18n.t("section_total"), bg=FOOT_BG,
                 font=("Segoe UI", 9, "bold"), fg="#555").pack(side=tk.LEFT)
        tot = tk.Label(foot, text="0,00 €", bg=FOOT_BG,
                       font=("Segoe UI", 9, "bold"), fg="#222")
        tot.pack(side=tk.LEFT, padx=6)
        self._section_total_labels[key] = tot
        tk.Button(wrap, text=i18n.t("btn_add_row"), bg=BG, fg=ADD_FG,
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#DCE0E5", pady=2,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=lambda k=key: self._add_row(k)
                  ).pack(anchor="w", pady=(2, 0))

    def _add_row(self, key, label="", prevoir=0.0, reel=0.0):
        locked      = self._is_locked()
        reel_locked = not self._is_bilan() or locked
        frame = self._section_frames[key]

        rf = tk.Frame(frame, bg=CARD_BG)
        rf.pack(fill=tk.X)
        if self._row_widgets[key]:
            tk.Frame(rf, bg=BORDER, height=1).pack(fill=tk.X)
        inner = tk.Frame(rf, bg=CARD_BG, padx=6, pady=3)
        inner.pack(fill=tk.X)

        lbl_var  = tk.StringVar(value=label)
        prev_var = tk.StringVar(value=f"{prevoir:.2f}")
        reel_var = tk.StringVar(value=f"{reel:.2f}")

        def _entry(parent, var, width, lock):
            return tk.Entry(parent, textvariable=var, font=("Segoe UI", 10),
                            relief=tk.FLAT, width=width,
                            justify=tk.RIGHT if width < 20 else tk.LEFT,
                            bg=LOCK_BG if lock else CARD_BG,
                            fg=LOCK_FG if lock else "#333",
                            state=tk.DISABLED if lock else tk.NORMAL,
                            disabledbackground=LOCK_BG, disabledforeground=LOCK_FG,
                            highlightthickness=1,
                            highlightbackground=LOCK_BG if lock else BORDER)

        _entry(inner, lbl_var,  26, locked     ).pack(side=tk.LEFT, padx=(0, 4), ipady=5)
        _entry(inner, prev_var, 13, locked     ).pack(side=tk.LEFT, padx=2,      ipady=5)
        _entry(inner, reel_var, 13, reel_locked).pack(side=tk.LEFT, padx=2,      ipady=5)
        tk.Button(inner, text="✕", bg=CARD_BG, fg="#C0392B",
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#FADBD8", bd=0,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=lambda f=rf, k=key: self._delete_row(f, k)
                  ).pack(side=tk.LEFT, padx=(4, 0))

        for var in (prev_var, reel_var):
            var.trace_add("write", lambda *_: self._recalculate())

        self._row_widgets[key].append({
            "frame": rf, "label": lbl_var, "prevoir": prev_var, "reel": reel_var
        })
        self._recalculate()

    def _delete_row(self, row_frame, key):
        self._row_widgets[key] = [r for r in self._row_widgets[key]
                                  if r["frame"] is not row_frame]
        row_frame.destroy()
        self._recalculate()
