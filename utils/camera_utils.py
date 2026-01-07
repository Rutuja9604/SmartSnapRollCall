# utils/face_recognition_utils.py
import face_recognition
import numpy as np
from PIL import Image
from io import BytesIO
from utils.database import get_connection
import threading
import time

# Cache variables
_known_lock = threading.Lock()
_known_encodings = []
_known_details = []
_last_load_time = 0


def _bytes_to_rgb(img_bytes):
    """Convert DB-stored bytes -> RGB NumPy array"""
    try:
        img = Image.open(BytesIO(img_bytes))
        img = img.convert("RGB")
        arr = np.array(img)

        if arr.dtype != np.uint8:
            arr = arr.astype(np.uint8)

        if arr.ndim != 3 or arr.shape[2] != 3:
            print("DEBUG: Unexpected image shape:", arr.shape)
            return None

        return arr

    except Exception as e:
        print("ERROR: _bytes_to_rgb failed:", e)
        return None


def reload_known_students(force=False):
    """Load student encodings from database (cached)."""
    global _known_encodings, _known_details, _last_load_time

    with _known_lock:
        if _known_encodings and not force:
            return len(_known_encodings), _last_load_time

        encodings = []
        details = []

        try:
            conn = get_connection()
            conn.row_factory = sqlite3.Row      # IMPORTANT FIX
            cur = conn.cursor()

            # FIX: correct table name
            cur.execute("SELECT prn, name, photo FROM student")
            rows = cur.fetchall()
            conn.close()

        except Exception as e:
            print("ERROR: reload_known_students DB read failed:", e)
            return 0, _last_load_time

        for r in rows:
            prn = r["prn"]
            name = r["name"]
            photo = r["photo"]

            if not photo:
                continue

            img = _bytes_to_rgb(photo)
            if img is None:
                print(f"WARNING: Could not decode student image for PRN {prn}")
                continue

            try:
                locs = face_recognition.face_locations(img, model="hog")
                if not locs:
                    print(f"WARNING: No face found in student photo for PRN {prn}")
                    continue

                enc = face_recognition.face_encodings(img, locs)[0]
                encodings.append(enc)
                details.append({"prn": prn, "name": name})

            except Exception as e:
                print(f"ERROR: encoding failed for PRN {prn} -> {e}")

        _known_encodings = encodings
        _known_details = details
        _last_load_time = time.time()

        print(f"DEBUG: reload_known_students -> loaded {len(encodings)} encodings")
        return len(encodings), _last_load_time


def recognize_students(group_photo_bytes, tolerance=0.50, reload_if_empty=True):
    """Recognize faces in the uploaded group photo."""
    img = _bytes_to_rgb(group_photo_bytes)
    if img is None:
        raise ValueError("Unsupported image: could not convert to RGB")

    # Ensure encodings are loaded
    with _known_lock:
        if not _known_encodings:
            if reload_if_empty:
                reload_known_students()

        if not _known_encodings:
            # No students in DB
            locs = face_recognition.face_locations(img, model="hog")
            return [], len(locs)

        known_encs = _known_encodings.copy()
        known_det = _known_details.copy()

    # Detect faces
    face_locs = face_recognition.face_locations(img, model="hog")
    face_encs = face_recognition.face_encodings(img, face_locs)

    recognized_prns = []
    unknown = 0

    for enc in face_encs:
        distances = face_recognition.face_distance(known_encs, enc)

        if len(distances) == 0:
            unknown += 1
            continue

        best_idx = np.argmin(distances)
        best_distance = float(distances[best_idx])

        if best_distance <= tolerance:
            recognized_prns.append(known_det[best_idx]["prn"])
        else:
            unknown += 1

    recognized_prns = list(dict.fromkeys(recognized_prns))
    return recognized_prns, unknown
