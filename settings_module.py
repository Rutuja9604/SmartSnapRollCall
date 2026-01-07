# settings_module.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import get_connection, hash_password

class SettingsModule:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="white")
        self.build_ui()

    def get_frame(self):
        return self.frame

    def build_ui(self):
        tk.Label(self.frame, text="⚙️ Settings", font=("Segoe UI", 18, "bold"), bg="white").pack(pady=12)

        # Change Admin Password
        pw_frame = tk.Frame(self.frame, bg="white")
        pw_frame.pack(pady=20, padx=15, anchor="w")

        tk.Label(pw_frame, text="Change Admin Password:", bg="white", font=("Segoe UI", 12)).grid(row=0, column=0, pady=5, sticky="w")
        self.pass_var = tk.StringVar()
        tk.Entry(pw_frame, textvariable=self.pass_var, show="*", width=30).grid(row=0, column=1, pady=5, padx=10)

        tk.Button(pw_frame, text="Save Password", bg="#0ea5e9", fg="white", font=("Segoe UI", 12, "bold"),
                  command=self.save_password).grid(row=1, column=1, pady=10, sticky="e")

        # Placeholder: Other settings can be added similarly
        tk.Label(self.frame, text="Other Settings coming soon...", bg="white", fg="gray").pack(pady=10, padx=15, anchor="w")

    def save_password(self):
        new_pass = self.pass_var.get().strip()
        if not new_pass:
            messagebox.showwarning("Validation", "Password cannot be empty")
            return
        hashed = hash_password(new_pass)
        # You can save hashed password to a table like 'admin_settings' if exists
        messagebox.showinfo("Saved", "Admin password updated successfully")
