import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import threading
import time

import os

# Import login classes directly
from admin_login import AdminLogin
from teacher_login import TeacherLogin
from login_student import StudentLogin


class SmartSnapHome(tk.Tk):
    def __init__(self):
        super().__init__()

        # ---------- WINDOW SETTINGS ----------
        self.title("Smart Snap Attendance System")
        self.geometry("1200x720")
        self.minsize(1000, 600)
        self.configure(bg="#0a192f")

        # ---------- BACKGROUND VIDEO ----------
        self.video_path = "background.mp4"
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not load background video!")
            self.destroy()
            return

        self.bg_label = tk.Label(self)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # ---------- GLASS EFFECT ----------
        self.overlay = tk.Frame(self, bg="#000000", bd=0)
        self.overlay.place(relx=0.5, rely=0.5, anchor="center")

        # ---------- TITLE ----------
        self.title_label = tk.Label(
            self.overlay,
            text="SMART SNAP ATTENDANCE SYSTEM",
            font=("Segoe UI", 34, "bold"),
            fg="#64ffda",
            bg="#000000"
        )
        self.title_label.pack(pady=(30, 20))

        # ---------- BUTTONS ----------
        self.button_frame = tk.Frame(self.overlay, bg="#000000")
        self.button_frame.pack(pady=20)

        self.admin_btn = self.create_role_button("👨‍💼  Admin", "#0078D7", self.open_admin)
        self.teacher_btn = self.create_role_button("👩‍🏫  Teacher", "#2ECC71", self.open_teacher)
        self.student_btn = self.create_role_button("🎓  Student", "#F1C40F", self.open_student)

        # ---------- FOOTER ----------
        self.footer = tk.Label(
            self,
            text="© 2025 Smart Snap Attendance System",
            font=("Segoe UI", 10, "italic"),
            bg="#0a192f",
            fg="#c0c0c0",
        )
        self.footer.pack(side="bottom", pady=10)

        # ---------- START VIDEO THREAD ----------
        self.running = True
        self.play_video()


        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- BUTTON CREATOR ----------
    def create_role_button(self, text, color, command):
        btn = tk.Label(
            self.button_frame,
            text=text,
            font=("Segoe UI", 18, "bold"),
            bg=color,
            fg="white",
            padx=50,
            pady=20,
            cursor="hand2",
            relief="flat"
        )
        btn.pack(side="left", padx=35, pady=10)

        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.lighten(color), fg="black"))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=color, fg="white"))
        btn.bind("<Button-1>", lambda e: command())
        return btn

    # ---------- LIGHTEN COLOR ----------
    def lighten(self, color, factor=0.25):
        color = color.lstrip("#")
        r, g, b = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ---------- OPEN LOGIN WINDOWS ----------
    def open_admin(self):
        self.open_login_window(AdminLogin)

    def open_teacher(self):
        self.open_login_window(TeacherLogin)

    def open_student(self):
        self.open_login_window(StudentLogin)

    def open_login_window(self, LoginClass):
        self.running = False
        try:
            if self.cap.isOpened():
                self.cap.release()
        except:
            pass

        self.destroy()
        login_window = LoginClass()
        login_window.mainloop()

    # ---------- BACKGROUND VIDEO THREAD ----------
    def play_video(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        # Resize only ONCE to window size
        w = self.winfo_width()
        h = self.winfo_height()
        img = img.resize((w, h), Image.LANCZOS)

        imgtk = ImageTk.PhotoImage(img)
        self.bg_label.imgtk = imgtk
        self.bg_label.config(image=imgtk)

        # Call this function again after 25 ms (40 FPS smooth video)
        self.after(25, self.play_video)

    # ---------- WINDOW CLOSE ----------
    def on_close(self):
        self.running = False
        try:
            if self.cap.isOpened():
                self.cap.release()
        except:
            pass

        self.destroy()


if __name__ == "__main__":
    app = SmartSnapHome()
    app.mainloop()
