import os
import subprocess
import yaml
import tkinter as tk
from tkinter import messagebox
from icon_data import ICON_BASE64
import base64

CONFIG_FILE = "pw-soulkeeper.yml"

# ========================
# Backend
# ========================
class PWBackend:
    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = config_path
        self.init_config()

    def init_config(self):
        if not os.path.exists(self.config_path):
            default_config = {
                "settings": {"game_path": "", "client_exe": ""},
                "characters": [],
                "groups": []
            }
            self.save_config(default_config)

    def get_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def save_config(self, config):
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, allow_unicode=True)

    def starter(self, game_path, element_exe, accounts):
        os.chdir(game_path)
        element_path = os.path.join(game_path, element_exe)
        for acc in accounts:
            subprocess.Popen([
                element_path,
                "startbypatcher",
                "game:cpw",
                "console:1",
                f"user:{acc['user']}",
                f"pwd:{acc['pwd']}",
                f"role:{acc['role']}"
            ], shell=True)

    # --- Characters ---
    def add_character(self, name, user, pwd, role):
        config = self.get_config()
        config["characters"].append({"name": name, "user": user, "pwd": pwd, "role": role})
        self.save_config(config)

    def update_character(self, old_name, name, user, pwd, role):
        config = self.get_config()
        for c in config["characters"]:
            if c["name"] == old_name:
                c.update({"name": name, "user": user, "pwd": pwd, "role": role})
        # Обновляем группы при переименовании персонажа
        for g in config.get("groups", []):
            g["characters"] = [name if x==old_name else x for x in g["characters"]]
        self.save_config(config)

    def delete_character(self, name):
        config = self.get_config()
        config["characters"] = [c for c in config["characters"] if c["name"] != name]
        for g in config.get("groups", []):
            g["characters"] = [c for c in g["characters"] if c != name]
        self.save_config(config)

    # --- Groups ---
    def add_group(self, name, chars):
        config = self.get_config()
        config["groups"].append({"name": name, "characters": chars})
        self.save_config(config)

    def update_group(self, old_name, name, chars):
        config = self.get_config()
        for g in config["groups"]:
            if g["name"] == old_name:
                g.update({"name": name, "characters": chars})
        self.save_config(config)

    def delete_group(self, name):
        config = self.get_config()
        config["groups"] = [g for g in config["groups"] if g["name"] != name]
        self.save_config(config)

