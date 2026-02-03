import tkinter as tk
from tkinter import messagebox

from utils.database import get_connection, hash_password


class StudentLoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#0a192f")
        self.controller = controller

        # ---------- TITLE ----------
        tk.Label(
            self,
            text="🎓 Student Login",
            font=("Segoe UI", 22, "bold"),
            bg="#0a192f",
            fg="white"
        ).pack(pady=25)

        # ---------- FORM ----------
        form = tk.Frame(self, bg="#0a192f")
        form.pack(pady=10)

        tk.Label(
            form, text="PRN:", font=("Segoe UI", 12),
            bg="#0a192f", fg="white"
        ).grid(row=0, column=0, pady=10, sticky="e")

        self.prn = tk.Entry(form, width=25, font=("Segoe UI", 12))
        self.prn.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(
            form, text="Password:", font=("Segoe UI", 12),
            bg="#0a192f", fg="white"
        ).grid(row=1, column=0, pady=10, sticky="e")

        self.password = tk.Entry(form, width=25, font=("Segoe UI", 12), show="*")
        self.password.grid(row=1, column=1, pady=10, padx=10)

        # ---------- BUTTONS ----------
        btn_row = tk.Frame(self, bg="#0a192f")
        btn_row.pack(pady=20)

        tk.Button(
            btn_row, text="⬅ Back",
            font=("Segoe UI", 11, "bold"),
            bg="#30363d", fg="white",
            width=12, bd=0,
            cursor="hand2",
            command=self.controller.back
        ).pack(side="left", padx=10)

        tk.Button(
            btn_row, text="Login",
            font=("Segoe UI", 11, "bold"),
            bg="#F1C40F", fg="black",
            width=12, bd=0,
            cursor="hand2",
            command=self.check_login
        ).pack(side="left", padx=10)

        # Enter key triggers login
        self.password.bind("<Return>", lambda e: self.check_login())

    def on_show(self):
        """Called by router when this page is opened."""
        self.prn.delete(0, tk.END)
        self.password.delete(0, tk.END)
        self.prn.focus_set()

    def check_login(self):
        prn = self.prn.get().strip()
        pwd = self.password.get().strip()

        if not prn or not pwd:
            messagebox.showwarning("Validation", "Enter PRN and password")
            return

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT prn, name, password FROM students WHERE prn=?", (prn,))
            row = cur.fetchone()

            if row and row["password"] == hash_password(pwd):
                # ✅ Save session info
                self.controller.session["student"] = {
                    "prn": row["prn"],
                    "name": row["name"]
                }

                messagebox.showinfo("Success", f"Welcome {row['name']}!")

                # ✅ Navigate to dashboard (convert dashboard next)
                self.controller.navigate("StudentDashboardPage")
            else:
                messagebox.showerror("Error", "Invalid credentials!")

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()
