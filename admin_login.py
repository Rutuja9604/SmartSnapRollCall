import tkinter as tk
from tkinter import messagebox


class AdminLoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#0a192f")
        self.controller = controller

        # ---------- TITLE ----------
        tk.Label(
            self,
            text="👨‍💼 Admin Login",
            font=("Segoe UI", 22, "bold"),
            bg="#0a192f",
            fg="white"
        ).pack(pady=25)

        # ---------- FORM ----------
        form = tk.Frame(self, bg="#0a192f")
        form.pack(pady=10)

        tk.Label(
            form,
            text="Username:",
            font=("Segoe UI", 12),
            bg="#0a192f",
            fg="white"
        ).grid(row=0, column=0, pady=10, sticky="e")

        self.username = tk.Entry(form, width=25, font=("Segoe UI", 12))
        self.username.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(
            form,
            text="Password:",
            font=("Segoe UI", 12),
            bg="#0a192f",
            fg="white"
        ).grid(row=1, column=0, pady=10, sticky="e")

        self.password = tk.Entry(form, width=25, font=("Segoe UI", 12), show="*")
        self.password.grid(row=1, column=1, pady=10, padx=10)

        # ---------- BUTTONS ----------
        btn_row = tk.Frame(self, bg="#0a192f")
        btn_row.pack(pady=20)

        tk.Button(
            btn_row,
            text="⬅ Back",
            font=("Segoe UI", 11, "bold"),
            bg="#30363d",
            fg="white",
            width=12,
            bd=0,
            cursor="hand2",
            command=self.controller.back
        ).pack(side="left", padx=10)

        tk.Button(
            btn_row,
            text="Login",
            font=("Segoe UI", 11, "bold"),
            bg="#0078D7",
            fg="white",
            width=12,
            bd=0,
            cursor="hand2",
            command=self.check_login
        ).pack(side="left", padx=10)

        # Enter key triggers login
        self.password.bind("<Return>", lambda e: self.check_login())

    def on_show(self):
        """Called by router when this page opens."""
        self.username.delete(0, tk.END)
        self.password.delete(0, tk.END)
        self.username.focus_set()

    def check_login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        # Basic validation
        if not user or not pwd:
            messagebox.showwarning("Validation", "Enter username and password")
            return

        # Temporary credentials (replace with DB later)
        if user == "admin" and pwd == "admin123":
            self.controller.session["admin"] = {"username": user}
            messagebox.showinfo("Success", "Welcome Admin!")
            self.controller.navigate("AdminDashboardPage")
        else:
            messagebox.showerror("Error", "Invalid credentials!")
