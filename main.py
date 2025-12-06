from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from deepface import DeepFace
import numpy as np
import sqlite3
import json
import os
import uuid

app = FastAPI()

# ---- FOLDERS -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMAGES_DIR = os.path.join(STATIC_DIR, "images")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DB_PATH = os.path.join(BASE_DIR, "students.db")

os.makedirs(IMAGES_DIR, exist_ok=True)

# ---- STATIC + TEMPLATES --------------------------------------

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ---- DATABASE ------------------------------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            reg_no TEXT UNIQUE,
            department TEXT,
            place TEXT,
            photo_path TEXT,
            embedding TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def save_student(name, reg_no, department, place, photo_path, embedding_list):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO students
        (name, reg_no, department, place, photo_path, embedding)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, reg_no, department, place, photo_path, json.dumps(embedding_list)),
    )
    conn.commit()
    conn.close()

def load_all_students():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, reg_no, department, place, photo_path, embedding FROM students"
    )
    rows = cur.fetchall()
    conn.close()
    students = []
    for r in rows:
        students.append(
            {
                "id": r[0],
                "name": r[1],
                "reg_no": r[2],
                "department": r[3],
                "place": r[4],
                "photo_path": r[5],
                "embedding": json.loads(r[6]),
            }
        )
    return students

init_db()

# ---- BASIC ROUTES (GET) --------------------------------------


@app.get("/test", response_class=HTMLResponse)
async def test():
    return "Server working"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/add-student", response_class=HTMLResponse)
async def add_student_page(request: Request):
    return templates.TemplateResponse("add_student.html", {"request": request})


@app.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request):
    return templates.TemplateResponse("verify.html", {"request": request})


# ---- ADD STUDENT (POST) --------------------------------------


@app.post("/add-student")
async def add_student(
    name: str = Form(...),
    reg_no: str = Form(...),
    department: str = Form(...),
    place: str = Form(...),
    photo: UploadFile = File(...),
):
    # Save uploaded image
    ext = photo.filename.split(".")[-1]
    filename = f"{reg_no}_{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(IMAGES_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(await photo.read())

    # Create face embedding
    try:
        emb_obj = DeepFace.represent(img_path=save_path, model_name="Facenet")[0]
        embedding_vector = emb_obj["embedding"]  # list of floats
    except Exception as e:
        # if no face / error, delete file and return error
        if os.path.exists(save_path):
            os.remove(save_path)
        return {"status": "error", "message": f"Face not detected or error: {e}"}

    # Store student in DB
    relative_path = os.path.join("static", "images", filename).replace("\\", "/")
    save_student(name, reg_no, department, place, relative_path, embedding_vector)

    return {"status": "ok", "message": "Student added successfully"}


# ---- VERIFY STUDENT (POST) -----------------------------------


@app.post("/verify")
async def verify_student(photo: UploadFile = File(...)):
    # Save the query image temporarily
    ext = photo.filename.split(".")[-1]
    filename = f"verify_{uuid.uuid4().hex}.{ext}"
    query_path = os.path.join(IMAGES_DIR, filename)

    with open(query_path, "wb") as f:
        f.write(await photo.read())

    try:
        query_emb_obj = DeepFace.represent(img_path=query_path, model_name="Facenet")[0]
        query_emb = np.array(query_emb_obj["embedding"])
    except Exception as e:
        if os.path.exists(query_path):
            os.remove(query_path)
        return {"status": "error", "message": f"Face not detected or error: {e}"}

    students = load_all_students()
    if not students:
        return {"status": "error", "message": "No students in database"}

    best_student = None
    best_distance = 1e9

    for st in students:
        stored_emb = np.array(st["embedding"])
        dist = np.linalg.norm(query_emb - stored_emb)
        if dist < best_distance:
            best_distance = dist
            best_student = st

    # You can tune this threshold based on your images
    THRESHOLD = 10.0

    if best_student and best_distance < THRESHOLD:
        return {
            "status": "match",
            "distance": float(best_distance),
            "student": {
                "name": best_student["name"],
                "reg_no": best_student["reg_no"],
                "department": best_student["department"],
                "place": best_student["place"],
                "photo_url": "/" + best_student["photo_path"].replace("\\", "/"),
            },
        }
    else:
        return {
            "status": "no_match",
            "message": "No matching student found. Possible fake ID / not enrolled.",
            "best_distance": float(best_distance),
        }
