import tkinter as tk
import json
import os
import sys
import copy
import webbrowser
import tempfile
from datetime import date

# ─── paths ────────────────────────────────────────────────────────────────────

def data_dir():
    if hasattr(sys, '_MEIPASS'):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, 'data')
    os.makedirs(d, exist_ok=True)
    return d

def month_path(year, month):
    return os.path.join(data_dir(), f"{year:04d}-{month:02d}.json")

def load_month_file(year, month):
    p = month_path(year, month)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    return None

def save_month_file(year, month, payload):
    with open(month_path(year, month), 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

def next_ym(y, m): return (y + 1, 1) if m == 12 else (y, m + 1)
def prev_ym(y, m): return (y - 1, 12) if m == 1 else (y, m - 1)

# ─── constants ────────────────────────────────────────────────────────────────

MONTHS_FR = ['','Janvier','Février','Mars','Avril','Mai','Juin',
             'Juillet','Août','Septembre','Octobre','Novembre','Décembre']

ACTIFS_FIELDS = [
    ("compte",   "Compte bancaire"),
    ("tricount", "Tricount"),
    ("etoro",    "eToro"),
]

DEFAULT_DATA = {
    "solde_initial": 0.0,
    "actifs":   {"compte": 0.0, "tricount": 0.0, "etoro": 0.0},
    "dettes":   [{"label": "Prêt immobilier", "montant": 0.0}],
    "revenu":   [{"label": "Salaire net",      "prevoir": 0.0, "reel": 0.0},
                 {"label": "Autres revenus",   "prevoir": 0.0, "reel": 0.0}],
    "fixe":     [{"label": "Loyer/Crédit immo","prevoir": 0.0, "reel": 0.0},
                 {"label": "Eau/Électricité",  "prevoir": 0.0, "reel": 0.0},
                 {"label": "Téléphone",        "prevoir": 0.0, "reel": 0.0},
                 {"label": "Internet",         "prevoir": 0.0, "reel": 0.0},
                 {"label": "Assurances",       "prevoir": 0.0, "reel": 0.0}],
    "variable": [{"label": "Courses",          "prevoir": 0.0, "reel": 0.0},
                 {"label": "Transport",        "prevoir": 0.0, "reel": 0.0},
                 {"label": "Sorties/Resto",    "prevoir": 0.0, "reel": 0.0},
                 {"label": "Divers",           "prevoir": 0.0, "reel": 0.0}],
    "note": ""
}

BG       = "#F4F6F8"
CARD_BG  = "#FFFFFF"
HDR_BG   = "#1E2D3D"
HDR_FG   = "#FFFFFF"
GREEN    = "#27AE60"
RED      = "#E74C3C"
ACCENT   = "#2980B9"
LOCK_BG  = "#ECECEC"
LOCK_FG  = "#AAAAAA"
BORDER   = "#D5D8DC"
FOOT_BG  = "#EAECEE"
SOLDE_BG = "#EBF5FB"
ADD_FG   = "#555555"

SECTION_COLORS = {"revenu":"#1A5276","fixe":"#145A32","variable":"#784212"}
SECTION_TITLES = {"revenu":"Revenus","fixe":"Dépenses fixes","variable":"Dépenses variables"}

# ─── app ──────────────────────────────────────────────────────────────────────

class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finarix")
        self.geometry("880x760")
        self.minsize(740, 560)
        self.configure(bg=BG)

        today = date.today()
        self.view_year  = today.year
        self.view_month = today.month
        self._today     = today

        self._bilan_editing = False

        # dynamic widget refs (reset per rebuild)
        self._row_widgets          = {"revenu": [], "fixe": [], "variable": []}
        self._section_frames       = {}
        self._section_total_labels = {}
        self._actifs_vars          = {}
        self._dette_rows           = []
        self._lbl_total_actifs     = None
        self._lbl_total_dettes     = None
        self._lbl_patrimoine_net   = None
        self._note_text            = None

        self._build_ui()
        self._load_month()

    # ── static UI (built once) ────────────────────────────────────────────────

    def _build_ui(self):
        # top bar
        top = tk.Frame(self, bg=HDR_BG, padx=10, pady=7)
        top.pack(fill=tk.X)
        nav = tk.Frame(top, bg=HDR_BG)
        nav.pack(side=tk.LEFT)
        tk.Button(nav, text="◀", bg=HDR_BG, fg=HDR_FG, relief=tk.FLAT,
                  font=("Segoe UI", 12, "bold"), activebackground="#111e28",
                  activeforeground=HDR_FG, cursor="hand2", bd=0,
                  command=self._go_prev).pack(side=tk.LEFT, padx=(0,5))
        self._lbl_month = tk.Label(nav, text="", bg=HDR_BG, fg=HDR_FG,
                                   font=("Segoe UI", 14, "bold"), width=22,
                                   anchor="center")
        self._lbl_month.pack(side=tk.LEFT)
        tk.Button(nav, text="▶", bg=HDR_BG, fg=HDR_FG, relief=tk.FLAT,
                  font=("Segoe UI", 12, "bold"), activebackground="#111e28",
                  activeforeground=HDR_FG, cursor="hand2", bd=0,
                  command=self._go_next).pack(side=tk.LEFT, padx=(5,0))
        self._lbl_mode = tk.Label(top, text="", font=("Segoe UI", 9, "bold"),
                                  fg=HDR_FG, bg=HDR_BG, padx=14, pady=4,
                                  relief=tk.GROOVE)
        self._lbl_mode.pack(side=tk.RIGHT, padx=6)

        # solde bar
        sb = tk.Frame(self, bg=SOLDE_BG, padx=14, pady=7)
        sb.pack(fill=tk.X)
        tk.Label(sb, text="Solde début de mois :", bg=SOLDE_BG,
                 font=("Segoe UI", 10, "bold"), fg="#1A5276").pack(side=tk.LEFT)
        self._solde_var = tk.StringVar(value="0.00")
        self._solde_entry = tk.Entry(sb, textvariable=self._solde_var,
                                     font=("Segoe UI", 10), width=12,
                                     justify=tk.RIGHT, relief=tk.SOLID, bd=1,
                                     bg=CARD_BG, fg="#333")
        self._solde_entry.pack(side=tk.LEFT, padx=(6,4), ipady=3)
        tk.Label(sb, text="€", bg=SOLDE_BG, font=("Segoe UI", 10),
                 fg="#555").pack(side=tk.LEFT, padx=(0,30))
        self._solde_var.trace_add("write", lambda *_: self._recalculate())
        tk.Label(sb, text="Solde fin de mois :", bg=SOLDE_BG,
                 font=("Segoe UI", 10, "bold"), fg="#1A5276").pack(side=tk.LEFT)
        self._lbl_solde_final = tk.Label(sb, text="0,00 €", bg=SOLDE_BG,
                                         font=("Segoe UI", 13, "bold"), fg="#222")
        self._lbl_solde_final.pack(side=tk.LEFT, padx=(6,0))

        # summary cards
        sumbar = tk.Frame(self, bg=BG, pady=6)
        sumbar.pack(fill=tk.X, padx=12)
        sumbar.columnconfigure((0,1,2), weight=1, uniform="card")
        self._card_rev = self._make_card(sumbar, "Revenus",  0)
        self._card_dep = self._make_card(sumbar, "Dépenses", 1)
        self._card_epg = self._make_card(sumbar, "Épargne",  2)

        # scrollable body
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,4))
        self._canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient=tk.VERTICAL, command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._body = tk.Frame(self._canvas, bg=BG)
        self._canvas_win = self._canvas.create_window((0,0), window=self._body,
                                                       anchor="nw")
        self._body.bind("<Configure>",
                        lambda e: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(
                              self._canvas_win, width=e.width))
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # bottom bar
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
        # initial pack — _update_buttons will fix on first load
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

        # column headers for income/expense sections
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
                self._add_row(key, item.get("label",""),
                              item.get("prevoir",0.0), item.get("reel",0.0))

        # notes
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

        # header
        hdr = tk.Frame(pat_wrap, bg="#17202A", padx=10, pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Tổng tài sản — Patrimoine", bg="#17202A", fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        # ── actifs ──────────────────────────────────────────────────────────
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

        # ── dettes ──────────────────────────────────────────────────────────
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
            self._add_dette(d.get("label",""), d.get("montant", 0.0))

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
                  command=self._add_dette).pack(anchor="w", pady=(2,0))

        # ── patrimoine net ───────────────────────────────────────────────────
        pat_net = tk.Frame(pat_wrap, bg="#1E2D3D", padx=12, pady=8)
        pat_net.pack(fill=tk.X, pady=(8,0))
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

        _e(inner, lbl_var, 22).pack(side=tk.LEFT, padx=(0,4), ipady=4)
        _e(inner, mont_var, 14, right=True).pack(side=tk.LEFT, padx=2, ipady=4)
        tk.Label(inner, text="€", bg=CARD_BG, font=("Segoe UI",10),
                 fg="#555").pack(side=tk.LEFT, padx=(2,6))
        tk.Button(inner, text="✕", bg=CARD_BG, fg="#C0392B",
                  font=("Segoe UI",9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#FADBD8", bd=0,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=lambda f=rf: self._delete_dette(f)
                  ).pack(side=tk.LEFT, padx=(4,0))

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
                  ).pack(anchor="w", pady=(2,0))

    def _add_row(self, key, label="", prevoir=0.0, reel=0.0):
        locked     = self._is_locked()
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

        _entry(inner, lbl_var,  26, locked     ).pack(side=tk.LEFT, padx=(0,4), ipady=5)
        _entry(inner, prev_var, 13, locked     ).pack(side=tk.LEFT, padx=2,     ipady=5)
        _entry(inner, reel_var, 13, reel_locked).pack(side=tk.LEFT, padx=2,     ipady=5)
        tk.Button(inner, text="✕", bg=CARD_BG, fg="#C0392B",
                  font=("Segoe UI",9), relief=tk.FLAT, cursor="hand2",
                  activebackground="#FADBD8", bd=0,
                  state=tk.DISABLED if locked else tk.NORMAL,
                  command=lambda f=rf, k=key: self._delete_row(f, k)
                  ).pack(side=tk.LEFT, padx=(4,0))

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

    # ── data ──────────────────────────────────────────────────────────────────

    def _is_bilan(self):
        return (self.view_year, self.view_month) < (self._today.year, self._today.month)

    def _is_locked(self):
        return self._is_bilan() and not self._bilan_editing

    @staticmethod
    def _to_float(s):
        try:
            return float(str(s).replace(',','.').strip())
        except (ValueError, TypeError):
            return 0.0

    def _collect(self, key):
        return [{"label":  r["label"].get(),
                 "prevoir": self._to_float(r["prevoir"].get()),
                 "reel":    self._to_float(r["reel"].get())}
                for r in self._row_widgets[key]]

    def _collect_actifs(self):
        return {k: self._to_float(v.get()) for k, v in self._actifs_vars.items()}

    def _collect_dettes(self):
        return [{"label":   r["label"].get(),
                 "montant": self._to_float(r["montant"].get())}
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
            "solde_initial": self._to_float(self._solde_var.get()),
            "actifs":        self._collect_actifs(),
            "dettes":        self._collect_dettes(),
            "revenu":        self._collect("revenu"),
            "fixe":          self._collect("fixe"),
            "variable":      self._collect("variable"),
            "note":          self._get_note(),
        }

    def _compute_solde_final(self, payload, use_reel):
        f = "reel" if use_reel else "prevoir"
        rev = sum(r[f] for r in payload["revenu"])
        dep = (sum(r[f] for r in payload["fixe"]) +
               sum(r[f] for r in payload["variable"]))
        return round(payload["solde_initial"] + rev - dep, 2)

    def _carry_balance(self, payload):
        solde_final = self._compute_solde_final(payload, use_reel=self._is_bilan())
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
                ps += self._to_float(r["prevoir"].get())
                rs += self._to_float(r["reel"].get())
            return ps, rs

        rev_p, rev_r = totals("revenu")
        fix_p, fix_r = totals("fixe")
        var_p, var_r = totals("variable")
        dep_p, dep_r = fix_p + var_p, fix_r + var_r
        epg_p, epg_r = rev_p - dep_p, rev_r - dep_r

        bilan      = self._is_bilan()
        solde_init = self._to_float(self._solde_var.get())
        rv, dv, ev = (rev_r, dep_r, epg_r) if bilan else (rev_p, dep_p, epg_p)

        def fmt(v):
            s = "-" if v < 0 else ""
            return f"{s}{abs(v):,.2f} €".replace(",", " ")

        self._card_rev._val.config(text=fmt(rv), fg=GREEN if rv >= 0 else RED)
        self._card_dep._val.config(text=fmt(dv), fg=RED   if dv >  0 else GREEN)
        self._card_epg._val.config(text=fmt(ev), fg=GREEN if ev >= 0 else RED)

        for key, pv, rv2 in (("revenu",  rev_p, rev_r),
                              ("fixe",    fix_p, fix_r),
                              ("variable",var_p, var_r)):
            if key in self._section_total_labels:
                self._section_total_labels[key].config(
                    text=fmt(rv2 if bilan else pv))

        solde_final = solde_init + ev
        self._lbl_solde_final.config(
            text=fmt(solde_final),
            fg=GREEN if solde_final >= 0 else RED)

        # patrimoine
        total_actifs = sum(self._to_float(v.get()) for v in self._actifs_vars.values())
        total_dettes = sum(self._to_float(r["montant"].get()) for r in self._dette_rows)
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

    # ── HTML / PDF export ─────────────────────────────────────────────────────

    def _export_html(self):
        payload  = self._build_payload()
        bilan    = self._is_bilan()
        field    = "reel" if bilan else "prevoir"
        mode_lbl = "Bilan" if bilan else "Prévision"
        month_lbl = f"{MONTHS_FR[self.view_month]} {self.view_year}"

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

        actifs = payload.get("actifs", {})
        ta     = sum(actifs.values())
        dettes = payload.get("dettes", [])
        td     = sum(d["montant"] for d in dettes)
        pat    = ta - td

        mode_bg = "#1A5276" if bilan else "#784212"

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
            note_html = (f"<h3>Notes</h3>"
                         f"<p style='white-space:pre-wrap'>{note_val}</p>")

        dettes_rows = "".join(
            f"<tr><td>{d['label']}</td>"
            f"<td style='text-align:right'>{fmt(d['montant'])}</td></tr>"
            for d in dettes)

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Finance {month_lbl}</title>
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
  <div class="card"><div class="t">Revenus</div>
    <div class="v" style="color:{color(rev)}">{fmt(rev)}</div></div>
  <div class="card"><div class="t">Dépenses</div>
    <div class="v" style="color:{color(dep, invert=True)}">{fmt(dep)}</div></div>
  <div class="card"><div class="t">Épargne</div>
    <div class="v" style="color:{color(epg)}">{fmt(epg)}</div></div>
