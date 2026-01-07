# admin_login.py
import tkinter as tk
from tkinter import messagebox
from admin_dashboard import AdminDashboard  # Import the dashboard class directly

class AdminLogin(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Admin Login - Smart Snap")
        self.geometry("500x400")
        self.config(bg="#0a192f")

        tk.Label(self, text="👨‍💼 Admin Login",
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
                  bg="#0078D7", fg="white",
                  width=12, command=self.check_login).pack(pady=30)

    def check_login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        # Replace with your database authentication if needed
        if user == "admin" and pwd == "admin123":
            messagebox.showinfo("Success", "Welcome Admin!")
            self.open_dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials!")

    def open_dashboard(self):
        # Close login window and open admin dashboard in the same process
        self.destroy()
        dashboard = AdminDashboard()
        dashboard.mainloop()


if __name__ == "__main__":
    app = AdminLogin()
    app.mainloop()
