import sqlite3
from tkinter import Tk, Label, Entry, Button, ttk, messagebox

def view_attendance():
    prn = prn_entry.get().strip()
    if not prn:
        messagebox.showwarning("Missing", "Enter your PRN number.")
        return

    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subject.subject_name, attendance.date, attendance.time, attendance.status
        FROM attendance
        JOIN subject ON attendance.subject_id = subject.id
        WHERE attendance.student_prn = ?
        ORDER BY attendance.date DESC
    """, (prn,))
    rows = cursor.fetchall()
    conn.close()

    for i in tree.get_children():
        tree.delete(i)

    if not rows:
        messagebox.showinfo("No Data", "No attendance records found for this PRN.")
    else:
        for row in rows:
            tree.insert("", "end", values=row)

root = Tk()
root.title("Student Attendance Viewer")
root.geometry("500x400")

Label(root, text="Enter Your PRN (10-digit):").pack(pady=5)
prn_entry = Entry(root, width=30)
prn_entry.pack()

Button(root, text="View Attendance", command=view_attendance, bg="green", fg="white").pack(pady=10)

tree = ttk.Treeview(root, columns=("Subject", "Date", "Time", "Status"), show="headings")
for col in tree["columns"]:
    tree.heading(col, text=col)
tree.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()
