#  Face-Based Student Verification for Sathyabama ERP (Demo)

A lightweight **face verification system** that helps college staff verify whether a student is genuine or using a **fake ID**, by matching a face photo with registered student records.

>  **Use case:** Security / admin uploads a student's face photo → the system finds the closest match from the database and returns **Name, Register Number, Department, Place, and Photo**.

This is a **demo project** built as a proof-of-concept for integrating **face identity** into a university ERP (specifically inspired by **Sathyabama Institute of Science and Technology**).

---

##  Features

-  **Student registration with face photo**
  - Admin adds student profile with: Name, Register No, Department, Place, Photo.
  - Automatically extracts and stores a **face embedding** for fast matching.

-  **Face-based verification**
  - Upload a face image.
  - System finds the **most similar registered student**.
  - Shows student details if match is above a similarity threshold.
  - Otherwise flags: **“Possible fake ID / student not found.”**

-  **Fast and simple demo**
  - Uses precomputed embeddings for quick comparison.
  - Built with **FastAPI** and **SQLite** – no heavy setup.
  - Suitable for **projects, demos, resumes, and LinkedIn posts**.

-  **Web interface**
  - Minimal UI with:
    - `/add-student` → add student record
    - `/verify` → verify a student by face

---

##  Tech Stack

- **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Face Recognition:** [DeepFace](https://github.com/serengil/deepface) (Facenet model)
- **Database:** SQLite (file-based, `students.db`)
- **Language:** Python 3
- **Web Server:** Uvicorn
- **Static Storage:** Local filesystem (`static/images`)

---

##  Project Architecture

**High-level flow:**

1. **Register Student**
   - Admin fills a form with student details + uploads a face image.
   - Backend:
     - Saves the image into `static/images/`.
     - Uses DeepFace (Facenet) to generate a **face embedding** (vector).
     - Saves student data + embedding in `students.db`.

2. **Verify Student**
   - Staff uploads a face image of the student standing at gate/office.
   - Backend:
     - Generates embedding for the uploaded face.
     - Compares it with embeddings of all registered students.
     - Finds the **closest match** using Euclidean distance.
     - If distance < threshold → returns student details.
     - Else → returns **no match / possible fake ID**.

---

## Project Structure

```bash
.
├── main.py             # FastAPI app - routes, DB logic, face verification
├── students.db         # SQLite database 
├── static/
│   └── images/         # Stored student & verification photos
└── README.md           # Project documentation
---

##  Output Demonstration

### Home Page
![Home](screenshots/home_page.png)

### Add Student Page
![Add Student](screenshots/add_student.png)

### Verification Result
![Verify](screenshots/verify_match.png)
