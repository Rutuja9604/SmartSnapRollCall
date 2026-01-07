# subject_module.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import get_connection

class SubjectModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.create_widgets()
        self.load_subjects()

    def create_widgets(self):
        title = tk.Label(self, text="📚 Subject Management", bg="#0a192f", fg="#64ffda", font=("Segoe UI", 24, "bold"))
        title.pack(anchor="w", pady=(0, 20), padx=15)

        # Table
        table_frame = tk.Frame(self, bg="#112240")
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self.tree = ttk.Treeview(table_frame, columns=("id","name"), show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Subject Name")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=200, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        # Buttons
        btn_frame = tk.Frame(self, bg="#0a192f")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Add Subject", bg="#64ffda", fg="black", width=12, command=self.add_subject).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Edit Subject", bg="#0b6e7f", fg="white", width=12, command=self.edit_selected).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Delete Subject", bg="#e63946", fg="white", width=12, command=self.delete_subject).pack(side="left", padx=10)

    # ---------------- DATABASE ----------------
    def run_query(self, query, params=(), fetch=True):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        if fetch:
            data = cur.fetchall()
            conn.close()
            return data
        else:
            conn.commit()
            conn.close()

    # ---------------- LOAD ----------------
    def load_subjects(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        rows = self.run_query("SELECT id, name FROM subjects ORDER BY name")

        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["name"]))

    # ---------------- ADD / EDIT ----------------
    def add_subject(self):
        self._open_form_window("Add Subject")

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Please select a subject.")
            return
        data = self.tree.item(selected, "values")
        self._open_form_window("Edit Subject", data)

    def _open_form_window(self, title, data=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("400x200")
        win.configure(bg="#0a192f")
        win.grab_set()

        tk.Label(win, text=title, font=("Segoe UI", 20, "bold"), fg="#64ffda", bg="#0a192f").pack(pady=15)

        tk.Label(win, text="Subject Name", font=("Segoe UI", 12), fg="white", bg="#112240").pack(pady=10)
        self.var_name = tk.StringVar(value=(data[1] if data else ""))
        tk.Entry(win, textvariable=self.var_name, width=30).pack(pady=10)

        tk.Button(win, text="Save", bg="#64ffda", fg="black", width=12, command=lambda: self.save_subject(data, win)).pack(pady=15)

    def save_subject(self, data, win):
        name = self.var_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Subject name is required.")
            return
        try:
            if data:  # edit
                self.run_query("UPDATE subjects SET name=? WHERE id=?", (name, data[0]), fetch=False)
            else:  # add
                self.run_query("INSERT INTO subjects (name) VALUES (?)", (name,), fetch=False)
            self.load_subjects()
            win.destroy()
            messagebox.showinfo("Success", "Subject saved successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # ---------------- DELETE ----------------
    def delete_subject(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Please select a subject.")
            return
        values = self.tree.item(selected, "values")
        sid = values[0]
        if messagebox.askyesno("Confirm", "Are you sure you want to delete?"):
            self.run_query("DELETE FROM subjects WHERE id=?", (sid,), fetch=False)
            self.load_subjects()
