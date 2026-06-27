import tkinter as tk

from finarix.config import BG, CARD_BG, ACCENT, HDR_BG, HDR_FG, RED
from finarix.storage import data_dir
from finarix import auth


class LoginDialog:
    def __init__(self, root: tk.Tk):
        self._root  = root
        self._key   = None
        self._ddir  = data_dir()

        self._win = tk.Toplevel(root)
        self._win.title("Finarix")
        self._win.resizable(False, False)
        self._win.configure(bg=BG)
        self._win.grab_set()
        self._win.protocol("WM_DELETE_WINDOW", self._on_close)

        self._is_setup = not auth.is_configured(self._ddir)
        if self._is_setup:
            self._build_setup()
        else:
            self._build_login()

        self._center(self._win)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _center(win: tk.Toplevel):
        win.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        x = (win.winfo_screenwidth()  - w) // 2
        y = (win.winfo_screenheight() - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _header(self, subtitle: str):
        hdr = tk.Frame(self._win, bg=HDR_BG, padx=24, pady=16)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Finarix", bg=HDR_BG, fg=HDR_FG,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(hdr, text=subtitle, bg=HDR_BG, fg="#90A4B0",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

    def _pw_field(self, parent: tk.Frame, label: str, var: tk.StringVar,
                  on_return=None) -> tk.Entry:
        tk.Label(parent, text=label, bg=BG, fg="#555",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(12, 2))
        row = tk.Frame(parent, bg=BG)
        row.pack(fill=tk.X)
        entry = tk.Entry(row, textvariable=var, show="●",
                         font=("Segoe UI", 11), relief=tk.SOLID, bd=1,
                         bg=CARD_BG, fg="#222")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=7)
        if on_return:
            entry.bind("<Return>", lambda _: on_return())
        return entry

    # ── login mode ────────────────────────────────────────────────────────────

    def _build_login(self):
        self._header("Entrez votre mot de passe pour accéder à vos données")
        body = tk.Frame(self._win, bg=BG, padx=28, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        self._pw_var = tk.StringVar()
        e = self._pw_field(body, "Mot de passe", self._pw_var,
                           on_return=self._do_login)
        e.focus_set()

        self._err_lbl = tk.Label(body, text="", bg=BG, fg=RED,
                                  font=("Segoe UI", 9))
        self._err_lbl.pack(anchor="w", pady=(8, 0))

        tk.Button(body, text="  Se connecter  ", bg=ACCENT, fg="white",
                  font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
                  padx=20, pady=8, cursor="hand2",
                  activebackground="#1f638d",
                  command=self._do_login).pack(pady=(12, 16))

    def _do_login(self):
        pw = self._pw_var.get()
        if not pw:
            self._err_lbl.config(text="Veuillez entrer votre mot de passe.")
            return
        key = auth.verify_password(pw, self._ddir)
        if key is None:
            self._err_lbl.config(text="Mot de passe incorrect.")
            self._pw_var.set("")
            return
        self._key = key
        self._win.destroy()

    # ── first-time setup mode ─────────────────────────────────────────────────

    def _build_setup(self):
        self._header("Première connexion — créez votre mot de passe")
        body = tk.Frame(self._win, bg=BG, padx=28, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        self._pw_var  = tk.StringVar()
        self._pw2_var = tk.StringVar()

        e1 = self._pw_field(body, "Nouveau mot de passe", self._pw_var)
        e1.focus_set()
        self._pw_field(body, "Confirmer le mot de passe", self._pw2_var,
                       on_return=self._do_setup)

        self._err_lbl = tk.Label(body, text="", bg=BG, fg=RED,
                                  font=("Segoe UI", 9))
        self._err_lbl.pack(anchor="w", pady=(8, 0))

        tk.Button(body, text="  Créer le compte  ", bg="#27AE60", fg="white",
                  font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
                  padx=20, pady=8, cursor="hand2",
                  activebackground="#1E8449",
                  command=self._do_setup).pack(pady=(12, 16))

    def _do_setup(self):
        pw  = self._pw_var.get()
        pw2 = self._pw2_var.get()
        if not pw:
            self._err_lbl.config(text="Le mot de passe ne peut pas être vide.")
            return
        if len(pw) < 4:
            self._err_lbl.config(
                text="Mot de passe trop court (minimum 4 caractères).")
            return
        if pw != pw2:
            self._err_lbl.config(
                text="Les mots de passe ne correspondent pas.")
            return
        key = auth.setup_password(pw, self._ddir)
        auth.migrate_existing_files(key, self._ddir)
        self._key = key
        self._win.destroy()

    # ── close ─────────────────────────────────────────────────────────────────

    def _on_close(self):
        self._key = None
        self._win.destroy()

    def run(self):
        self._win.wait_window()
        return self._key
