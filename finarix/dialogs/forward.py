import copy
import tkinter as tk

from finarix.config import (
    BG, CARD_BG, BORDER, ACCENT,
    SECTION_COLORS, DEFAULT_DATA,
)
from finarix.storage import load_month_file, save_month_file, next_ym
from finarix import i18n


class ApplyForwardDialog(tk.Toplevel):
    def __init__(self, parent, payload, base_year, base_month):
        super().__init__(parent)
        self.parent     = parent
        self.payload    = payload
        self.base_year  = base_year
        self.base_month = base_month
        self.title(i18n.t("fwd_title"))
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
        tk.Label(self, text=i18n.t("fwd_title"),
                 bg=BG, font=("Segoe UI", 12, "bold"), fg="#222"
                 ).pack(pady=(14, 2))
        tk.Label(self, text=i18n.t("fwd_subtitle"),
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
        for var, label in ((self._var_solde, i18n.t("fwd_solde")),
                           (self._var_note,  i18n.t("fwd_notes"))):
            tk.Checkbutton(misc, text=label, variable=var, bg=CARD_BG,
                           font=("Segoe UI", 10), fg="#444",
                           activebackground=CARD_BG, anchor="w"
                           ).pack(fill=tk.X, pady=1)

        bot = tk.Frame(self, bg="#E8EAED", padx=16, pady=8)
        bot.pack(fill=tk.X, side=tk.BOTTOM)
        uf = tk.Frame(bot, bg="#E8EAED")
        uf.pack(fill=tk.X, pady=(0, 8))
        tk.Label(uf, text=i18n.t("fwd_until"), bg="#E8EAED",
                 font=("Segoe UI", 10, "bold"), fg="#333").pack(side=tk.LEFT)
        self._months_list = self._future_months()
        labels = [x[2] for x in self._months_list]
        self._until_var = tk.StringVar()
        mnths = i18n.months()
        dec_lbl = f"{mnths[12]} {self.base_year}"
        self._until_var.set(dec_lbl if dec_lbl in labels else labels[-1])
        om = tk.OptionMenu(uf, self._until_var, *labels)
        om.config(font=("Segoe UI", 10), bg=CARD_BG, relief=tk.SOLID, width=18)
        om.pack(side=tk.LEFT, padx=10)
        bf = tk.Frame(bot, bg="#E8EAED")
        bf.pack()
        tk.Button(bf, text=i18n.t("btn_ignore"), bg="#BDC3C7", fg="#333",
                  font=("Segoe UI", 10), relief=tk.FLAT, padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text=i18n.t("btn_apply"), bg=ACCENT, fg="white",
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
        tk.Label(hdr, text=i18n.t(f"sec_{key}"), bg=color, fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        toggle_btn = tk.Button(hdr, text=i18n.t("btn_none"), bg=color, fg="white",
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
            amount = f"{row['prevoir']:,.2f} €".replace(",", " ")
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
            btn.config(text=i18n.t("btn_all") if all_on else i18n.t("btn_none"))
        toggle_btn.config(command=_toggle)

    def _mw(self, event):
        self._scr.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _future_months(self):
        mnths  = i18n.months()
        result, y, m = [], *next_ym(self.base_year, self.base_month)
        end_y = self.base_year + 1
        while y < end_y or (y == end_y and m <= 12):
            result.append((y, m, f"{mnths[m]} {y}"))
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
