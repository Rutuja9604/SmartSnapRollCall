# utils/face_recognition_utils.py

import face_recognition
import numpy as np
from PIL import Image
import io
import sqlite3
import threading
import time
from utils.database import get_connection

# ---------------- Cache ----------------
_known_lock = threading.Lock()
_known_encodings = []
_known_prns = []
_last_load_time = 0


# ---------------- Image Conversion ----------------
def bytes_to_rgb_np(image_bytes):
    """Convert bytes → uint8 RGB NumPy array (dlib safe)"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.asarray(img, dtype=np.uint8)

    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("Unsupported image format")

    return arr


# ---------------- Load Known Students ----------------
def reload_known_students(force=False):
    global _known_encodings, _known_prns, _last_load_time

    with _known_lock:
        if _known_encodings and not force:
            return len(_known_encodings)

        print("🔄 Reloading known student encodings...")

        _known_encodings = []
        _known_prns = []

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT prn, photo FROM students WHERE photo IS NOT NULL")
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            try:
                prn = str(r["prn"]).strip()
                img_np = bytes_to_rgb_np(r["photo"])

                locs = face_recognition.face_locations(img_np, model="hog")
                if not locs:
                    continue

                enc = face_recognition.face_encodings(img_np, locs)[0]
                _known_encodings.append(enc)
                _known_prns.append(prn)

            except Exception as e:
                print(f"❌ Encoding failed for PRN {r['prn']} → {e}")

        _last_load_time = time.time()
        print(f"✅ Loaded {_last_load_time} | Faces: {len(_known_encodings)}")

        return len(_known_encodings)


# ---------------- Recognize Students ----------------
def recognize_students(image_bytes, tolerance=0.50):
    """
    Returns:
        present_prns (list[str])
        unknown_count (int)
    """

    # ALWAYS reload (important for attendance accuracy)
    reload_known_students(force=True)

    if not _known_encodings:
        print("⚠ No known student faces loaded")
        return [], 0

    img_np = bytes_to_rgb_np(image_bytes)

    face_locs = face_recognition.face_locations(img_np, model="hog")
    face_encs = face_recognition.face_encodings(img_np, face_locs)

    print(f"👥 Faces detected in group image: {len(face_encs)}")

    present = []
    unknown = 0

    for enc in face_encs:
        distances = face_recognition.face_distance(_known_encodings, enc)

        best_idx = np.argmin(distances)
        best_dist = float(distances[best_idx])

        print(f"📏 Distance: {best_dist}")

        if best_dist <= tolerance:
            prn = _known_prns[best_idx]
            present.append(prn)
            print(f"✅ Recognized PRN: {prn}")
        else:
            unknown += 1
            print("❓ Unknown face")

    # Remove duplicates
    present = list(dict.fromkeys(present))
    return present, unknown
