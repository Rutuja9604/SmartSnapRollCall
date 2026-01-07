import io
import os
from datetime import datetime
import threading
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import sqlite3
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from utils.database import get_connection
from utils.face_recognition_utils import recognize_students
import openpyxl

# ------------------------- Utility functions -------------------------
def get_exif_gps(img_path):
    try:
        img = Image.open(img_path)
        exif_data = img._getexif()
        if not exif_data:
            return None, None
        from PIL.ExifTags import TAGS, GPSTAGS
        gps_info = {}
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_info[sub_decoded] = value[t]

        def convert_to_degrees(val):
            d = val[0][0] / val[0][1]
            m = val[1][0] / val[1][1]
            s = val[2][0] / val[2][1]
            return d + (m / 60.0) + (s / 3600.0)

        if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
            lat = convert_to_degrees(gps_info["GPSLatitude"])
            if gps_info["GPSLatitudeRef"] != "N":
                lat = -lat
        else:
            lat = None

        if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
            lon = convert_to_degrees(gps_info["GPSLongitude"])
            if gps_info["GPSLongitudeRef"] != "E":
                lon = -lon
        else:
            lon = None

        return lat, lon
    except:
        return None, None

def capture_from_webcam(parent, window_title="Press SPACE to capture, ESC to cancel"):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        messagebox.showerror("Webcam Error", "Cannot access webcam.")
        return None
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    captured_bytes = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        preview = cv2.flip(frame, 1)
        cv2.imshow(window_title, preview)
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # SPACE
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                captured_bytes = buf.tobytes()
            break
        if key == 27:  # ESC
            captured_bytes = None
            break
    cap.release()
    cv2.destroyWindow(window_title)
    return captured_bytes

