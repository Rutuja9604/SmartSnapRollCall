# teacher_login.py
import tkinter as tk
from tkinter import messagebox
from utils.database import get_connection, hash_password
from Teacher_Dashboard import TeacherDashboard  # Your teacher dashboard

class TeacherLogin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Teacher Login - Smart Snap")
        self.geometry("500x400")
        self.config(bg="#0a192f")

        tk.Label(self, text="👩‍🏫 Teacher Login",
                 font=("Segoe UI", 22, "bold"),
                 bg="#0a192f", fg="white").pack(pady=30)

        form = tk.Frame(self, bg="#0a192f")
        form.pack(pady=20)

        tk.Label(form, text="Username:", font=("Segoe UI", 12),
                 bg="#0a192f", fg="white").grid(row=0, column=0, pady=10, sticky="e")
        self.username = tk.Entry(form, width=25, font=("Segoe UI", 12))
        self.username.grid(row=0, column=1, pady=10)

        tk.Label(form, text="Password:", font=("Segoe UI", 12),
                 bg="#0a192f", fg="white").grid(row=1, column=0, pady=10, sticky="e")
        self.password = tk.Entry(form, width=25, font=("Segoe UI", 12), show="*")
        self.password.grid(row=1, column=1, pady=10)

        tk.Button(self, text="Login",
                  font=("Segoe UI", 12, "bold"),
                  bg="#2ECC71", fg="white",
                  width=12, command=self.check_login).pack(pady=30)

    def check_login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        if not user or not pwd:
            messagebox.showwarning("Validation", "Enter username and password")
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM teachers WHERE username=?", (user,))
            row = cur.fetchone()
            if row:
                # Compare hashed password
                if row["password"] == hash_password(pwd):
                    messagebox.showinfo("Success", f"Welcome {row['name']}!")
                    self.open_dashboard(row["id"])  # Pass teacher_id
                else:
                    messagebox.showerror("Error", "Invalid username or password")
            else:
                messagebox.showerror("Error", "Invalid username or password")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def open_dashboard(self, teacher_id):
        self.destroy()
        dashboard = TeacherDashboard(teacher_id=teacher_id)
        dashboard.mainloop()


if __name__ == "__main__":
    app = TeacherLogin()
    app.mainloop()
