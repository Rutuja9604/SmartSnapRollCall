# reports_module.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils.database import get_connection
from datetime import datetime
import pandas as pd

class ReportsModule:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="white")
        self.frame.pack(fill="both", expand=True)
        self.build_ui()

    def get_frame(self):
        return self.frame

    def build_ui(self):
        tk.Label(self.frame, text="📊 Attendance Reports", font=("Segoe UI", 16, "bold"), bg="white").pack(anchor="w", pady=10, padx=10)

        # Filter Frame
        filt = tk.Frame(self.frame, bg="white")
        filt.pack(fill="x", padx=10, pady=5)

        tk.Label(filt, text="From (YYYY-MM-DD):", bg="white").pack(side="left", padx=5)
        self.from_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        tk.Entry(filt, textvariable=self.from_var, width=12).pack(side="left")

        tk.Label(filt, text="To (YYYY-MM-DD):", bg="white").pack(side="left", padx=5)
        self.to_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(filt, textvariable=self.to_var, width=12).pack(side="left")

        tk.Button(filt, text="Load Report", command=self.load_report).pack(side="left", padx=10)
        tk.Button(filt, text="Export to Excel", command=self.export_excel).pack(side="left", padx=10)

        # Table
        cols = ("prn","roll_no","name","subject","teacher","date","status","remarks")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, anchor="center", width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_report()

    def load_report(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        from_date = self.from_var.get().strip()
        to_date = self.to_var.get().strip()

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT a.prn, s.roll_no, s.name, sub.name as subject, t.name as teacher, a.date, a.status, a.remarks
                FROM attendance a
                LEFT JOIN students s ON a.prn = s.prn
                LEFT JOIN subjects sub ON a.subject_id = sub.id
                LEFT JOIN teachers t ON a.teacher_id = t.id
                WHERE a.date BETWEEN ? AND ?
                ORDER BY a.date, s.roll_no
            """, (from_date, to_date))
            rows = cur.fetchall()
            for r in rows:
                self.tree.insert("", "end", values=(
                    r["prn"], r["roll_no"], r["name"], r["subject"], r["teacher"], r["date"], r["status"], r["remarks"]
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def export_excel(self):
        if not self.tree.get_children():
            messagebox.showwarning("No Data", "No report data to export!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Report"
        )
        if not file_path:
            return

        data = []
        for iid in self.tree.get_children():
            data.append(self.tree.item(iid)["values"])

        df = pd.DataFrame(data, columns=["PRN","Roll No","Name","Subject","Teacher","Date","Status","Remarks"])
        try:
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Exported", f"Report exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