</div>

<div class="solde-bar">
  <span>Solde début : <b style="color:{color(si)}">{fmt(si)}</b></span>
  <span>Solde fin : <b style="color:{color(sf)}">{fmt(sf)}</b></span>
</div>

<div class="pat-box">
  <h3 class="pat" style="margin-top:0">Patrimoine</h3>
  <table>
    <tr><td>Compte bancaire</td><td style="text-align:right">{fmt(actifs.get('compte',0))}</td></tr>
    <tr><td>Tricount</td><td style="text-align:right">{fmt(actifs.get('tricount',0))}</td></tr>
    <tr><td>eToro</td><td style="text-align:right">{fmt(actifs.get('etoro',0))}</td></tr>
    <tr class="tot"><td>Total actifs</td><td style="text-align:right;color:{color(ta)}">{fmt(ta)}</td></tr>
  </table>
  <table>{dettes_rows}
    <tr class="tot"><td>Total dettes</td><td style="text-align:right;color:#E74C3C">{fmt(td)}</td></tr>
  </table>
  <div class="pat-net" style="color:{color(pat)}">Patrimoine net : {fmt(pat)}</div>
</div>

<h3>Revenus</h3>
<table>{rows_html(payload['revenu'])}
<tr class="tot"><td>Total</td><td style="text-align:right">{fmt(rev)}</td></tr></table>

