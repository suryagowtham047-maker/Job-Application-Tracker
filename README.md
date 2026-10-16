
# Job Application Tracker

A web-based application built with Python, Flask, and SQLite to help job seekers organize, monitor, and manage their job applications from one place.

## Features

- **Dashboard:** View application statistics and track your job search progress.
- **Add Applications:** Record company names, job roles, application dates, statuses, and interview dates.
- **Edit Applications:** Update application details whenever needed.
- **Search and Filter:** Find applications and filter them by status.
- **CSV Export:** Export active application records for reporting and analysis.
- **Recycle Bin:** Move deleted applications to the Recycle Bin instead of deleting them immediately.
- **Restore Applications:** Recover applications from the Recycle Bin.
- **Permanent Deletion:** Permanently remove unwanted applications when necessary.
- **Automatic Cleanup:** Applications in the Recycle Bin are automatically removed after 15 days.
- **SQLite Database:** Store application records locally.
- **Responsive Interface:** Use a dark-themed interface designed for a clean, organized experience.

## Technologies Used

- Python
- Flask
- SQLite
- HTML5
- CSS3

## Project Structure

```text
Job-Application-Tracker/
├── app.py
├── database.py
├── requirements.txt
├── .gitignore
├── README.md
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── applications.html
    ├── edit_application.html
    └── recycle_bin.html
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/suryagowtham047-maker/Job-Application-Tracker.git
cd Job-Application-Tracker
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

### 6. Open in Your Browser

Visit:

http://127.0.0.1:5000

## Database and Privacy

The application uses a local SQLite database to store job application records. The database file is excluded from Git using `.gitignore`, so your personal application records are not included in the repository.

When you clone the project, the application initializes its database automatically.

## Future Improvements

- User authentication and individual accounts
- Application deadline reminders
- Charts showing application trends
- Interview preparation notes
- Deployment to a cloud hosting platform

## Author

**Surya Gowtham**

GitHub: [@suryagowtham047-maker](https://github.com/suryagowtham047-maker)

---

If you find this project useful, consider giving the repository a star!
