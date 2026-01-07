import tkinter as tk
from tkinter import messagebox
from utils.database import get_connection, hash_password
from student_dashboard import open_dashboard


class StudentLogin(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Student Login - Smart Snap")
        self.geometry("500x400")
        self.config(bg="#0a192f")

        tk.Label(self, text="🎓 Student Login",
                 font=("Segoe UI", 22, "bold"),
                 bg="#0a192f", fg="white").pack(pady=30)

        form = tk.Frame(self, bg="#0a192f")
        form.pack(pady=20)

        tk.Label(form, text="PRN:", font=("Segoe UI", 12),
                 bg="#0a192f", fg="white").grid(row=0, column=0, pady=10, sticky="e")
        self.prn = tk.Entry(form, width=25, font=("Segoe UI", 12))
        self.prn.grid(row=0, column=1, pady=10)

        tk.Label(form, text="Password:", font=("Segoe UI", 12),
                 bg="#0a192f", fg="white").grid(row=1, column=0, pady=10, sticky="e")
        self.password = tk.Entry(form, width=25, font=("Segoe UI", 12), show="*")
        self.password.grid(row=1, column=1, pady=10)

        tk.Button(self, text="Login",
                  font=("Segoe UI", 12, "bold"),
                  bg="#F1C40F", fg="white",
                  width=12, command=self.check_login).pack(pady=30)

    def check_login(self):
        prn = self.prn.get().strip()
        pwd = self.password.get().strip()

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, password FROM students WHERE prn=?", (prn,))
        row = cur.fetchone()
        conn.close()

        if row and row["password"] == hash_password(pwd):
            messagebox.showinfo("Success", f"Welcome {row['name']}!")
            self.withdraw()  # hide login window
            open_dashboard(prn, parent=self)
        else:
            messagebox.showerror("Error", "Invalid credentials!")


if __name__ == "__main__":
    app = StudentLogin()
    app.mainloop()