<h3 class="fixe">Dépenses fixes</h3>
<table>{rows_html(payload['fixe'])}
<tr class="tot"><td>Total</td><td style="text-align:right">{fmt(fix)}</td></tr></table>

<h3 class="var">Dépenses variables</h3>
<table>{rows_html(payload['variable'])}
<tr class="tot"><td>Total</td><td style="text-align:right">{fmt(var)}</td></tr></table>

{note_html}
<p style="color:#bbb;font-size:11px;margin-top:40px">Finarix</p>
</body></html>"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html',
                                         delete=False, encoding='utf-8') as f:
            f.write(html)
            tmp = f.name
        webbrowser.open(f"file:///{tmp.replace(os.sep, '/')}")


# ─── Apply-to-future dialog ───────────────────────────────────────────────────

class ApplyForwardDialog(tk.Toplevel):
    def __init__(self, parent, payload, base_year, base_month):
        super().__init__(parent)
        self.parent     = parent
        self.payload    = payload
        self.base_year  = base_year
        self.base_month = base_month
        self.title("Appliquer aux mois suivants")
        self.geometry("500x600")
        self.minsize(460, 400)
        self.resizable(True, True)
        self.configure(bg=BG)
        self.grab_set()
        self.transient(parent)
        self._row_vars = {"revenu": [], "fixe": [], "variable": []}
        self._build()
        self.wait_window()

    def _build(self):
        tk.Label(self, text="Appliquer aux mois suivants ?",
                 bg=BG, font=("Segoe UI", 12, "bold"), fg="#222"
                 ).pack(pady=(14, 2))
        tk.Label(self, text="Cochez les lignes à copier dans les mois futurs :",
                 bg=BG, font=("Segoe UI", 9), fg="#777"
                 ).pack(pady=(0, 6))

        scr_outer = tk.Frame(self, bg=BG)
        scr_outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 4))
        self._scr = tk.Canvas(scr_outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(scr_outer, orient=tk.VERTICAL, command=self._scr.yview)
        self._scr.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._scr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inner = tk.Frame(self._scr, bg=BG)
        win   = self._scr.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda _e: self._scr.configure(scrollregion=self._scr.bbox("all")))
        self._scr.bind("<Configure>",
                       lambda _e: self._scr.itemconfig(win, width=_e.width))
        self._scr.bind("<Enter>",
                       lambda _e: self._scr.bind_all("<MouseWheel>", self._mw))
        self._scr.bind("<Leave>",
                       lambda _e: self._scr.unbind_all("<MouseWheel>"))

        for key in ("revenu", "fixe", "variable"):
            self._build_group(inner, key)

        misc = tk.Frame(inner, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=12, pady=6)
        misc.pack(fill=tk.X, pady=(8, 2))
        self._var_solde = tk.BooleanVar(value=False)
        self._var_note  = tk.BooleanVar(value=False)
        for var, label in ((self._var_solde, "Solde de début de mois"),
                           (self._var_note,  "Notes")):
            tk.Checkbutton(misc, text=label, variable=var, bg=CARD_BG,
                           font=("Segoe UI", 10), fg="#444",
                           activebackground=CARD_BG, anchor="w"
                           ).pack(fill=tk.X, pady=1)

        bot = tk.Frame(self, bg="#E8EAED", padx=16, pady=8)
        bot.pack(fill=tk.X, side=tk.BOTTOM)
        uf = tk.Frame(bot, bg="#E8EAED")
        uf.pack(fill=tk.X, pady=(0, 8))
        tk.Label(uf, text="Jusqu'au mois de :", bg="#E8EAED",
                 font=("Segoe UI", 10, "bold"), fg="#333").pack(side=tk.LEFT)
        self._months_list = self._future_months()
        labels = [x[2] for x in self._months_list]
        self._until_var = tk.StringVar()
        dec_lbl = f"Décembre {self.base_year}"
        self._until_var.set(dec_lbl if dec_lbl in labels else labels[-1])
        om = tk.OptionMenu(uf, self._until_var, *labels)
        om.config(font=("Segoe UI", 10), bg=CARD_BG, relief=tk.SOLID, width=18)
        om.pack(side=tk.LEFT, padx=10)
        bf = tk.Frame(bot, bg="#E8EAED")
        bf.pack()
        tk.Button(bf, text="Ignorer", bg="#BDC3C7", fg="#333",
                  font=("Segoe UI", 10), relief=tk.FLAT, padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text="  Appliquer  ", bg=ACCENT, fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=16, pady=6,
                  activebackground="#1f638d", cursor="hand2",
                  command=self._apply).pack(side=tk.LEFT, padx=6)

    def _build_group(self, parent, key):
        color = SECTION_COLORS[key]
        rows  = self.payload[key]
        wrap  = tk.Frame(parent, bg=BG)
        wrap.pack(fill=tk.X, pady=(4, 0))
        hdr = tk.Frame(wrap, bg=color, padx=8, pady=4)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=SECTION_TITLES[key], bg=color, fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        toggle_btn = tk.Button(hdr, text="Aucun", bg=color, fg="white",
                               font=("Segoe UI", 8), relief=tk.FLAT,
                               cursor="hand2", bd=0, padx=8,
                               activebackground=color, activeforeground="white")
        toggle_btn.pack(side=tk.RIGHT)
        rows_frame = tk.Frame(wrap, bg=CARD_BG, relief=tk.SOLID, bd=1)
        rows_frame.pack(fill=tk.X)
        row_vars = []
        for i, row in enumerate(rows):
            if i > 0:
                tk.Frame(rows_frame, bg=BORDER, height=1).pack(fill=tk.X, padx=8)
            rf = tk.Frame(rows_frame, bg=CARD_BG, padx=8, pady=4)
            rf.pack(fill=tk.X)
            v = tk.BooleanVar(value=True)
            row_vars.append(v)
            amount = f"{row['prevoir']:,.2f} €".replace(",", " ")
            tk.Label(rf, text=amount, bg=CARD_BG, font=("Segoe UI", 10),
                     fg="#555").pack(side=tk.RIGHT)
            tk.Checkbutton(rf, text=row["label"], variable=v, bg=CARD_BG,
                           font=("Segoe UI", 10), fg="#222",
                           activebackground=CARD_BG, anchor="w"
                           ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._row_vars[key] = row_vars

        def _toggle(btn=toggle_btn, vlist=row_vars):
            all_on = all(v.get() for v in vlist)
            for v in vlist: v.set(not all_on)
            btn.config(text="Tout" if all_on else "Aucun")
        toggle_btn.config(command=_toggle)

    def _mw(self, event):
        self._scr.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _future_months(self):
        result, y, m = [], *next_ym(self.base_year, self.base_month)
        end_y = self.base_year + 1
        while y < end_y or (y == end_y and m <= 12):
            result.append((y, m, f"{MONTHS_FR[m]} {y}"))
            y, m = next_ym(y, m)
        return result

    def _apply(self):
        chosen   = self._until_var.get()
        until    = next((t for t in self._months_list if t[2] == chosen), None)
        if not until: self.destroy(); return
        until_ym = (until[0], until[1])
        selected = {key: [dict(row, reel=0.0)
                          for row, var in zip(self.payload[key], self._row_vars[key])
                          if var.get()]
                    for key in ("revenu", "fixe", "variable")}
        do_sold = self._var_solde.get()
        do_note = self._var_note.get()
        y, m = next_ym(self.base_year, self.base_month)
        while (y, m) <= until_ym:
            tgt = load_month_file(y, m) or copy.deepcopy(DEFAULT_DATA)
            for key in ("revenu", "fixe", "variable"):
                if selected[key]:
                    tgt[key] = copy.deepcopy(selected[key])
            if do_sold: tgt["solde_initial"] = self.payload["solde_initial"]
            if do_note: tgt["note"]          = self.payload["note"]
            save_month_file(y, m, tgt)
            y, m = next_ym(y, m)
        self.destroy()


# ─── entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = FinanceApp()
    app.mainloop()
