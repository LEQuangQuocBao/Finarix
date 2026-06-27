import tkinter as tk

from finarix.config import (
    BG, CARD_BG, HDR_BG, HDR_FG, ACCENT,
    LOCK_BG, LOCK_FG, BORDER, FOOT_BG, SOLDE_BG, ADD_FG,
    GREEN, RED, SECTION_COLORS, SECTION_TITLES, ACTIFS_FIELDS, DEFAULT_DATA,
)
from finarix.finance import to_float


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

        sb = tk.Frame(self, bg=SOLDE_BG, padx=14, pady=7)
        sb.pack(fill=tk.X)
        tk.Label(sb, text="Solde début de mois :", bg=SOLDE_BG,
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
        tk.Label(sb, text="Solde fin de mois :", bg=SOLDE_BG,
                 font=("Segoe UI", 10, "bold"), fg="#1A5276").pack(side=tk.LEFT)
        self._lbl_solde_final = tk.Label(sb, text="0,00 €", bg=SOLDE_BG,
                                         font=("Segoe UI", 13, "bold"), fg="#222")
        self._lbl_solde_final.pack(side=tk.LEFT, padx=(6, 0))

        sumbar = tk.Frame(self, bg=BG, pady=6)
        sumbar.pack(fill=tk.X, padx=12)
        sumbar.columnconfigure((0, 1, 2), weight=1, uniform="card")
        self._card_rev = self._make_card(sumbar, "Revenus",  0)
        self._card_dep = self._make_card(sumbar, "Dépenses", 1)
        self._card_epg = self._make_card(sumbar, "Épargne",  2)

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
        tk.Button(bot, text="  Exporter PDF  ", bg="#566573", fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT, padx=14, pady=5,
                  activebackground="#424949", cursor="hand2",
                  command=self._export_html).pack(side=tk.LEFT, padx=12)
        self._btn_modifier = tk.Button(bot, text="  Modifier  ",
                                       bg="#F39C12", fg="white",
                                       font=("Segoe UI", 10, "bold"),
                                       relief=tk.FLAT, padx=18, pady=5,
                                       activebackground="#D68910", cursor="hand2",
                                       command=self._on_modifier_click)
        self._btn_save = tk.Button(bot, text="  Enregistrer  ",
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
        self._actifs_vars          = {}
        self._dette_rows           = []
        self._lbl_total_actifs     = None
        self._lbl_total_dettes     = None
        self._lbl_patrimoine_net   = None
        self._note_text            = None

        self._build_patrimoine(data)

        ch = tk.Frame(self._body, bg=BG)
        ch.pack(fill=tk.X, padx=4, pady=(10, 0))
        tk.Label(ch, text="", bg=BG, width=26).pack(side=tk.LEFT)
        for t in ("Prévoir (€)", "Réel (€)"):
            tk.Label(ch, text=t, bg=BG, fg="#666",
                     font=("Segoe UI", 9, "bold"), width=13,
                     anchor="center").pack(side=tk.LEFT, padx=2)

        for key in ("revenu", "fixe", "variable"):
            self._build_section(key)
            for item in data.get(key, []):
                self._add_row(key, item.get("label", ""),
                              item.get("prevoir", 0.0), item.get("reel", 0.0))

        locked = self._is_locked()
        nf = tk.LabelFrame(self._body, text=" Notes ", bg=BG,
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

        pat_wrap = tk.Frame(self._body, bg=BG)
        pat_wrap.pack(fill=tk.X, pady=(4, 0))

        hdr = tk.Frame(pat_wrap, bg="#17202A", padx=10, pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Tổng tài sản — Patrimoine", bg="#17202A", fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        act_wrap = tk.Frame(pat_wrap, bg=BG)
        act_wrap.pack(fill=tk.X, pady=(4, 0))
        tk.Frame(act_wrap, bg="#1A5276", padx=8, pady=4).pack(fill=tk.X)
        tk.Label(act_wrap.winfo_children()[-1], text="Actifs",
                 bg="#1A5276", fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        act_frame = tk.Frame(act_wrap, bg=CARD_BG, relief=tk.SOLID, bd=1)
        act_frame.pack(fill=tk.X)

        self._actifs_vars = {}
        for i, (key, label) in enumerate(ACTIFS_FIELDS):
            if i > 0:
                tk.Frame(act_frame, bg=BORDER, height=1).pack(fill=tk.X, padx=8)
            rf = tk.Frame(act_frame, bg=CARD_BG, padx=8, pady=4)
            rf.pack(fill=tk.X)
            tk.Label(rf, text=label, bg=CARD_BG, font=("Segoe UI", 10),
                     fg="#333", width=20, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=f"{actifs_data.get(key, 0.0):.2f}")
            self._actifs_vars[key] = var
            e = tk.Entry(rf, textvariable=var, font=("Segoe UI", 10),
                         relief=tk.FLAT, width=14, justify=tk.RIGHT,
                         bg=LOCK_BG if locked else CARD_BG,
                         fg=LOCK_FG if locked else "#333",
                         state=tk.DISABLED if locked else tk.NORMAL,
                         disabledbackground=LOCK_BG, disabledforeground=LOCK_FG,
                         highlightthickness=1,
                         highlightbackground=LOCK_BG if locked else BORDER)
            e.pack(side=tk.LEFT, padx=4, ipady=4)
            tk.Label(rf, text="€", bg=CARD_BG, font=("Segoe UI", 10),
                     fg="#555").pack(side=tk.LEFT)
            var.trace_add("write", lambda *_: self._recalculate())

        act_foot = tk.Frame(act_wrap, bg=FOOT_BG, padx=8, pady=4)
        act_foot.pack(fill=tk.X)
        tk.Label(act_foot, text="Total actifs :", bg=FOOT_BG,
                 font=("Segoe UI", 9, "bold"), fg="#555").pack(side=tk.LEFT)
        self._lbl_total_actifs = tk.Label(act_foot, text="0,00 €", bg=FOOT_BG,
                                          font=("Segoe UI", 9, "bold"), fg=GREEN)
        self._lbl_total_actifs.pack(side=tk.LEFT, padx=6)

        det_wrap = tk.Frame(pat_wrap, bg=BG)
        det_wrap.pack(fill=tk.X, pady=(6, 0))
        tk.Frame(det_wrap, bg="#7B241C", padx=8, pady=4).pack(fill=tk.X)
        tk.Label(det_wrap.winfo_children()[-1], text="Dettes",
                 bg="#7B241C", fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        self._dette_frame = tk.Frame(det_wrap, bg=CARD_BG, relief=tk.SOLID, bd=1)
        self._dette_frame.pack(fill=tk.X)

        self._dette_rows = []
        for d in dettes_data:
            self._add_dette(d.get("label", ""), d.get("montant", 0.0))

        det_foot = tk.Frame(det_wrap, bg=FOOT_BG, padx=8, pady=4)
        det_foot.pack(fill=tk.X)
        tk.Label(det_foot, text="Total dettes :", bg=FOOT_BG,
                 font=("Segoe UI", 9, "bold"), fg="#555").pack(side=tk.LEFT)
        self._lbl_total_dettes = tk.Label(det_foot, text="0,00 €", bg=FOOT_BG,
                                          font=("Segoe UI", 9, "bold"), fg=RED)
        self._lbl_total_dettes.pack(side=tk.LEFT, padx=6)

        tk.Button(det_wrap, text="+ Ajouter une dette", bg=BG, fg=ADD_FG,
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#DCE0E5", pady=2,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=self._add_dette).pack(anchor="w", pady=(2, 0))

        pat_net = tk.Frame(pat_wrap, bg="#1E2D3D", padx=12, pady=8)
        pat_net.pack(fill=tk.X, pady=(8, 0))
        tk.Label(pat_net, text="Patrimoine net :", bg="#1E2D3D", fg="#AAA",
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

    def _build_section(self, key):
        locked = self._is_locked()
        color  = SECTION_COLORS[key]
        wrap   = tk.Frame(self._body, bg=BG)
        wrap.pack(fill=tk.X, pady=4)
        hdr = tk.Frame(wrap, bg=color, padx=8, pady=5)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=SECTION_TITLES[key], bg=color, fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        rows = tk.Frame(wrap, bg=CARD_BG, relief=tk.SOLID, bd=1)
        rows.pack(fill=tk.X)
        self._section_frames[key] = rows
        foot = tk.Frame(wrap, bg=FOOT_BG, padx=8, pady=4)
        foot.pack(fill=tk.X)
        tk.Label(foot, text="Total :", bg=FOOT_BG,
                 font=("Segoe UI", 9, "bold"), fg="#555").pack(side=tk.LEFT)
        tot = tk.Label(foot, text="0,00 €", bg=FOOT_BG,
                       font=("Segoe UI", 9, "bold"), fg="#222")
        tot.pack(side=tk.LEFT, padx=6)
        self._section_total_labels[key] = tot
        tk.Button(wrap, text="+ Ajouter une ligne", bg=BG, fg=ADD_FG,
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
