import tkinter as tk
from tkinter import messagebox
import sqlite3

DB = "attendance.db"

# =================== DATABASE FUNCTIONS ===================

def connect_db():
    return sqlite3.connect(DB)

def add_subject():
    subject = entry_subject.get().strip()
    teacher = entry_teacher.get().strip()

    if not subject or not teacher:
        messagebox.showwarning("Missing", "Please fill all fields.")
        return

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO subject (subject_name, teacher_name)
            VALUES (?, ?)
        """, (subject, teacher))
        conn.commit()
        messagebox.showinfo("Added", f"{subject} assigned to {teacher}")
        entry_subject.delete(0, tk.END)
        entry_teacher.delete(0, tk.END)
        load_subjects()
    except sqlite3.IntegrityError:
        messagebox.showerror("Exists", "This subject already exists.")
    finally:
        conn.close()


def delete_selected():
    selected = subject_listbox.curselection()
    if not selected:
        messagebox.showwarning("No Selection", "Select a subject to delete.")
        return

    subject = subject_listbox.get(selected[0])

    if messagebox.askyesno("Confirm", f"Delete '{subject}'?"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subject WHERE subject_name = ?", (subject,))
        conn.commit()
        conn.close()
        load_subjects()


def load_subjects():
    subject_listbox.delete(0, tk.END)
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT subject_name FROM subject ORDER BY subject_name")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        subject_listbox.insert(tk.END, row[0])


# =================== GUI ===================

root = tk.Tk()
root.title("Manage Subjects")
root.geometry("450x450")
root.configure(bg="#1e272e")

title = tk.Label(root, text="📘 Manage Subjects", font=("Segoe UI", 18, "bold"),
                 bg="#1e272e", fg="#00cec9")
title.pack(pady=15)

form_frame = tk.Frame(root, bg="#1e272e")
form_frame.pack(pady=10)

# Subject input
tk.Label(form_frame, text="Subject Name:", font=("Segoe UI", 12), bg="#1e272e", fg="white").grid(row=0, column=0, pady=10, sticky="w")
entry_subject = tk.Entry(form_frame, width=30, font=("Segoe UI", 12))
entry_subject.grid(row=0, column=1, pady=10)

# Teacher input
tk.Label(form_frame, text="Teacher Name:", font=("Segoe UI", 12), bg="#1e272e", fg="white").grid(row=1, column=0, pady=10, sticky="w")
entry_teacher = tk.Entry(form_frame, width=30, font=("Segoe UI", 12))
entry_teacher.grid(row=1, column=1, pady=10)

# Add button
tk.Button(root, text="➕ Add Subject", font=("Segoe UI", 12, "bold"),
          bg="#00b894", fg="white", width=20, command=add_subject).pack(pady=15)

# Subject list
tk.Label(root, text="Available Subjects:", font=("Segoe UI", 14, "bold"),
         bg="#1e272e", fg="white").pack()

subject_listbox = tk.Listbox(root, height=10, width=40, font=("Segoe UI", 12))
subject_listbox.pack(pady=10)

# Delete button
tk.Button(root, text="🗑 Delete Selected Subject", font=("Segoe UI", 12, "bold"),
          bg="#d63031", fg="white", width=25, command=delete_selected).pack(pady=10)

load_subjects()
root.mainloop()
