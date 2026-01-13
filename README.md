# PDF-Centric CBT Engine

A Django-based Computer-Based Testing (CBT) Engine designed to conduct exams using uploaded PDF question papers and CSV answer keys.

## Features
- **PDF-Centric:** Upload a PDF and an Answer Key CSV to create an exam.
- **Split-Screen UI:** View the PDF on the left and the Question Palette/Inputs on the right.
- **Scientific Calculator:** Built-in virtual scientific calculator.
- **Scoring:** Supports MCQ, MSQ, and NAT question types with negative marking.
- **Persistence:** Saves attempt history and allows resuming exams.

## Prerequisites
- Python 3.8+
- PostgreSQL (optional, defaults to SQLite for local dev)

## Local Setup

1. **Install Dependencies**
   ```bash
   pip install django psycopg2-binary img2pdf
   ```

2. **Apply Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create Admin User**
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Server**
   ```bash
   python manage.py runserver
   ```
   Access the app at `http://127.0.0.1:8000`.

## Docker Setup

1. **Build and Run**
   ```bash
   cd pdf2CBT
   docker-compose up --build
   ```
   *Note: Ensure the `Dockerfile` is present in the `pdf2CBT` directory or adjust the `docker-compose.yml` build path.*

## Usage

1. Go to the Admin panel (`/admin/`) and log in.
2. Create an **Exam**:
   - Upload the Question Paper (PDF).
   - Upload the Answer Key (CSV).
   - Set duration.
3. The system will automatically parse the CSV and create Questions.
4. Go to the home page (`/`) to see available exams and start an attempt.

### Answer Key CSV Format
```csv
Section, Question No, Type, Key, Marks, Negative
Aptitude, 1, MCQ, A, 1, 0.33
Core, 2, MSQ, A;B, 2, 0
Core, 3, NAT, 5.1:5.3, 2, 0
```
- **Type:** MCQ (Multiple Choice), MSQ (Multiple Select), NAT (Numerical).
- **Key:**
  - MCQ: Single option (e.g., "A").
  - MSQ: Comma or Semicolon separated (e.g., "A,B").
  - NAT: Range (min:max) or Exact Value.
