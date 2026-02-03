import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.database import get_connection


class StudentDashboardPage(tk.Frame):
    """
    Routed Student Dashboard (Frame)
    - No Toplevel / No Tk()
    - Uses controller.session["student"] = {"prn":..., "name":...}
    - Internal view routing: Overall / Course-wise with back stack
    - Logout returns to HomePage
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#0f1720")
        self.controller = controller

        # ---- THEME ----
        self.FONT_BOLD = ("Segoe UI", 14, "bold")
        self.FONT_LG = ("Segoe UI", 18, "bold")
        self.FONT_MD = ("Segoe UI", 13)
        self.ACCENT = "#08bdb6"
        self.SECOND = "#0b6fb5"
        self.CARD_BG = "#ffffff"
        self.PANEL_BG = "#0f1720"
        self.SIDEBAR_BG = "#0b1619"

        # matplotlib figure ref (cleanup)
        self._fig = None
        self._canvas = None

        # internal view history inside dashboard (overall/course)
        self.view_stack = []
        self.current_view = None

        # --------- LAYOUT (Sidebar + Main) ----------
        self.sidebar = tk.Frame(self, bg=self.SIDEBAR_BG, width=280)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = tk.Frame(self, bg=self.PANEL_BG)
        self.main.pack(side="right", fill="both", expand=True)

        # --------- SIDEBAR HEADER ----------
        tk.Label(
            self.sidebar,
            text="👤 Student Portal",
            bg=self.SIDEBAR_BG,
            fg=self.ACCENT,
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(30, 10))

        # --------- SIDEBAR BUTTONS ----------
        self.btn_overall = self._sidebar_btn("🏠 Overall Attendance", self.ACCENT, self.show_overall, active=True)
        self.btn_course = self._sidebar_btn("📘 Course-wise", self.SECOND, self.show_course, active=False)

        # spacer
        tk.Frame(self.sidebar, bg=self.SIDEBAR_BG).pack(fill="both", expand=True)

        self.btn_logout = self._sidebar_btn("🚪 Logout", "#d9534f", self.logout, active=False, hover="#c9302c")

        # --------- TOP BAR (Main) ----------
        self.topbar = tk.Frame(self.main, bg=self.PANEL_BG)
        self.topbar.pack(fill="x", pady=(12, 0))

        self.route_back_btn = tk.Button(
            self.topbar,
            text="⬅ App Back",
            font=self.FONT_MD,
            bg="#111827",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.controller.back
        )
        self.route_back_btn.pack(side="left", padx=18)

        self.inner_back_btn = tk.Button(
            self.topbar,
            text="← Dashboard Back",
            font=self.FONT_MD,
            bg="#1f2937",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.view_back
        )
        self.inner_back_btn.pack(side="left", padx=10)

        self.title_lbl = tk.Label(
            self.topbar,
            text="Student Dashboard",
            bg=self.PANEL_BG,
            fg="white",
            font=("Segoe UI", 18, "bold")
        )
        self.title_lbl.pack(side="right", padx=20)

        # --------- CONTENT AREA ----------
        self.content = tk.Frame(self.main, bg=self.PANEL_BG)
        self.content.pack(fill="both", expand=True, padx=20, pady=16)

    # ========================= ROUTER LIFECYCLE =========================
    def on_show(self):
        student = self.controller.session.get("student")
        if not student:
            messagebox.showwarning("Access Denied", "Please login as Student first.")
            self.controller.navigate("StudentLoginPage", add_to_history=False)
            return

        # Start at overall view each time page opens
        self.view_stack.clear()
        self._set_active_sidebar("overall")
        self.show_overall(add_to_stack=False)

    def on_hide(self):
        self._cleanup_chart()

    # ========================= SIDEBAR HELPERS =========================
    def _sidebar_btn(self, text, bg, cmd, active=False, hover="#1b2b2f"):
        lbl = tk.Label(
            self.sidebar,
            text=text,
            bg=bg if active else self.SIDEBAR_BG,
            fg="white",
            font=self.FONT_MD,
            width=22,
            height=2,
            cursor="hand2"
        )
        lbl.pack(pady=8)
        lbl.bind("<Enter>", lambda e: lbl.config(bg=hover))
        lbl.bind("<Leave>", lambda e: lbl.config(bg=(bg if active else self.SIDEBAR_BG)))
        lbl.bind("<Button-1>", lambda e: cmd())
        return lbl

    def _set_active_sidebar(self, which):
        # reset
        self.btn_overall.config(bg=self.SIDEBAR_BG)
        self.btn_course.config(bg=self.SIDEBAR_BG)

        if which == "overall":
            self.btn_overall.config(bg=self.ACCENT)
        elif which == "course":
            self.btn_course.config(bg=self.SECOND)

    # ========================= INTERNAL VIEW ROUTING =========================
    def view_push(self, view_name):
        if self.current_view and self.current_view != view_name:
            self.view_stack.append(self.current_view)
        self.current_view = view_name
        self._update_inner_back_state()

    def view_back(self):
        if not self.view_stack:
            return
        prev = self.view_stack.pop()
        if prev == "overall":
            self.show_overall(add_to_stack=False)
        elif prev == "course":
            self.show_course(add_to_stack=False)

    def _update_inner_back_state(self):
        if self.view_stack:
            self.inner_back_btn.config(state="normal", bg="#1f2937")
        else:
            self.inner_back_btn.config(state="disabled", bg="#374151")

    # ========================= DB HELPERS =========================
    def fetch_student(self, prn):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT name, photo FROM students WHERE prn=?", (prn,))
            res = cur.fetchone()
            conn.close()
            return res
        except:
            return None

    def attendance_totals(self, prn):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM attendance WHERE prn=?", (prn,))
            total = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM attendance WHERE prn=? AND status='Present'", (prn,))
            present = cur.fetchone()[0] or 0
            conn.close()
            absent = total - present
            return total, present, absent
        except:
            return 0, 0, 0

    def subject_stats(self, prn):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT s.name, COUNT(a.id) AS total,
                       SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present
                FROM attendance a
                JOIN subjects s ON a.subject_id = s.id
                WHERE a.prn=?
                GROUP BY a.subject_id
            """, (prn,))
            rows = cur.fetchall()
            conn.close()
            return rows
        except:
            return []

    # ========================= UI HELPERS =========================
    def clear_content(self):
        self._cleanup_chart()
        for w in self.content.winfo_children():
            w.destroy()

    def _cleanup_chart(self):
        # remove tk canvas widget
        try:
            if self._canvas:
                self._canvas.get_tk_widget().destroy()
        except:
            pass
        self._canvas = None

        # close matplotlib figure
        if self._fig:
            try:
                plt.close(self._fig)
            except:
                pass
        self._fig = None

    # ========================= VIEWS =========================
    def show_overall(self, add_to_stack=True):
        student = self.controller.session.get("student")
        if not student:
            return
        prn = student["prn"]

        if add_to_stack:
            self.view_push("overall")
        else:
            self.current_view = "overall"
            self._update_inner_back_state()

        self._set_active_sidebar("overall")
        self.clear_content()

        # ------- fetch student -------
        std = self.fetch_student(prn)
        student_name, photo_data = (std["name"], std["photo"]) if std else (prn, None)

        # -------- GRID LAYOUT --------
        left = tk.Frame(self.content, bg=self.PANEL_BG)
        left.pack(side="left", fill="y", padx=(10, 16), pady=10)

        right = tk.Frame(self.content, bg=self.PANEL_BG)
        right.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        # -------- PROFILE CARD --------
        prof_card = tk.Frame(left, bg=self.CARD_BG, bd=0, highlightthickness=0)
        prof_card.pack(fill="x", pady=(0, 14))

        tk.Label(prof_card, text="Profile", bg=self.CARD_BG, fg="#0f1720", font=self.FONT_BOLD).pack(
            anchor="w", padx=16, pady=(14, 8)
        )

        # photo
        photo_box = tk.Frame(prof_card, bg=self.CARD_BG)
        photo_box.pack(pady=(0, 10))

        if photo_data:
            try:
                img = Image.open(io.BytesIO(photo_data)).resize((120, 120))
                photo = ImageTk.PhotoImage(img)
                tk.Label(photo_box, image=photo, bg=self.CARD_BG).pack()
                prof_card.image = photo
            except:
                tk.Label(photo_box, text="No Image", bg=self.CARD_BG, fg="#444").pack(pady=35)
        else:
            tk.Label(photo_box, text="No Image", bg=self.CARD_BG, fg="#444").pack(pady=35)

        tk.Label(prof_card, text=student_name, bg=self.CARD_BG, fg="#0f1720", font=self.FONT_LG).pack(pady=2)
        tk.Label(prof_card, text=f"PRN: {prn}", bg=self.CARD_BG, fg="#57606a", font=self.FONT_MD).pack(pady=(0, 16))

        # -------- SUMMARY CARD --------
        total, present, absent = self.attendance_totals(prn)

        summary_card = tk.Frame(left, bg=self.CARD_BG, bd=0, highlightthickness=0)
        summary_card.pack(fill="x")

        tk.Label(summary_card, text="Attendance Summary", bg=self.CARD_BG, fg="#0f1720", font=self.FONT_BOLD).pack(
            anchor="w", padx=16, pady=(14, 8)
        )

        def stat_row(label, value, color="#333"):
            row = tk.Frame(summary_card, bg=self.CARD_BG)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=label, bg=self.CARD_BG, fg="#6b7280", font=self.FONT_MD).pack(side="left")
            tk.Label(row, text=value, bg=self.CARD_BG, fg=color, font=("Segoe UI", 13, "bold")).pack(side="right")

        stat_row("Total Classes", total, "#111827")
        stat_row("Present", present, "#0b8f83")
        stat_row("Absent", absent, "#d9534f")
        stat_row("Percentage", f"{(present/total*100):.1f}%" if total else "0.0%", self.ACCENT)

        tk.Frame(summary_card, bg=self.CARD_BG, height=14).pack()

        # -------- CHART CARD --------
        chart_card = tk.Frame(right, bg=self.CARD_BG, bd=0, highlightthickness=0)
        chart_card.pack(fill="both", expand=True)

        tk.Label(chart_card, text="Overall Attendance", bg=self.CARD_BG, fg="#0f1720", font=self.FONT_BOLD).pack(
            anchor="w", padx=16, pady=(14, 8)
        )

        percent = (present / total) * 100 if total else 0

        self._fig, ax = plt.subplots(figsize=(5.2, 4.2), dpi=90)
        ax.pie(
            [percent, 100 - percent],
            labels=[f"Present ({percent:.1f}%)", "Absent"],
            autopct="%1.1f%%",
            startangle=90
        )
        ax.set_title("Attendance", fontsize=13, fontweight="bold")
        self._fig.tight_layout()

        self._canvas = FigureCanvasTkAgg(self._fig, master=chart_card)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(expand=True, pady=12)

    def show_course(self, add_to_stack=True):
        student = self.controller.session.get("student")
        if not student:
            return
        prn = student["prn"]

        if add_to_stack:
            self.view_push("course")
        else:
            self.current_view = "course"
            self._update_inner_back_state()

        self._set_active_sidebar("course")
        self.clear_content()

        rows = self.subject_stats(prn)

        wrapper = tk.Frame(self.content, bg=self.PANEL_BG)
        wrapper.pack(fill="both", expand=True, padx=12, pady=10)

        header = tk.Frame(wrapper, bg=self.PANEL_BG)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text="📘 Course-wise Attendance",
            bg=self.PANEL_BG,
            fg="white",
            font=("Segoe UI", 18, "bold")
        ).pack(side="left")

        if not rows:
            tk.Label(wrapper, text="No course records found.", bg=self.PANEL_BG, fg="#9aa7b0",
                     font=self.FONT_MD).pack(pady=40)
            return

        # scroll area
        canvas = tk.Canvas(wrapper, bg=self.PANEL_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.PANEL_BG)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for subj, total, pres in rows:
            percent = (pres / total) * 100 if total else 0

            card = tk.Frame(scroll_frame, bg=self.CARD_BG, bd=0, highlightthickness=0)
            card.pack(fill="x", pady=10, padx=6)

            left = tk.Frame(card, bg=self.CARD_BG)
            left.pack(side="left", padx=14, pady=14)

            tk.Label(left, text=subj, bg=self.CARD_BG, fg="#0f1720",
                     font=("Segoe UI", 16, "bold")).pack(anchor="w")
            tk.Label(left, text=f"Present {pres} / Total {total}", bg=self.CARD_BG, fg="#6b7280",
                     font=("Segoe UI", 12)).pack(anchor="w", pady=(4, 0))

            right = tk.Frame(card, bg=self.CARD_BG)
            right.pack(side="right", padx=14, pady=14)

            pill = tk.Label(
                right,
                text=f"{percent:.1f}%",
                bg=self.ACCENT if percent >= 75 else "#f59e0b" if percent >= 50 else "#ef4444",
                fg="white",
                font=("Segoe UI", 12, "bold"),
                padx=14,
                pady=8
            )
            pill.pack()

    # ========================= LOGOUT =========================
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.controller.session["student"] = None
            self.controller.history.clear()
            self.controller.navigate("HomePage", add_to_history=False)
