import tkinter as tk
from datetime import date

from finarix.config import BG
from finarix.ui_mixin import UIBuildMixin
from finarix.logic_mixin import AppLogicMixin
from finarix import storage, i18n
from finarix.dialogs.login import LoginDialog


class FinanceApp(UIBuildMixin, AppLogicMixin, tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.withdraw()  # hide until login succeeds

        # Load language preference before showing login dialog
        i18n.load_lang(storage.data_dir())

        key = LoginDialog(self).run()
        if key is None:
            self.destroy()
            return

        storage.set_key(key)

        self.title("Finarix")
        self.geometry("880x760")
        self.minsize(740, 560)
        self.configure(bg=BG)

        today = date.today()
        self.view_year  = today.year
        self.view_month = today.month
        self._today     = today

        self._bilan_editing = False

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

        self._build_ui()
        self._load_month()
        self.deiconify()
