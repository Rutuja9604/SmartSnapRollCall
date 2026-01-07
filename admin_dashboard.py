# admin_dashboard.py
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from utils.database import get_connection, init_db
from student_module import StudentModule
from teacher_module import TeacherModule
from subject_module import SubjectModule
from attendance_module import AttendanceModule
import os

init_db()


# ======================= MAIN ADMIN DASHBOARD ===========================
class AdminDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart SNAP - Admin Dashboard")
        self.geometry("1250x750")
        self.configure(bg="#F5F7FA")

        self.active_btn = None  # track active highlighted button

        self.create_sidebar()
        self.create_content()
        self.show_dashboard_page()

    # ------------------------------- SIDEBAR --------------------------------
    def create_sidebar(self):
        self.sidebar = tk.Frame(self, bg="#111827", width=230)
        self.sidebar.pack(side="left", fill="y")

        tk.Label(self.sidebar, text="Smart SNAP",
                 bg="#111827", fg="#22d3ee",
                 font=("Segoe UI", 20, "bold")).pack(pady=25)

        self.menu_buttons = []

        buttons = [
            ("🏠   Dashboard", self.show_dashboard_page),
            ("🎓   Students", self.show_students_page),
            ("👩‍🏫   Teachers", self.show_teachers_page),
            ("📘   Subjects", self.show_subjects_page),
            ("🕒   Attendance", self.show_attendance_page),
            ("📊   Reports", self.show_reports_page),
            ("⚙️   Settings", self.show_settings_page),
            ("🚪   Logout", self.logout),
        ]

        for text, command in buttons:
            btn = tk.Button(
                self.sidebar, text=text, anchor="w",
                bg="#111827", fg="#E5E7EB",
                font=("Segoe UI", 13),
                relief="flat", bd=0, padx=25, pady=14,
                activebackground="#1f2937",
                command=lambda c=command, b=text: self.sidebar_click(c, b)
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#1f2937"))
            btn.bind("<Leave>", lambda e, b=btn: self.reset_btn_bg(b))
            self.menu_buttons.append(btn)

    # highlight the active button
    def sidebar_click(self, command, btn_text):
        for b in self.menu_buttons:
            if b.cget("text") == btn_text:
                b.configure(bg="#0ea5e9", fg="white")
                self.active_btn = b
            else:
                b.configure(bg="#111827", fg="#E5E7EB")
        command()

    def reset_btn_bg(self, btn):
        if btn == self.active_btn:
            btn.configure(bg="#0ea5e9")
        else:
            btn.configure(bg="#111827")

    # ---------------------------- MAIN CONTENT AREA ------------------------
    def create_content(self):
        self.content = tk.Frame(self, bg="#F5F7FA")
        self.content.pack(fill="both", expand=True)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    # ---------------------------- DASHBOARD PAGE ---------------------------
    def show_dashboard_page(self):
        self.clear_content()

        tk.Label(self.content, text="Dashboard Overview",
                 bg="#F5F7FA", fg="#111827",
                 font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=12, padx=8)

        stats_frame = tk.Frame(self.content, bg="#F5F7FA")
        stats_frame.pack(fill="x", pady=10)

        stats = [
            ("Total Students", self.get_count("students")),
            ("Total Teachers", self.get_count("teachers")),
            ("Attendance Records", self.get_count("attendance")),
        ]

        for i, (label, value) in enumerate(stats):
            card = tk.Frame(stats_frame, bg="white",
                            width=260, height=130,
                            highlightthickness=0,
                            bd=0, relief="flat")
            card.grid(row=0, column=i, padx=20)
            card.pack_propagate(False)

            tk.Label(card, text=label, bg="white",
                     fg="#4b5563", font=("Segoe UI", 12, "bold")).pack(pady=10)

            tk.Label(card, text=value, bg="white",
                     fg="#0ea5e9", font=("Segoe UI", 30, "bold")).pack()

        # ------------------- CHART AREA -------------------
        chart_frame = tk.Frame(self.content, bg="#F5F7FA")
        chart_frame.pack(pady=20)

        tk.Label(chart_frame, text="Recent Attendance Trend",
                 bg="#F5F7FA", fg="#111827",
                 font=("Segoe UI", 16, "bold")).pack()

        data = self.get_attendance_summary()
        fig, ax = plt.subplots(figsize=(6.5, 3.2))

        if data:
            ax.plot(list(data.keys()), list(data.values()), marker="o")
            ax.set_ylabel("Present Count")
            ax.set_xlabel("Date")
        else:
            ax.text(0.5, 0.5, "No Attendance Data Available", ha="center")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack()

    # ---------------------- PAGE LOADERS ----------------------
    def show_students_page(self):
        self.clear_content()
        StudentModule(self.content).pack(fill="both", expand=True)

    def show_teachers_page(self):
        self.clear_content()
        TeacherModule(self.content).pack(fill="both", expand=True)

    def show_subjects_page(self):
        self.clear_content()
        module = SubjectModule(self.content)
        module.frame.pack(fill="both", expand=True)

    def show_attendance_page(self):
        self.clear_content()
        AttendanceModule(self.content).pack(fill="both", expand=True)

    def show_reports_page(self):
        self.clear_content()
        from reports_module import ReportsModule
        ReportsModule(self.content).get_frame().pack(fill="both", expand=True)

    def show_settings_page(self):
        self.clear_content()
        from settings_module import SettingsModule
        SettingsModule(self.content).get_frame().pack(fill="both", expand=True)

    # ---------------------- LOGOUT ----------------------
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()

    # ------------------------ DB Helpers ------------------------
    def get_count(self, table_name):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT COUNT(*) as c FROM {table_name}")
            result = cur.fetchone()["c"]
        except:
            result = 0
        conn.close()
        return result

    def get_attendance_summary(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT date, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present_count
                FROM attendance
                GROUP BY date
                ORDER BY date DESC
                LIMIT 7
            """)
            rows = cur.fetchall()
            conn.close()

            rows = list(reversed(rows))  # oldest → newest
            return {r["date"]: r["present_count"] for r in rows}
        except:
            return {}


# ------------------------ RUN APP ------------------------
if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    app = AdminDashboard()
    app.mainloop()
