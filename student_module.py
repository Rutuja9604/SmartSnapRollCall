# student_module.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
import hashlib
import os
import pandas as pd
from utils.database import get_connection

# ---------- Helpers ----------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_photo_column():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(students)")
        cols = [r[1] for r in cur.fetchall()]
        if "photo" not in cols:
            cur.execute("ALTER TABLE students ADD COLUMN photo BLOB")
            conn.commit()
        conn.close()
    except:
        try: conn.close()
        except: pass

ensure_photo_column()

# ---------- Student Module ----------
class StudentModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.photo_blob = None
        self.preview_img = None
        self.selected_prn_for_edit = None
        self.create_widgets()
        self.load_students()

    # ---------- UI ----------
    def create_widgets(self):
        container = tk.Frame(self, bg="#F6F8FA")
        container.pack(fill="both", expand=True)

        # Header
        header_frame = tk.Frame(container, bg="#F6F8FA")
        header_frame.pack(fill="x", padx=10, pady=(8, 6))
        tk.Label(header_frame, text="🎓 Students", bg="#F6F8FA",
                 fg="#0b6e7f", font=("Segoe UI", 18, "bold")).pack(side="left")

        # Top Controls
        top_frame = tk.Frame(container, bg="#F6F8FA")
        top_frame.pack(fill="x", padx=10)
        tk.Button(top_frame, text="➕ Add Student", bg="#0b6e7f", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=12, pady=6, command=self.open_add_window).pack(side="left")
        tk.Button(top_frame, text="🔄 Refresh", bg="#e6eef0", fg="#0b6e7f", font=("Segoe UI", 10),
                  relief="flat", padx=10, pady=6, command=self.load_students).pack(side="left", padx=8)
        tk.Label(top_frame, text="Search:", bg="#F6F8FA", fg="#34495e").pack(side="left", padx=(20,4))
        self.search_var = tk.StringVar()
        search_ent = ttk.Entry(top_frame, textvariable=self.search_var, width=34)
        search_ent.pack(side="left")
        search_ent.bind("<Return>", lambda e: self.search_students())
        tk.Button(top_frame, text="Go", bg="#0b6e7f", fg="white", command=self.search_students,
                  relief="flat").pack(side="left", padx=(6,0))
        tk.Button(top_frame, text="📑 Export Excel", bg="#f0f0f0", fg="#0b6e7f", relief="flat",
                  command=self.generate_excel).pack(side="right")

        # Table
        table_frame = tk.Frame(container, bg="#F6F8FA")
        table_frame.pack(fill="both", expand=True, padx=10, pady=8)
        cols = ("prn", "roll_no", "name", "class", "division", "email")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        for c in cols:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.open_edit_window())

        # Bottom buttons
        action_frame = tk.Frame(container, bg="#F6F8FA")
        action_frame.pack(fill="x", padx=10, pady=(6,12))
        tk.Button(action_frame, text="✏️ Edit", bg="#0b6e7f", fg="white", relief="flat",
                  command=self.open_edit_window).pack(side="left", padx=6)
        tk.Button(action_frame, text="🗑 Delete", bg="#e53e3e", fg="white", relief="flat",
                  command=self.delete_student).pack(side="left", padx=6)

    # ---------- DB Helper ----------
    def run_query(self, query, params=(), fetch=True):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall() if fetch else []
            conn.commit()
            conn.close()
            return rows
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            try: conn.close()
            except: pass
            return []

    # ---------- Load / Search ----------
    def load_students(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT prn, roll_no, name, class, division, email FROM students ORDER BY roll_no")
            rows = cur.fetchall()

            for r in rows:
                self.tree.insert("", "end",
                                 values=(r["prn"], r["roll_no"], r["name"], r["class"], r["division"], r["email"]))

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def search_students(self):
        q = self.search_var.get().strip()
        for r in self.tree.get_children():
            self.tree.delete(r)
        if q:
            rows = self.run_query(
                "SELECT prn, roll_no, name, class, division, email FROM students "
                "WHERE name LIKE ? OR prn LIKE ? OR email LIKE ? ORDER BY name",
                (f"%{q}%", f"%{q}%", f"%{q}%")
            )
        else:
            rows = self.run_query("SELECT prn, roll_no, name, class, division, email FROM students ORDER BY name")
        for row in rows:
            self.tree.insert("", "end", values=row)

    # ---------- Add / Edit ----------
    def open_add_window(self):
        self.photo_blob = None
        self.preview_img = None
        self.selected_prn_for_edit = None
        self._open_form_window("Add Student")

    def open_edit_window(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a student to edit.")
            return
        item = self.tree.item(sel[0])["values"]
        self.selected_prn_for_edit = item[0]
        rows = self.run_query("SELECT prn, roll_no, name, class, division, email, password, photo FROM students WHERE prn=?",
                              (self.selected_prn_for_edit,))
        self.photo_blob = rows[0][7] if rows else None
        self._open_form_window("Edit Student", data=item)

    # ---------- Upload ----------
    def upload_photo(self, parent_win):
        file_path = filedialog.askopenfilename(title="Select Photo", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file_path:
            img = Image.open(file_path)
            b = io.BytesIO()
            img.save(b, format="PNG")
            self.photo_blob = b.getvalue()
            img.thumbnail((120, 120))
            self.preview_img = ImageTk.PhotoImage(img)
            parent_win.preview_label.config(image=self.preview_img)
            parent_win.preview_label.image = self.preview_img

    # ---------- Form Window ----------
    def _open_form_window(self, title, data=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("560x700")
        win.configure(bg="#0a192f")
        win.grab_set()
        win.preview_label = None

        tk.Label(win, text=title, font=("Segoe UI", 20, "bold"), fg="#64ffda", bg="#0a192f").pack(pady=10)

        form = tk.Frame(win, bg="#112240")
        form.pack(fill="both", expand=True, padx=16, pady=12)

        # Fields
        fields = [
            ("PRN Number", "prn"),
            ("Roll Number", "roll_no"),
            ("Full Name", "name"),
            ("Class", "class_"),
            ("Division", "division"),
            ("Email", "email"),
            ("Password (leave blank to keep)", "password")
        ]
        self.form_vars = {}
        for i, (label_text, key) in enumerate(fields):
            tk.Label(form, text=label_text, font=("Segoe UI", 11, "bold"), fg="white", bg="#112240")\
                .grid(row=i, column=0, sticky="w", padx=10, pady=8)
            entry_opts = {"font": ("Segoe UI", 12), "width": 34, "relief": "flat", "bg": "#e9eef8"}

            # Dropdowns
            if key == "class_":
                self.form_vars[key] = tk.StringVar(value=(data[3] if data else ""))
                ttk.Combobox(form, textvariable=self.form_vars[key], values=["MCA1","MCA2","MBA1","MBA2"],
                             width=32, state="readonly").grid(row=i, column=1, pady=6, padx=6)
                continue
            if key == "division":
                self.form_vars[key] = tk.StringVar(value=(data[4] if data else ""))
                ttk.Combobox(form, textvariable=self.form_vars[key], values=["A","B","C"], width=32, state="readonly")\
                    .grid(row=i, column=1, pady=6, padx=6)
                continue
            # Password
            if key == "password":
                self.form_vars[key] = tk.StringVar(value="")
                tk.Entry(form, textvariable=self.form_vars[key], show="*", **entry_opts).grid(row=i, column=1, pady=6, padx=6)
                continue
            # Normal fields
            default_val = (data[i] if data else "")
            self.form_vars[key] = tk.StringVar(value=default_val)
            tk.Entry(form, textvariable=self.form_vars[key], **entry_opts).grid(row=i, column=1, pady=6, padx=6)

        # Photo upload
        photo_row = len(fields)
        tk.Label(form, text="Photo (optional)", font=("Segoe UI", 11, "bold"), fg="white", bg="#112240")\
            .grid(row=photo_row, column=0, sticky="w", padx=10, pady=8)
        tk.Button(form, text="Upload Photo", bg="#64ffda", fg="black", width=14,
                  font=("Segoe UI", 10, "bold"), relief="flat", command=lambda: self.upload_photo(win))\
            .grid(row=photo_row, column=1, sticky="w", padx=6, pady=6)
        win.preview_label = tk.Label(form, bg="#112240")
        win.preview_label.grid(row=photo_row+1, column=1, sticky="w", padx=6, pady=10)

        if self.photo_blob:
            try:
                img = Image.open(io.BytesIO(self.photo_blob))
                img.thumbnail((120,120))
                self.preview_img = ImageTk.PhotoImage(img)
                win.preview_label.config(image=self.preview_img)
                win.preview_label.image = self.preview_img
            except: pass

        # Buttons
        btn_frame = tk.Frame(win, bg="#0a192f")
        btn_frame.pack(pady=14)
        tk.Button(btn_frame, text="Save", bg="#64ffda", fg="black",
                  font=("Segoe UI", 12, "bold"), width=12, relief="flat",
                  command=lambda: self.save_student(data, win)).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Cancel", bg="#e63946", fg="white",
                  font=("Segoe UI", 12, "bold"), width=12, relief="flat", command=win.destroy).pack(side="left", padx=8)

    # ---------- Save ----------
    def save_student(self, data, win):
        prn = self.form_vars["prn"].get().strip()
        roll_no = self.form_vars["roll_no"].get().strip()
        name = self.form_vars["name"].get().strip()
        class_ = self.form_vars["class_"].get().strip()
        division = self.form_vars["division"].get().strip()
        email = self.form_vars["email"].get().strip()
        password = self.form_vars["password"].get().strip()

        if not (prn and roll_no and name and class_ and division and email):
            messagebox.showwarning("Validation", "All fields except photo and password are required.")
            return
        if not data and not password:
            messagebox.showwarning("Validation", "Password is required for new student.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            if data:  # edit
                if password:
                    hashed = hash_password(password)
                    cur.execute("UPDATE students SET roll_no=?, name=?, class=?, division=?, email=?, password=?, photo=? WHERE prn=?",
                                (roll_no, name, class_, division, email, hashed, self.photo_blob, prn))
                else:
                    cur.execute("UPDATE students SET roll_no=?, name=?, class=?, division=?, email=?, photo=? WHERE prn=?",
                                (roll_no, name, class_, division, email, self.photo_blob, prn))
            else:  # add
                hashed = hash_password(password)
                cur.execute("INSERT INTO students (prn, roll_no, name, class, division, email, password, photo) VALUES (?,?,?,?,?,?,?,?)",
                            (prn, roll_no, name, class_, division, email, hashed, self.photo_blob))
            conn.commit()
            conn.close()
            self.load_students()
            win.destroy()
            messagebox.showinfo("Success", "Student saved successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            try: conn.close()
            except: pass

    # ---------- Delete ----------
    def delete_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a student to delete.")
            return
        item = self.tree.item(sel[0])["values"]
        prn = item[0]
        name = item[2]
        if messagebox.askyesno("Delete", f"Delete student {name} ({prn})?"):
            self.run_query("DELETE FROM students WHERE prn=?", (prn,), fetch=False)
            self.load_students()

    # ---------- Export ----------
    def generate_excel(self):
        try:
            rows = self.run_query("SELECT prn, roll_no, name, class, division, email FROM students ORDER BY name")
            if not rows:
                messagebox.showinfo("No Data", "No student data found.")
                return
            df = pd.DataFrame(rows, columns=["PRN", "Roll No", "Name", "Class", "Division", "Email"])
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")],
                                                     title="Save Excel File")
            if save_path:
                df.to_excel(save_path, index=False)
                messagebox.showinfo("Success", f"Excel file saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Excel file:\n{e}")