# ========================
# GUI
# ========================
class PWSoulkeeperGUI:
    def __init__(self, root, backend: PWBackend):
        self.root = root
        self.backend = backend
        self.root.title("PW SoulKeeper")
        self.root.geometry("500x600")

        self.setup_tabs()
        self.setup_characters_page()
        self.setup_groups_page()
        self.setup_settings_page()

        self.show_page(self.page_characters)
        self.refresh_characters()
        self.refresh_groups()
        self.load_settings()

    # ------------------------
    # Tabs
    # ------------------------
    def setup_tabs(self):
        self.page_characters = tk.Frame(self.root)
        self.page_groups = tk.Frame(self.root)
        self.page_settings = tk.Frame(self.root)
        for frame in (self.page_characters, self.page_groups, self.page_settings):
            frame.grid(row=1, column=0, sticky="nsew")

        top_frame = tk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="ew")
        self.tab_chars = tk.Button(top_frame, text="👤 Персонажи", command=lambda: self.show_page(self.page_characters))
        self.tab_groups = tk.Button(top_frame, text="🗂️ Группы", command=lambda: self.show_page(self.page_groups))
        self.tab_settings = tk.Button(top_frame, text="⚙️ Настройки", command=lambda: self.show_page(self.page_settings))
        self.tab_chars.pack(side="left")
        self.tab_groups.pack(side="left")
        self.tab_settings.pack(side="left")

    def show_page(self, page):
        self.tab_chars.config(relief="raised")
        self.tab_groups.config(relief="raised")
        self.tab_settings.config(relief="raised")
        if page == self.page_characters:
            self.tab_chars.config(relief="sunken")
        elif page == self.page_groups:
            self.tab_groups.config(relief="sunken")
        else:
            self.tab_settings.config(relief="sunken")
        page.tkraise()

    # ========================
    # Page 1: Characters
    # ========================
    def setup_characters_page(self):
        self.characters_frame = tk.Frame(self.page_characters)
        self.characters_frame.pack(pady=10, anchor="w", fill="x")

        # Add form
        self.form_frame = tk.Frame(self.page_characters)
        self.name_entry = tk.Entry(self.form_frame)
        self.user_entry = tk.Entry(self.form_frame)
        self.pwd_entry = tk.Entry(self.form_frame)
        self.role_entry = tk.Entry(self.form_frame)
        self.create_form_widgets(self.form_frame, self.name_entry, self.user_entry, self.pwd_entry, self.role_entry,
                                 "Добавить персонажа", self.add_character_gui)

        self.edit_frame = tk.Frame(self.page_characters)
        self.edit_name_entry = tk.Entry(self.edit_frame)
        self.edit_user_entry = tk.Entry(self.edit_frame)
        self.edit_pwd_entry = tk.Entry(self.edit_frame)
        self.edit_role_entry = tk.Entry(self.edit_frame)
        self.create_form_widgets(self.edit_frame, self.edit_name_entry, self.edit_user_entry, self.edit_pwd_entry,
                                 self.edit_role_entry, "Сохранить", self.save_edit_gui, edit_mode=True)

        self.plus_button = tk.Button(self.page_characters, text="➕", command=self.toggle_form, width=3)
        self.plus_button.pack(padx=5, pady=5, anchor="w")

    def create_form_widgets(self, frame, name_e, user_e, pwd_e, role_e, submit_text, submit_command, edit_mode=False):
        tk.Label(frame, text="Имя").grid(row=0, column=0, sticky="w")
        name_e.grid(row=0, column=1)
        tk.Label(frame, text="Логин").grid(row=1, column=0, sticky="w")
        user_e.grid(row=1, column=1)
        tk.Label(frame, text="Пароль").grid(row=2, column=0, sticky="w")
        pwd_e.grid(row=2, column=1)
        tk.Label(frame, text="Роль").grid(row=3, column=0, sticky="w")
        role_e.grid(row=3, column=1)
        row = 4
        tk.Button(frame, text="💾 Сохранить" if edit_mode else "✅ "+submit_text, command=submit_command).grid(row=row, column=0, pady=10)
        if edit_mode:
            tk.Button(frame, text="❌ Отмена", command=self.cancel_edit).grid(row=row, column=1, pady=10)
            tk.Button(frame, text="🗑️ Удалить", command=self.delete_character_gui).grid(row=row, column=2, pady=10, padx=5)

    def toggle_form(self):
        if self.form_frame.winfo_ismapped():
            self.form_frame.pack_forget()
        else:
            self.edit_frame.pack_forget()
            self.form_frame.pack(pady=10, anchor="w")

    def add_character_gui(self):
        name = self.name_entry.get().strip()
        user = self.user_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        role = self.role_entry.get().strip()
        if not (name and user and pwd and role):
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return
        self.backend.add_character(name, user, pwd, role)
        for e in [self.name_entry, self.user_entry, self.pwd_entry, self.role_entry]:
            e.delete(0, tk.END)
        self.form_frame.pack_forget()
        self.refresh_characters()
        self.refresh_groups()

    def edit_character_gui(self, char):
        self.edit_frame.pack(pady=10, anchor="w")
        self.form_frame.pack_forget()
        self.edit_name_entry.delete(0, tk.END)
        self.edit_name_entry.insert(0, char["name"])
        self.edit_user_entry.delete(0, tk.END)
        self.edit_user_entry.insert(0, char["user"])
        self.edit_pwd_entry.delete(0, tk.END)
        self.edit_pwd_entry.insert(0, char["pwd"])
        self.edit_role_entry.delete(0, tk.END)
        self.edit_role_entry.insert(0, char["role"])
        self.current_edit_char = char["name"]

    def save_edit_gui(self):
        name = self.edit_name_entry.get().strip()
        user = self.edit_user_entry.get().strip()
        pwd = self.edit_pwd_entry.get().strip()
        role = self.edit_role_entry.get().strip()
        if not (name and user and pwd and role):
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return
        self.backend.update_character(self.current_edit_char, name, user, pwd, role)
        self.edit_frame.pack_forget()
        self.refresh_characters()
        self.refresh_groups()

    def cancel_edit(self):
        self.edit_frame.pack_forget()

    def delete_character_gui(self):
        answer = messagebox.askyesno("Подтверждение", f"Точно хотите удалить персонажа {self.current_edit_char}?")
        if answer:
            self.backend.delete_character(self.current_edit_char)
            self.edit_frame.pack_forget()
            self.refresh_characters()
            self.refresh_groups()

    def refresh_characters(self):
        for widget in self.characters_frame.winfo_children():
            widget.destroy()
        config = self.backend.get_config()
        for char in config.get("characters", []):
            row_frame = tk.Frame(self.characters_frame)
            row_frame.pack(fill="x", pady=2, padx=5)
            tk.Button(row_frame, text=char["name"], width=20,
                      command=lambda c=char: self.backend.starter(
                          config["settings"]["game_path"], config["settings"]["client_exe"], [c])).pack(side="left")
            tk.Button(row_frame, text="✏️", command=lambda c=char: self.edit_character_gui(c)).pack(side="left", padx=5)

    # ========================
    # Page 2: Groups
    # ========================
    def setup_groups_page(self):
        self.groups_frame = tk.Frame(self.page_groups)
        self.groups_frame.pack(pady=10, anchor="w", fill="x")

        self.group_form_frame = tk.Frame(self.page_groups)
        self.group_name_entry = tk.Entry(self.group_form_frame)
        self.group_chars_frame = tk.Frame(self.group_form_frame)
        tk.Label(self.group_form_frame, text="Название группы").grid(row=0, column=0, sticky="w")
        self.group_name_entry.grid(row=0, column=1)
        tk.Label(self.group_form_frame, text="Персонажи").grid(row=1, column=0, sticky="nw")
        self.group_chars_frame.grid(row=1, column=1, sticky="w")
        tk.Button(self.group_form_frame, text="✅ Добавить группу", command=self.add_group_gui).grid(row=2, column=0, columnspan=2, pady=10)

        self.group_check_vars = {}

        self.edit_group_frame = tk.Frame(self.page_groups)
        self.edit_group_name_entry = tk.Entry(self.edit_group_frame)
        self.edit_group_chars_frame = tk.Frame(self.edit_group_frame)
        tk.Label(self.edit_group_frame, text="Название группы").grid(row=0, column=0, sticky="w")
        self.edit_group_name_entry.grid(row=0, column=1)
        tk.Label(self.edit_group_frame, text="Персонажи").grid(row=1, column=0, sticky="nw")
        self.edit_group_chars_frame.grid(row=1, column=1, sticky="w")
        tk.Button(self.edit_group_frame, text="💾 Сохранить", command=self.save_group_edit).grid(row=2, column=0, pady=10)
        tk.Button(self.edit_group_frame, text="❌ Отмена", command=self.cancel_group_edit).grid(row=2, column=1, pady=10)
        tk.Button(self.edit_group_frame, text="🗑️ Удалить", command=self.delete_group_gui).grid(row=2, column=2, pady=10, padx=5)

        tk.Button(self.page_groups, text="➕", command=self.toggle_group_form, width=3).pack(padx=5, pady=5, anchor="w")

    def populate_group_chars(self, frame, check_vars, selected=None):
        for w in frame.winfo_children():
            w.destroy()
        check_vars.clear()
        config = self.backend.get_config()
        for char in config.get("characters", []):
            var = tk.BooleanVar(value=selected and char["name"] in selected)
            chk = tk.Checkbutton(frame, text=char["name"], variable=var)
            chk.pack(anchor="w")
            check_vars[char["name"]] = var

    def toggle_group_form(self):
        if self.group_form_frame.winfo_ismapped():
            self.group_form_frame.pack_forget()
        else:
            self.populate_group_chars(self.group_chars_frame, self.group_check_vars)
            self.edit_group_frame.pack_forget()
            self.group_form_frame.pack(pady=10, anchor="w")

    def add_group_gui(self):
        name = self.group_name_entry.get().strip()
        chars = [c for c, var in self.group_check_vars.items() if var.get()]
        if not name or not chars:
            messagebox.showwarning("Ошибка", "Введите имя группы и выберите персонажей")
            return
        self.backend.add_group(name, chars)
        self.group_form_frame.pack_forget()
        self.refresh_groups()

    def edit_group_gui(self, group):
        self.edit_group_frame.pack(pady=10, anchor="w")
        self.group_form_frame.pack_forget()
        self.edit_group_name_entry.delete(0, tk.END)
        self.edit_group_name_entry.insert(0, group["name"])
        self.populate_group_chars(self.edit_group_chars_frame, self.group_check_vars, group["characters"])
        self.current_edit_group = group["name"]

    def save_group_edit(self):
        name = self.edit_group_name_entry.get().strip()
        chars = [c for c, var in self.group_check_vars.items() if var.get()]
        if not name or not chars:
            messagebox.showwarning("Ошибка", "Введите имя группы и выберите персонажей")
            return
        self.backend.update_group(self.current_edit_group, name, chars)
        self.edit_group_frame.pack_forget()
        self.refresh_groups()

    def cancel_group_edit(self):
        self.edit_group_frame.pack_forget()

    def delete_group_gui(self):
        answer = messagebox.askyesno("Подтверждение", f"Точно хотите удалить группу {self.current_edit_group}?")
        if answer:
            self.backend.delete_group(self.current_edit_group)
            self.edit_group_frame.pack_forget()
            self.refresh_groups()

    def refresh_groups(self):
        for widget in self.groups_frame.winfo_children():
            widget.destroy()
        config = self.backend.get_config()
        for group in config.get("groups", []):
            row_frame = tk.Frame(self.groups_frame)
            row_frame.pack(fill="x", pady=2, padx=5)
            tk.Button(row_frame, text=group["name"], width=20,
                      command=lambda g=group: self.backend.starter(
                          config["settings"]["game_path"], config["settings"]["client_exe"],
                          [c for c in config["characters"] if c["name"] in g["characters"]])
                      ).pack(side="left")
            tk.Button(row_frame, text="✏️", command=lambda g=group: self.edit_group_gui(g)).pack(side="left", padx=5)

    # ========================
    # Page 3: Settings
    # ========================
    def setup_settings_page(self):
        frame = self.page_settings
        tk.Label(frame, text="Путь к игре").grid(row=0, column=0, sticky="w")
        self.game_path_entry = tk.Entry(frame, width=40)
        self.game_path_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame, text="ElementClient.exe").grid(row=1, column=0, sticky="w")
        self.client_exe_entry = tk.Entry(frame, width=40)
        self.client_exe_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(frame, text="💾 Сохранить", command=self.save_settings).grid(row=2, column=0, columnspan=2, pady=10)

    def load_settings(self):
        config = self.backend.get_config()
        self.game_path_entry.delete(0, tk.END)
        self.game_path_entry.insert(0, config["settings"].get("game_path", ""))
        self.client_exe_entry.delete(0, tk.END)
        self.client_exe_entry.insert(0, config["settings"].get("client_exe", ""))

    def save_settings(self):
        config = self.backend.get_config()
        config["settings"]["game_path"] = self.game_path_entry.get().strip()
        config["settings"]["client_exe"] = self.client_exe_entry.get().strip()
        self.backend.save_config(config)
        messagebox.showinfo("Настройки", "Сохранено!")

# ========================
# Main
# ========================
if __name__ == "__main__":
    backend = PWBackend()
    root = tk.Tk()
    icon = tk.PhotoImage(data=base64.b64decode(ICON_BASE64))
    root.iconphoto(True, icon)
    gui = PWSoulkeeperGUI(root, backend)
    root.mainloop()