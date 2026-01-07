import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.database import get_connection

def open_dashboard(prn, parent=None):
    dash = tk.Toplevel(parent) if parent else tk.Tk()
    dash.title("🎨 Smart Attendance — Student Dashboard")
    dash.geometry("1366x768")
    dash.state("zoomed")
    dash.configure(bg="#0f1720")

    FONT_BOLD = ("Segoe UI", 14, "bold")
    FONT_LG = ("Segoe UI", 18, "bold")
    FONT_MD = ("Segoe UI", 14)
    ACCENT = "#08bdb6"
    SECOND = "#0b6fb5"
    CARD_BG = "#ffffff"
    PANEL_BG = "#0f1720"

    # ---------- LEFT SIDEBAR ----------
    sidebar = tk.Frame(dash, bg="#0b1619", width=280)
    sidebar.pack(side="left", fill="y")

    tk.Label(sidebar, text="👤 Student Portal", bg="#0b1619", fg=ACCENT,
             font=("Segoe UI", 20, "bold")).pack(pady=(30, 10))

    def make_sidebar_btn(text, bg, cmd):
        lbl = tk.Label(sidebar, text=text, bg=bg, fg="white", font=FONT_MD, width=22, height=2, cursor="hand2")
        lbl.pack(pady=8)
        lbl.bind("<Enter>", lambda e: lbl.config(bg="#1b2b2f"))
        lbl.bind("<Leave>", lambda e: lbl.config(bg=bg))
        lbl.bind("<Button-1>", lambda e: cmd())
        return lbl

    btn_overall = make_sidebar_btn("🏠 Overall Attendance", ACCENT, lambda: None)
    btn_course = make_sidebar_btn("📘 Course-wise", SECOND, lambda: None)
    logout_btn = make_sidebar_btn("🚪 Logout", "#d9534f", lambda: (dash.destroy(), parent.destroy() if parent else None))

    # ---------- MAIN CONTENT ----------
    main = tk.Frame(dash, bg=PANEL_BG)
    main.pack(side="right", fill="both", expand=True)

    def clear_main():
        for w in main.winfo_children():
            w.destroy()

    # ---------- BACK BUTTON ----------
    def add_back_button(target_view=None):
        # remove previous back buttons
        for w in main.winfo_children():
            if getattr(w, "is_back_btn", False):
                w.destroy()

        btn = tk.Button(main, text="← Back to Main", font=FONT_MD, bg="#d9534f", fg="white",
                        activebackground="#c9302c", activeforeground="white",
                        command=lambda: target_view() if target_view else show_overall())
        btn.pack(anchor="ne", padx=20, pady=20)
        btn.is_back_btn = True

    # ---------- HELPERS ----------
    def fetch_student(prn):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT name, photo FROM students WHERE prn=?", (prn,))
            res = cur.fetchone()
            conn.close()
            return res
        except:
            return None

    def attendance_totals(prn):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM attendance WHERE prn=?", (prn,))
            total = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM attendance WHERE prn=? AND status='Present'", (prn,))
            present = cur.fetchone()[0] or 0
            absent = total - present
            conn.close()
            return total, present, absent
        except:
            return 0, 0, 0

    def subject_stats(prn):
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

    # ---------- VIEWS ----------
    def show_overall():
        clear_main()
        add_back_button(target_view=show_overall)

        std = fetch_student(prn)
        student_name, photo_data = (std["name"], std["photo"]) if std else (prn, None)

        # Profile card
        prof_card = tk.Frame(main, bg=CARD_BG, bd=2, relief="groove")
        prof_card.place(relx=0.03, rely=0.06, relwidth=0.28, relheight=0.36)

        if photo_data:
            try:
                img = Image.open(io.BytesIO(photo_data)).resize((120, 120))
                photo = ImageTk.PhotoImage(img)
                tk.Label(prof_card, image=photo, bg=CARD_BG).pack(pady=(18, 6))
                prof_card.image = photo
            except:
                tk.Label(prof_card, text="No Image", bg=CARD_BG, fg="#444").pack(pady=40)
        else:
            tk.Label(prof_card, text="No Image", bg=CARD_BG, fg="#444").pack(pady=40)

        tk.Label(prof_card, text=student_name, bg=CARD_BG, fg="#0f1720", font=FONT_LG).pack(pady=2)
        tk.Label(prof_card, text=f"PRN: {prn}", bg=CARD_BG, fg="#57606a", font=FONT_MD).pack()

        # Attendance summary
        total, present, absent = attendance_totals(prn)
        summary_card = tk.Frame(main, bg=CARD_BG, bd=2, relief="groove")
        summary_card.place(relx=0.03, rely=0.46, relwidth=0.28, relheight=0.28)
        tk.Label(summary_card, text="Attendance Summary", bg=CARD_BG, fg="#0f1720", font=FONT_BOLD).pack(pady=12)
        tk.Label(summary_card, text=f"Total Classes: {total}", bg=CARD_BG, fg="#333", font=FONT_MD).pack(pady=4)
        tk.Label(summary_card, text=f"Present: {present}", bg=CARD_BG, fg="#0b8f83", font=FONT_MD).pack(pady=4)
        tk.Label(summary_card, text=f"Absent: {absent}", bg=CARD_BG, fg="#d9534f", font=FONT_MD).pack(pady=4)

        # Pie chart
        percent = (present / total) * 100 if total else 0
        chart_card = tk.Frame(main, bg=CARD_BG, bd=2, relief="groove")
        chart_card.place(relx=0.34, rely=0.06, relwidth=0.45, relheight=0.68)
        fig, ax = plt.subplots(figsize=(4, 4), dpi=80)
        ax.pie([percent, 100 - percent], labels=[f'Present ({percent:.1f}%)', 'Absent'],
               autopct='%1.1f%%', startangle=90, colors=["#08bdb6", "#e9ecef"])
        ax.set_title("Overall Attendance", fontsize=14, fontweight="bold")
        canvas = FigureCanvasTkAgg(fig, master=chart_card)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, pady=20)

    def show_course():
        clear_main()
        add_back_button(target_view=show_overall)
        rows = subject_stats(prn)

        container = tk.Frame(main, bg=PANEL_BG)
        container.pack(fill="both", expand=True, padx=28, pady=8)
        if not rows:
            tk.Label(container, text="No course records found.", bg=PANEL_BG, fg="#9aa7b0", font=FONT_MD).pack(pady=40)
            return

        for subj, total, pres in rows:
            percent = (pres / total) * 100 if total else 0
            card = tk.Frame(container, bg="#ffffff", bd=1, relief="ridge")
            card.pack(pady=12, padx=8, fill="x")
            tk.Label(card, text=subj, bg="#ffffff", fg="#0f1720", font=("Segoe UI", 16, "bold")).pack(side="left", padx=10, pady=12)
            tk.Label(card, text=f"{pres}/{total} ({percent:.1f}%)", bg="#ffffff", fg="#0b8f83", font=("Segoe UI", 14, "bold")).pack(side="right", padx=10, pady=12)

    # Bind sidebar
    btn_overall.bind("<Button-1>", lambda e: show_overall())
    btn_course.bind("<Button-1>", lambda e: show_course())

    show_overall()

    if parent is None:
        dash.mainloop()