def choose_mobile_photo(parent):
    path = filedialog.askopenfilename(
        parent=parent,
        title="Select Mobile Camera Photo",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
    )
    if not path:
        return None, None, None
    try:
        img = Image.open(path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        photo_bytes = buf.getvalue()
        lat, lon = get_exif_gps(path)
        return photo_bytes, lat, lon
    except Exception as e:
        messagebox.showerror("File Error", f"Cannot read selected image:\n{e}")
        return None, None, None

# ------------------------- Teacher Dashboard -------------------------
class TeacherDashboard(tb.Window):

    def __init__(self, teacher_id=1, teacher_name="Teacher"):
        super().__init__(title="Smart Snap - Teacher Dashboard", themename="litera")
        self.geometry("1200x720")
        self.minsize(1000, 600)

        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.class_var = tb.StringVar()
        self.division_var = tb.StringVar()
        self.subject_var = tb.StringVar()
        self.all_present_toggle = tb.BooleanVar(value=False)

        self.location_var = tb.StringVar(value="Unknown Location")
        self.lat_var = tb.StringVar(value="")
        self.lon_var = tb.StringVar(value="")

        self.last_group_photo = None
        self.tk_photo = None  # Keep reference to PhotoImage

        self.create_header()
        self.create_filters()
        self.create_table_and_photo()
        self.create_actions()

    # ---------------- UI ----------------
    def create_header(self):
        tb.Label(self, text=f"📸 Smart Snap - {self.teacher_name}", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(pady=8)
        tb.Label(self, textvariable=self.subject_var, font=("Segoe UI", 12, "bold")).pack()

    def create_filters(self):
        f = tb.Frame(self)
        f.pack(fill="x", padx=18, pady=6)

        tb.Label(f, text="Class:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=5)
        tb.Combobox(f, textvariable=self.class_var, values=["MCA1","MCA2","MBA1","MBA2"], width=12).grid(row=0,column=1,padx=5)

        tb.Label(f, text="Division:", font=("Segoe UI", 11, "bold")).grid(row=0, column=2, padx=5)
        tb.Combobox(f, textvariable=self.division_var, values=["A","B","C"], width=10).grid(row=0,column=3,padx=5)

        tb.Label(f, text="Subject:", font=("Segoe UI", 11, "bold")).grid(row=0,column=4,padx=5)
        self.subject_cb = tb.Combobox(f, textvariable=self.subject_var, values=self.get_subjects_from_db(), width=24)
        self.subject_cb.grid(row=0,column=5,padx=5)

        tb.Button(f, text="Load Students", bootstyle="success-outline", command=self.load_filtered_students).grid(row=0,column=6,padx=10)

        g = tb.Frame(self)
        g.pack(fill="x", padx=18, pady=(6,12))
        tb.Label(g, text="Location:", font=("Segoe UI",10,"bold")).grid(row=0,column=0,padx=6)
        tb.Entry(g, textvariable=self.location_var, width=40).grid(row=0,column=1,padx=6)
        tb.Label(g, text="Lat:", font=("Segoe UI",10,"bold")).grid(row=0,column=2,padx=6)
        tb.Entry(g, textvariable=self.lat_var, width=12).grid(row=0,column=3,padx=6)
        tb.Label(g, text="Lon:", font=("Segoe UI",10,"bold")).grid(row=0,column=4,padx=6)
        tb.Entry(g, textvariable=self.lon_var, width=12).grid(row=0,column=5,padx=6)

    # ---------------- Table + Photo ----------------
    def create_table_and_photo(self):
        container = tb.Frame(self)
        container.pack(fill="both", expand=True, padx=18, pady=8)

        # Left: Student Table
        table_frame = tb.Frame(container)
        table_frame.pack(side="left", fill="both", expand=True)

        cols = ("PRN","Roll No","Name","Class","Division","Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor="center")
        self.tree.tag_configure("present", foreground="green")
        self.tree.tag_configure("absent", foreground="red")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click_toggle)

        # Right: Group Photo
        self.photo_frame = tb.Frame(container, width=320)
        self.photo_frame.pack(side="left", fill="y", padx=(12,0))
        self.photo_label = tb.Label(self.photo_frame, text="No Photo Uploaded", bootstyle="info")
        self.photo_label.pack(pady=10, padx=10)

    # ---------------- Actions ----------------
    def create_actions(self):
        f = tb.Frame(self)
        f.pack(fill="x", padx=18, pady=12)
        tb.Button(f, text="📷 Capture (Webcam)", bootstyle="primary-outline", command=self.capture_and_recognize).pack(side="left", padx=8)
        tb.Button(f, text="📱 Upload Mobile Photo", bootstyle="secondary-outline", command=self.upload_mobile_and_recognize).pack(side="left", padx=8)
        tb.Checkbutton(f, text="Mark All Present", variable=self.all_present_toggle, bootstyle="success-round-toggle", command=self.toggle_all_present).pack(side="left", padx=12)
        tb.Button(f, text="💾 Save Attendance Now", bootstyle="success", command=self.export_attendance_excel).pack(side="right", padx=8)

    # ---------------- DB Helpers ----------------
    def get_subjects_from_db(self):
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM subjects ORDER BY name")
            return [r["name"] for r in cur.fetchall()]
        except:
            return []
        finally:
            conn.close()

    # ---------------- Load Students ----------------
    def load_filtered_students(self):
        cls = self.class_var.get().strip()
        div = self.division_var.get().strip()
        if not cls or not div:
            messagebox.showwarning("Missing", "Select Class and Division first.")
            return
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute("SELECT prn, roll_no, name, class, division FROM students WHERE class=? AND division=? ORDER BY roll_no", (cls, div))
            rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            rows = []
        finally:
            conn.close()
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=(r["prn"], r["roll_no"], r["name"], r["class"], r["division"], "Absent"), tags=("absent",))

    # ---------------- Toggle ----------------
    def toggle_all_present(self):
        val = self.all_present_toggle.get()
        status = "Present" if val else "Absent"
        tag = "present" if val else "absent"
        for item in self.tree.get_children():
            self.tree.set(item, "Status", status)
            self.tree.item(item, tags=(tag,))

    def on_double_click_toggle(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        cur = self.tree.set(item, "Status")
        new_status = "Absent" if cur=="Present" else "Present"
        tag = "absent" if new_status=="Absent" else "present"
        self.tree.set(item,"Status",new_status)
        self.tree.item(item, tags=(tag,))

    # ---------------- Recognition Flow ----------------
    def capture_and_recognize(self):
        if not self.subject_var.get().strip():
            messagebox.showwarning("Missing", "Select subject first.")
            return
        def worker():
            photo_bytes = capture_from_webcam(self)
            if not photo_bytes:
                return
            self.process_recognition(photo_bytes)
        threading.Thread(target=worker, daemon=True).start()

    def upload_mobile_and_recognize(self):
        if not self.subject_var.get().strip():
            messagebox.showwarning("Missing", "Select subject first.")
            return
        photo_bytes, lat, lon = choose_mobile_photo(self)
        if not photo_bytes:
            return
        if lat and lon:
            self.lat_var.set(f"{lat:.6f}")
            self.lon_var.set(f"{lon:.6f}")
            self.location_var.set(f"Lat: {lat:.6f}, Lon: {lon:.6f}")
        else:
            self.location_var.set("Unknown Location")
            self.lat_var.set("")
            self.lon_var.set("")
        if not self.tree.get_children():
            self.load_filtered_students()
            if not self.tree.get_children():
                messagebox.showwarning("No Students", "No students loaded to mark attendance.")
                return
        self.process_recognition(photo_bytes)

    # ---------------- Display & Recognition ----------------
    def process_recognition(self, photo_bytes):
        # ---------------- Display photo ----------------
        try:
            pil_img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
            pil_img.thumbnail((300, 300))
            self.tk_photo = ImageTk.PhotoImage(pil_img)
            self.photo_label.configure(image=self.tk_photo, text="")
        except Exception as e:
            messagebox.showwarning("Display Error", str(e))

        # ---------------- Face Recognition ----------------
        try:
            # 🔥 FORCE reload encodings every time
            from utils.face_recognition_utils import reload_known_students
            reload_known_students(force=True)

            present_prns, unknown_count = recognize_students(photo_bytes)
        except Exception as e:
            messagebox.showerror("Recognition Error", str(e))
            return

        # ---------------- Normalize PRNs ----------------
        present_set = set(str(p).strip() for p in present_prns)

        print("DEBUG: Recognized PRNs ->", present_set)

        matched = 0

        for item in self.tree.get_children():
            tree_prn = str(self.tree.item(item)["values"][0]).strip()

            if tree_prn in present_set:
                self.tree.set(item, "Status", "Present")
                self.tree.item(item, tags=("present",))
                matched += 1
            else:
                self.tree.set(item, "Status", "Absent")
                self.tree.item(item, tags=("absent",))

        print(f"DEBUG: Matched {matched} students in table")

        self.last_group_photo = photo_bytes
        self.save_to_db(photo_bytes)

        if unknown_count > 0:
            messagebox.showwarning("Unknown Faces", f"{unknown_count} unknown face(s) detected.")

        messagebox.showinfo(
            "Done",
            f"Recognition completed.\nPresent: {matched}\nUnknown: {unknown_count}"
        )

    # ---------------- Save Attendance DB ----------------
    def save_to_db(self, photo_bytes):
        if not self.subject_var.get().strip() or not self.tree.get_children():
            return
        subject = self.subject_var.get().strip()
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM subjects WHERE name=?", (subject,))
            row = cur.fetchone()
            if not row:
                messagebox.showerror("DB Error", "Selected subject not found in database.")
                return
            subject_id = row["id"]
            date = datetime.now().strftime("%Y-%m-%d")
            time_now = datetime.now().strftime("%H:%M:%S")
            location = self.location_var.get().strip()
            latitude = float(self.lat_var.get()) if self.lat_var.get() else None
            longitude = float(self.lon_var.get()) if self.lon_var.get() else None

            for item in self.tree.get_children():
                prn = str(self.tree.item(item)["values"][0]).strip()
                status = self.tree.set(item,"Status")
                cur.execute("""SELECT id FROM attendance WHERE prn=? AND subject_id=? AND date=?""",(prn,subject_id,date))
                existing = cur.fetchone()
                if existing:
                    cur.execute("""UPDATE attendance SET teacher_id=?, time=?, status=?, photo=?, location=?, latitude=?, longitude=? WHERE id=?""",
                                (self.teacher_id,time_now,status,photo_bytes,location,latitude,longitude,existing["id"]))
                else:
                    cur.execute("""INSERT INTO attendance(prn,subject_id,teacher_id,date,time,status,photo,location,latitude,longitude) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                (prn,subject_id,self.teacher_id,date,time_now,status,photo_bytes,location,latitude,longitude))
            conn.commit()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("DB Error", f"Saving attendance failed:\n{e}")
        finally:
            conn.close()

    # ---------------- Export Attendance Excel ----------------
    def export_attendance_excel(self):
        if not self.tree.get_children():
            messagebox.showwarning("No Data", "No attendance data to export.")
            return
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "Attendance"
        headers = ["PRN","Roll No","Name","Class","Division","Status"]
        sheet.append(headers)
        for item in self.tree.get_children():
            row = self.tree.item(item)["values"]
            sheet.append(row)
        filename = f"attendance_{datetime.now().strftime('%Y_%m_%d')}.xlsx"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        wb.save(downloads_path)
        messagebox.showinfo("Success", f"Attendance saved in Excel:\n{downloads_path}")


# ------------------------- Run -------------------------
if __name__ == "__main__":
    app = TeacherDashboard(teacher_id=1, teacher_name="abc")
    app.mainloop()
