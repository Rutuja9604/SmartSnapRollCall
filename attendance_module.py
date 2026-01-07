# attendance_module.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import get_connection
from datetime import datetime

class AttendanceModule:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="white")
        self.frame.pack(fill="both", expand=True)
        self.build_ui()

    def get_frame(self):
        return self.frame

    # ----------------- BUILD UI -----------------
    def build_ui(self):
        # Header
        header = tk.Label(
            self.frame,
            text="🕒 Attendance Records",
            font=("Segoe UI", 16, "bold"),
            bg="white"
        )
        header.pack(anchor="w", pady=(10,5), padx=10)

        # Controls
        ctl = tk.Frame(self.frame, bg="white")
        ctl.pack(fill="x", padx=10, pady=(0,10))

        tk.Button(ctl, text="Mark Attendance for Today",
                  command=self.open_mark_dialog).pack(side="left", padx=5)
        tk.Button(ctl, text="Refresh", command=self.load_records).pack(side="left", padx=5)

        tk.Label(ctl, text="Date (YYYY-MM-DD):", bg="white").pack(side="left", padx=(20,5))
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(ctl, textvariable=self.date_var, width=12).pack(side="left")
        tk.Button(ctl, text="Load", command=self.load_records).pack(side="left", padx=5)

        # Table
        cols = ("id","prn","roll_no","name","subject_id","teacher_id","date","time","status","remarks")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", height=14)

        for c in cols:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, anchor="center", width=120)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Load initial records
        self.load_records()

    # ----------------- LOAD RECORDS -----------------
    def load_records(self):
        date = self.date_var.get().strip()
        for r in self.tree.get_children():
            self.tree.delete(r)

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT * FROM attendance WHERE date=?
                ORDER BY prn
            """, (date,))
            rows = cur.fetchall()
            for row in rows:
                r = dict(row)  # convert sqlite3.Row -> dict
                self.tree.insert("", "end", values=(
                    r.get("id"),
                    r.get("prn"),
                    r.get("roll_no", ""),
                    r.get("name", ""),
                    r.get("subject_id"),
                    r.get("teacher_id"),
                    r.get("date"),
                    r.get("time"),
                    r.get("status"),
                    r.get("remarks")
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    # ----------------- MARK ATTENDANCE -----------------
    def open_mark_dialog(self):
        dlg = tk.Toplevel(self.parent)
        dlg.title("Mark Attendance")
        dlg.geometry("500x500")
        dlg.transient(self.parent)
        dlg.grab_set()

        date_str = datetime.now().strftime("%Y-%m-%d")
        tk.Label(dlg, text=f"Mark attendance for {date_str}",
                 font=("Segoe UI", 12, "bold")).pack(pady=8)

        canvas = tk.Frame(dlg)
        canvas.pack(fill="both", expand=True)

        tree = ttk.Treeview(canvas, columns=("prn","roll_no","name","status"), show="headings", height=15)
        for c in ("prn","roll_no","name","status"):
            tree.heading(c, text=c.replace("_"," ").title())
            tree.column(c, anchor="center", width=100)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Load students
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT prn, roll_no, name FROM students ORDER BY roll_no")
            students = cur.fetchall()
            for s in students:
                s = dict(s)
                tree.insert("", "end", values=(s["prn"], s["roll_no"], s["name"], "Absent"))
        finally:
            conn.close()

        # Toggle status on double-click
        def toggle_status(event):
            item = tree.selection()
            if not item:
                return
            vals = tree.item(item, "values")
            new_status = "Present" if vals[3]=="Absent" else "Absent"
            tree.item(item, values=(vals[0], vals[1], vals[2], new_status))
        tree.bind("<Double-1>", toggle_status)

        # Optional note
        note_var = tk.StringVar()
        tk.Label(dlg, text="Optional Note:").pack(anchor="w", padx=12)
        tk.Entry(dlg, textvariable=note_var).pack(fill="x", padx=12, pady=(0,8))

        # Save attendance
        def save_all():
            conn = get_connection()
            cur = conn.cursor()
            try:
                for iid in tree.get_children():
                    vals = tree.item(iid)["values"]
                    prn, roll, name, status = vals
                    # Check if already exists
                    cur.execute("SELECT id FROM attendance WHERE prn=? AND date=?", (prn, date_str))
                    r = cur.fetchone()
                    if r:
                        cur.execute("UPDATE attendance SET status=?, remarks=? WHERE id=?",
                                    (status, note_var.get().strip(), r["id"]))
                    else:
                        cur.execute("""
                            INSERT INTO attendance (prn, date, status, remarks)
                            VALUES (?,?,?,?)
                        """, (prn, date_str, status, note_var.get().strip()))
                conn.commit()
                messagebox.showinfo("Saved", "Attendance saved successfully.")
                dlg.destroy()
                self.date_var.set(date_str)
                self.load_records()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()

        tk.Button(dlg, text="Save Attendance", command=save_all).pack(pady=10)

    # ----------------- EDIT RECORD -----------------
    def on_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        vals = self.tree.item(item)["values"]
        self.open_edit_dialog(vals)

    def open_edit_dialog(self, vals):
        dlg = tk.Toplevel(self.parent)
        dlg.title("Edit Attendance")
        dlg.geometry("360x260")
        dlg.transient(self.parent)
        dlg.grab_set()

        status_var = tk.StringVar(value=vals[8])
        note_var = tk.StringVar(value=vals[9] or "")

        tk.Label(dlg, text=f"Student: {vals[2]} ({vals[1]})").pack(pady=(10,6))
        tk.Label(dlg, text="Status").pack()
        ttk.Combobox(dlg, textvariable=status_var, values=("Present","Absent")).pack(pady=5)

        tk.Label(dlg, text="Note").pack()
        tk.Entry(dlg, textvariable=note_var).pack(pady=5)

        def save():
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("UPDATE attendance SET status=?, remarks=? WHERE id=?",
                            (status_var.get(), note_var.get().strip(), vals[0]))
                conn.commit()
                messagebox.showinfo("Updated", "Attendance updated successfully.")
                dlg.destroy()
                self.load_records()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()

        tk.Button(dlg, text="Save", command=save).pack(pady=12)
