import json
import os

_LANG = "fr"

LANGS = [("fr", "FR"), ("en", "EN"), ("vi", "VI")]

_MONTHS = {
    "fr": ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
           'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'],
    "en": ['', 'January', 'February', 'March', 'April', 'May', 'June',
           'July', 'August', 'September', 'October', 'November', 'December'],
    "vi": ['', 'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
           'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'],
}

_T = {
    # ── navigation ────────────────────────────────────────────────────────────
    "mode_bilan":    {"fr": "  Bilan  ",    "en": "  Balance  ",  "vi": "  Quyết toán  "},
    "mode_prevision":{"fr": "  Prévision  ","en": "  Forecast  ", "vi": "  Dự báo  "},

    # ── solde bar ─────────────────────────────────────────────────────────────
    "solde_debut":   {"fr": "Solde début de mois :", "en": "Opening balance :",  "vi": "Số dư đầu tháng :"},
    "solde_fin":     {"fr": "Solde fin de mois :",   "en": "Closing balance :",  "vi": "Số dư cuối tháng :"},

    # ── summary cards ─────────────────────────────────────────────────────────
    "card_revenus":  {"fr": "Revenus",  "en": "Income",   "vi": "Thu nhập"},
    "card_depenses": {"fr": "Dépenses", "en": "Expenses", "vi": "Chi tiêu"},
    "card_epargne":  {"fr": "Épargne",  "en": "Savings",  "vi": "Tiết kiệm"},

    # ── section titles ────────────────────────────────────────────────────────
    "sec_revenu":    {"fr": "Revenus",            "en": "Income",           "vi": "Thu nhập"},
    "sec_fixe":      {"fr": "Dépenses fixes",     "en": "Fixed expenses",   "vi": "Chi phí cố định"},
    "sec_variable":  {"fr": "Dépenses variables", "en": "Variable expenses","vi": "Chi phí biến động"},

    # ── column headers ────────────────────────────────────────────────────────
    "col_prevoir":   {"fr": "Prévoir (€)", "en": "Planned (€)", "vi": "Dự kiến (€)"},
    "col_reel":      {"fr": "Réel (€)",    "en": "Actual (€)",  "vi": "Thực tế (€)"},

    # ── compte bancaire block ─────────────────────────────────────────────────
    "cb_titre":    {"fr": "Compte bancaire",        "en": "Bank account",        "vi": "Tài khoản ngân hàng"},
    "cb_debut":    {"fr": "Début de mois :",         "en": "Month opening :",     "vi": "Đầu tháng :"},
    "cb_fin":      {"fr": "Fin de mois :",           "en": "Month closing :",     "vi": "Cuối tháng :"},
    "cb_calcule":  {"fr": "Calculé :",               "en": "Calculated :",        "vi": "Tính toán :"},
    "cb_ecart":    {"fr": "Écart :",                 "en": "Difference :",        "vi": "Chênh lệch :"},

    # ── patrimoine ────────────────────────────────────────────────────────────
    "pat_titre":           {"fr": "Tổng tài sản — Patrimoine", "en": "Net Worth",           "vi": "Tổng tài sản"},
    "pat_actifs":          {"fr": "Actifs",                     "en": "Assets",              "vi": "Tài sản"},
    "pat_total_actifs":    {"fr": "Total actifs :",             "en": "Total assets :",      "vi": "Tổng tài sản :"},
    "pat_dettes":          {"fr": "Dettes",                     "en": "Liabilities",         "vi": "Khoản nợ"},
    "pat_total_dettes":    {"fr": "Total dettes :",             "en": "Total liab. :",        "vi": "Tổng nợ :"},
    "pat_net":             {"fr": "Patrimoine net :",            "en": "Net worth :",          "vi": "Tài sản ròng :"},

    # ── notes ─────────────────────────────────────────────────────────────────
    "notes":         {"fr": " Notes ", "en": " Notes ", "vi": " Ghi chú "},

    # ── bottom buttons ────────────────────────────────────────────────────────
    "btn_modifier":       {"fr": "  Modifier  ",           "en": "  Edit  ",          "vi": "  Chỉnh sửa  "},
    "btn_enregistrer":    {"fr": "  Enregistrer  ",        "en": "  Save  ",          "vi": "  Lưu  "},
    "btn_pdf":            {"fr": "  Exporter PDF  ",       "en": "  Export PDF  ",    "vi": "  Xuất PDF  "},
    "btn_save_data":      {"fr": "  Sauvegarder données  ","en": "  Backup data  ",   "vi": "  Sao lưu  "},
    "btn_restore_data":   {"fr": "  Restaurer données  ", "en": "  Restore data  ",  "vi": "  Khôi phục  "},
    "btn_add_row":        {"fr": "+ Ajouter une ligne",    "en": "+ Add row",         "vi": "+ Thêm dòng"},
    "btn_add_dette":      {"fr": "+ Ajouter une dette",    "en": "+ Add debt",        "vi": "+ Thêm khoản nợ"},
    "btn_add_actif":      {"fr": "+ Ajouter un actif",     "en": "+ Add asset",       "vi": "+ Thêm tài sản"},
    "section_total":      {"fr": "Total :",                "en": "Total :",           "vi": "Tổng :"},

    # ── login dialog ──────────────────────────────────────────────────────────
    "login_subtitle":  {"fr": "Entrez votre mot de passe pour accéder à vos données",
                        "en": "Enter your password to access your data",
                        "vi": "Nhập mật khẩu để truy cập dữ liệu của bạn"},
    "setup_subtitle":  {"fr": "Première connexion — créez votre mot de passe",
                        "en": "First login — create your password",
                        "vi": "Lần đầu đăng nhập — tạo mật khẩu của bạn"},
    "lbl_password":    {"fr": "Mot de passe",             "en": "Password",          "vi": "Mật khẩu"},
    "lbl_new_pw":      {"fr": "Nouveau mot de passe",     "en": "New password",      "vi": "Mật khẩu mới"},
    "lbl_confirm_pw":  {"fr": "Confirmer le mot de passe","en": "Confirm password",  "vi": "Xác nhận mật khẩu"},
    "btn_login":       {"fr": "  Se connecter  ",         "en": "  Log in  ",        "vi": "  Đăng nhập  "},
    "btn_create_acc":  {"fr": "  Créer le compte  ",      "en": "  Create account  ","vi": "  Tạo tài khoản  "},
    "err_empty_pw":    {"fr": "Veuillez entrer votre mot de passe.",
                        "en": "Please enter your password.",
                        "vi": "Vui lòng nhập mật khẩu."},
    "err_wrong_pw":    {"fr": "Mot de passe incorrect.",
                        "en": "Incorrect password.",
                        "vi": "Mật khẩu không đúng."},
    "err_empty_new_pw":{"fr": "Le mot de passe ne peut pas être vide.",
                        "en": "Password cannot be empty.",
                        "vi": "Mật khẩu không được để trống."},
    "err_short_pw":    {"fr": "Mot de passe trop court (minimum 4 caractères).",
                        "en": "Password too short (minimum 4 characters).",
                        "vi": "Mật khẩu quá ngắn (tối thiểu 4 ký tự)."},
    "err_pw_mismatch": {"fr": "Les mots de passe ne correspondent pas.",
                        "en": "Passwords do not match.",
                        "vi": "Mật khẩu không khớp."},

    # ── forward dialog ────────────────────────────────────────────────────────
    "fwd_title":    {"fr": "Appliquer aux mois suivants ?",
                     "en": "Apply to following months?",
                     "vi": "Áp dụng cho các tháng tiếp theo?"},
    "fwd_subtitle": {"fr": "Cochez les lignes à copier dans les mois futurs :",
                     "en": "Check rows to copy to future months:",
                     "vi": "Chọn dòng cần sao chép sang các tháng tới :"},
    "fwd_solde":    {"fr": "Solde de début de mois", "en": "Opening balance",  "vi": "Số dư đầu tháng"},
    "fwd_notes":    {"fr": "Notes",                  "en": "Notes",            "vi": "Ghi chú"},
    "fwd_until":    {"fr": "Jusqu'au mois de :",     "en": "Until month:",     "vi": "Đến tháng:"},
    "btn_ignore":   {"fr": "Ignorer",                "en": "Skip",             "vi": "Bỏ qua"},
    "btn_apply":    {"fr": "  Appliquer  ",          "en": "  Apply  ",        "vi": "  Áp dụng  "},
    "btn_all":      {"fr": "Tout",                   "en": "All",              "vi": "Tất cả"},
    "btn_none":     {"fr": "Aucun",                  "en": "None",             "vi": "Không"},

    # ── backup / restore ──────────────────────────────────────────────────────
    "dlg_backup_title":  {"fr": "Sauvegarder toutes les données",
                          "en": "Backup all data",
                          "vi": "Sao lưu tất cả dữ liệu"},
    "dlg_backup_file":   {"fr": "Finarix_sauvegarde.zip", "en": "Finarix_backup.zip", "vi": "Finarix_sao_luu.zip"},
    "dlg_backup_ok":     {"fr": "Sauvegarde réussie",     "en": "Backup successful",  "vi": "Sao lưu thành công"},
    "dlg_backup_msg":    {"fr": "{n} mois exportés vers :\n{path}",
                          "en": "{n} months exported to:\n{path}",
                          "vi": "{n} tháng đã xuất sang:\n{path}"},
    "dlg_restore_title": {"fr": "Restaurer les données",  "en": "Restore data",       "vi": "Khôi phục dữ liệu"},
    "dlg_restore_ok":    {"fr": "Restauration réussie",   "en": "Restore successful", "vi": "Khôi phục thành công"},
    "dlg_restore_msg":   {"fr": "{n} mois importés.",     "en": "{n} months imported.","vi": "{n} tháng đã nhập."},
    "dlg_confirm_title": {"fr": "Confirmer la restauration","en": "Confirm restore",  "vi": "Xác nhận khôi phục"},
    "dlg_confirm_msg":   {"fr": "Les données existantes seront remplacées.\n\nContinuer ?",
                          "en": "Existing data will be replaced.\n\nContinue?",
                          "vi": "Dữ liệu hiện tại sẽ bị thay thế.\n\nTiếp tục?"},
    "dlg_error":         {"fr": "Erreur", "en": "Error", "vi": "Lỗi"},
    "ft_zip":            {"fr": "Archive ZIP", "en": "ZIP Archive", "vi": "File ZIP"},

    # ── HTML export ───────────────────────────────────────────────────────────
    "html_bilan":        {"fr": "Bilan",      "en": "Balance",  "vi": "Quyết toán"},
    "html_prevision":    {"fr": "Prévision",  "en": "Forecast", "vi": "Dự báo"},
    "html_revenus":      {"fr": "Revenus",    "en": "Income",   "vi": "Thu nhập"},
    "html_depenses":     {"fr": "Dépenses",   "en": "Expenses", "vi": "Chi tiêu"},
    "html_epargne":      {"fr": "Épargne",    "en": "Savings",  "vi": "Tiết kiệm"},
    "html_solde_debut":  {"fr": "Solde début :", "en": "Opening:", "vi": "Đầu tháng:"},
    "html_solde_fin":    {"fr": "Solde fin :",   "en": "Closing:", "vi": "Cuối tháng:"},
    "html_cb":           {"fr": "Compte bancaire", "en": "Bank account",     "vi": "Tài khoản ngân hàng"},
    "html_cb_ecart":     {"fr": "Écart",           "en": "Difference",       "vi": "Chênh lệch"},
    "html_patrimoine":   {"fr": "Patrimoine",       "en": "Net Worth",        "vi": "Tài sản ròng"},
    "html_total_actifs": {"fr": "Total actifs",   "en": "Total assets",     "vi": "Tổng tài sản"},
    "html_total_dettes": {"fr": "Total dettes",   "en": "Total liabilities","vi": "Tổng nợ"},
    "html_pat_net":      {"fr": "Patrimoine net :","en": "Net worth:",       "vi": "Tài sản ròng:"},
    "html_total":        {"fr": "Total",           "en": "Total",            "vi": "Tổng"},
    "html_notes":        {"fr": "Notes",           "en": "Notes",            "vi": "Ghi chú"},
    "html_sec_revenu":   {"fr": "Revenus",          "en": "Income",           "vi": "Thu nhập"},
    "html_sec_fixe":     {"fr": "Dépenses fixes",   "en": "Fixed expenses",   "vi": "Chi phí cố định"},
    "html_sec_variable": {"fr": "Dépenses variables","en": "Variable expenses","vi": "Chi phí biến động"},
}


def t(key: str) -> str:
    return _T.get(key, {}).get(_LANG, _T.get(key, {}).get("fr", key))


def months() -> list:
    return _MONTHS.get(_LANG, _MONTHS["fr"])


def set_lang(lang: str) -> None:
    global _LANG
    if lang in _MONTHS:
        _LANG = lang


def get_lang() -> str:
    return _LANG


def load_lang(data_directory: str) -> None:
    path = os.path.join(data_directory, "prefs.json")
    try:
        with open(path, encoding="utf-8") as f:
            prefs = json.load(f)
        set_lang(prefs.get("lang", "fr"))
    except Exception:
        pass


def save_lang(data_directory: str) -> None:
    path = os.path.join(data_directory, "prefs.json")
    try:
        os.makedirs(data_directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"lang": _LANG}, f)
    except Exception:
        pass
