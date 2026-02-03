import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import get_connection
import hashlib


class TeacherModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.create_styles()
        self.create_widgets()
        self.load_teachers()

    # ---------------- STYLES ----------------
    def create_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("MainBG.TFrame", background="#0a192f")

        style.configure("Title.TLabel",
                        background="#0a192f",
                        foreground="#64ffda",
                        font=("Segoe UI", 24, "bold"))

        style.configure("Card.TFrame",
                        background="#112240")

        style.configure("Normal.TButton",
                        background="#233554",
                        foreground="white",
                        font=("Segoe UI", 12, "bold"),
                        padding=10)
        style.map("Normal.TButton", background=[("active", "#1f2d3e")])

        style.configure("Success.TButton",
                        background="#64ffda",
                        foreground="black",
                        font=("Segoe UI", 12, "bold"),
                        padding=10)
        style.map("Success.TButton", background=[("active", "#52e0c4")])

        style.configure("Danger.TButton",
                        background="#e63946",
                        foreground="white",
                        font=("Segoe UI", 12, "bold"),
                        padding=10)
        style.map("Danger.TButton", background=[("active", "#c62828")])

        style.configure("Treeview",
                        background="#112240",
                        foreground="white",
                        rowheight=32,
                        fieldbackground="#112240",
                        font=("Segoe UI", 12))

        style.configure("Treeview.Heading",
                        background="#233554",
                        foreground="#64ffda",
                        font=("Segoe UI", 13, "bold"))

        style.map("Treeview",
                  background=[("selected", "#64ffda")],
                  foreground=[("selected", "black")])

    # ---------------- WIDGETS ----------------
    def create_widgets(self):
        # Use GRID so buttons never disappear
        self.configure(style="MainBG.TFrame")
        self.grid_rowconfigure(1, weight=1)   # tree row grows
        self.grid_columnconfigure(0, weight=1)

        # HEADER
        header = ttk.Frame(self, style="MainBG.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Teacher Management", style="Title.TLabel").grid(row=0, column=0, sticky="w")

        # TABLE CARD
        table_card = ttk.Frame(self, style="Card.TFrame")
        table_card.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        cols = ("id", "username", "name", "email", "phone", "subject")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings")
        headings = ["ID", "Username", "Name", "Email", "Phone", "Subject"]
        widths = [70, 150, 200, 240, 140, 160]

        for col, head, width in zip(cols, headings, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        vsb.grid(row=0, column=1, sticky="ns", pady=10, padx=(0, 10))

        self.tree.bind("<Double-1>", self.edit_selected)

        # ✅ BUTTONS ALWAYS VISIBLE (row=2, no expand)
        btns = ttk.Frame(self, style="MainBG.TFrame")
        btns.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 20))

        ttk.Button(btns, text="➕ Add Teacher", style="Success.TButton", command=self.add_teacher)\
            .pack(side="left", padx=8)

        ttk.Button(btns, text="✏️ Edit Teacher", style="Normal.TButton", command=self.edit_selected)\
            .pack(side="left", padx=8)

        ttk.Button(btns, text="🗑 Delete Teacher", style="Danger.TButton", command=self.delete_teacher)\
            .pack(side="left", padx=8)

    # ---------------- DATABASE ----------------
    def run_query(self, query, params=(), fetch=True):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        if fetch:
            data = cur.fetchall()
            conn.close()
            return data
        conn.commit()
        conn.close()

    # ---------------- LOAD ----------------
    def load_teachers(self):
        self.tree.delete(*self.tree.get_children())
        rows = self.run_query(
            "SELECT id, username, name, email, phone, subject FROM teachers ORDER BY id DESC"
        )
        for r in rows:
            self.tree.insert("", "end",
                             values=(r["id"], r["username"], r["name"], r["email"], r["phone"], r["subject"]))

    # ---------------- ADD / EDIT ----------------
    def add_teacher(self):
        self._open_form_window("Add Teacher")

    def edit_selected(self, event=None):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Please select a teacher to edit.")
            return
        data = self.tree.item(selected, "values")
        self._open_form_window("Edit Teacher", data)

    def _open_form_window(self, title, data=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("600x600")
        win.configure(bg="#0a192f")
        win.grab_set()

        tk.Label(win, text=title, font=("Segoe UI", 22, "bold"),
                 fg="#64ffda", bg="#0a192f").pack(pady=15)

        form = tk.Frame(win, bg="#112240")
        form.pack(fill="both", expand=True, padx=20, pady=10)

        subjects = [s[0] for s in self.run_query("SELECT name FROM subjects ORDER BY name")]
        fields = [("Username", "username"), ("Teacher Name", "name"), ("Email", "email"),
                  ("Phone", "phone"), ("Subject", "subject"), ("Password", "password")]

        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, fg="white", bg="#112240",
                     font=("Segoe UI", 11, "bold")).grid(row=i, column=0, sticky="w", pady=10, padx=10)

            if key == "subject":
                self.vars[key] = tk.StringVar(value=(data[5] if data else ""))
                ttk.Combobox(form, textvariable=self.vars[key], values=subjects, width=35, state="readonly")\
                    .grid(row=i, column=1, pady=10, padx=10)
                continue

            if key == "password":
                self.vars[key] = tk.StringVar(value="")
                ttk.Entry(form, textvariable=self.vars[key], show="*", width=37)\
                    .grid(row=i, column=1, pady=10, padx=10)
                continue

            default = data[i + 1] if data else ""
            self.vars[key] = tk.StringVar(value=default)
            ttk.Entry(form, textvariable=self.vars[key], width=37)\
                .grid(row=i, column=1, pady=10, padx=10)

        # Buttons
        btn_frame = tk.Frame(win, bg="#0a192f")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Save", bg="#64ffda", fg="black",
                  font=("Segoe UI", 12, "bold"), width=14, relief="flat",
                  command=lambda: self.save_teacher(data, win)).pack(side="left", padx=10)

        tk.Button(btn_frame, text="Cancel", bg="#e63946", fg="white",
                  font=("Segoe UI", 12, "bold"), width=14, relief="flat",
                  command=win.destroy).pack(side="left", padx=10)

    # ---------------- SAVE ----------------
    def save_teacher(self, data, win):
        username = self.vars["username"].get().strip()
        name = self.vars["name"].get().strip()
        email = self.vars["email"].get().strip()
        phone = self.vars["phone"].get().strip()
        subject = self.vars["subject"].get().strip()
        password = self.vars["password"].get().strip()

        if not (username and name and email and phone and subject):
            messagebox.showwarning("Validation", "All fields except password are required.")
            return

        try:
            if data:  # Edit
                if password:
                    hashed = hashlib.sha256(password.encode()).hexdigest()
                    self.run_query(
                        "UPDATE teachers SET username=?, name=?, email=?, phone=?, subject=?, password=? WHERE id=?",
                        (username, name, email, phone, subject, hashed, data[0]), fetch=False
                    )
                else:
                    self.run_query(
                        "UPDATE teachers SET username=?, name=?, email=?, phone=?, subject=? WHERE id=?",
                        (username, name, email, phone, subject, data[0]), fetch=False
                    )
            else:  # Add
                if not password:
                    messagebox.showwarning("Validation", "Password is required for new teacher.")
                    return
                hashed = hashlib.sha256(password.encode()).hexdigest()
                self.run_query(
                    "INSERT INTO teachers (username,name,email,phone,subject,password) VALUES (?,?,?,?,?,?)",
                    (username, name, email, phone, subject, hashed), fetch=False
                )

            self.load_teachers()
            win.destroy()
            messagebox.showinfo("Success", "Teacher saved successfully!")

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # ---------------- DELETE ----------------
    def delete_teacher(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Please select a teacher.")
            return

        values = self.tree.item(selected, "values")
        tid = values[0]

        if messagebox.askyesno("Confirm", "Are you sure you want to delete?"):
            self.run_query("DELETE FROM teachers WHERE id=?", (tid,), fetch=False)
            self.load_teachers()
