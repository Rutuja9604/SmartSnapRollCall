import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import os

icon_path = os.path.join("assets", "logo.png")
icon = tk.PhotoImage(file=icon_path)
self.iconphoto(True, icon)
# ✅ Import routed Frame pages (NOT Tk windows)
from admin_login import AdminLoginPage
from teacher_login import TeacherLoginPage
from login_student import StudentLoginPage
from admin_dashboard import AdminDashboardPage
from Teacher_Dashboard import TeacherDashboardPage
from student_dashboard import StudentDashboardPage


class SmartSnapApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Smart Snap Attendance System")
        self.geometry("1200x720")
        self.minsize(1000, 600)
        self.configure(bg="#0a192f")

        # Session storage (later use for route guards)
        self.session = {"admin": None, "teacher": None, "student": None}

        # Back navigation history
        self.history = []
        self.current_page = None

        # Container holds all pages (Frames)
        self.container = tk.Frame(self, bg="#0a192f")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # ✅ Register pages
        self.register(HomePage)
        self.register(AdminLoginPage)
        self.register(TeacherLoginPage)
        self.register(StudentLoginPage)
        self.register(AdminDashboardPage)
        self.register(TeacherDashboardPage)
        self.register(StudentDashboardPage)

        # Start route
        self.navigate("HomePage", add_to_history=False)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def register(self, PageClass):
        name = PageClass.__name__
        frame = PageClass(self.container, self)
        self.frames[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def navigate(self, page_name: str, add_to_history=True):
        print("➡ Navigating to:", page_name)
        print("📄 Registered pages:", list(self.frames.keys()))

        if page_name not in self.frames:
            messagebox.showerror(
                "Routing Error",
                f"Page not registered: {page_name}"
            )
            return

        if self.current_page:
            cur = self.frames[self.current_page]
            if hasattr(cur, "on_hide"):
                cur.on_hide()

        if add_to_history and self.current_page and self.current_page != page_name:
            self.history.append(self.current_page)

        self.current_page = page_name
        nxt = self.frames[page_name]
        nxt.tkraise()

        if hasattr(nxt, "on_show"):
            nxt.on_show()

    def back(self):
        if self.history:
            prev = self.history.pop()
            self.navigate(prev, add_to_history=False)

    def on_close(self):
        if self.current_page:
            cur = self.frames[self.current_page]
            if hasattr(cur, "on_hide"):
                cur.on_hide()
        self.destroy()


class HomePage(tk.Frame):
    def __init__(self, parent, controller: SmartSnapApp):
        super().__init__(parent, bg="#0a192f")
        self.controller = controller

        # ---------- VIDEO ----------
        self.video_path = "background.mp4"
        self.cap = None
        self.running = False

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

        self.create_role_button(
            "👨‍💼  Admin", "#0078D7",
            lambda: self.controller.navigate("AdminLoginPage")
        )

        self.create_role_button(
            "👩‍🏫  Teacher", "#2ECC71",
            lambda: self.controller.navigate("TeacherLoginPage")
        )

        self.create_role_button(
            "🎓  Student", "#F1C40F",
            lambda: self.controller.navigate("StudentLoginPage")
        )

        # ---------- FOOTER ----------
        self.footer = tk.Label(
            self,
            text="© 2026 Smart Snap Attendance System",
            font=("Segoe UI", 10, "italic"),
            bg="#0a192f",
            fg="#c0c0c0",
        )
        self.footer.pack(side="bottom", pady=10)

    # Called when page becomes active
    def on_show(self):
        if not os.path.exists(self.video_path):
            messagebox.showerror("Error", f"Could not find: {self.video_path}")
            return

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not load background video!")
            self.cap = None
            return

        self.running = True
        self.play_video()

    # Called when leaving the page
    def on_hide(self):
        self.running = False
        try:
            if self.cap and self.cap.isOpened():
                self.cap.release()
        except:
            pass
        self.cap = None

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

    def lighten(self, color, factor=0.25):
        color = color.lstrip("#")
        r, g, b = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def play_video(self):
        if not self.running or not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                self.after(50, self.play_video)
                return

        w = self.winfo_width()
        h = self.winfo_height()

        if w < 50 or h < 50:
            self.after(50, self.play_video)
            return

        frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(img)

        self.bg_label.imgtk = imgtk
        self.bg_label.configure(image=imgtk)

        self.after(33, self.play_video)


if __name__ == "__main__":
    app = SmartSnapApp()
    app.mainloop()
