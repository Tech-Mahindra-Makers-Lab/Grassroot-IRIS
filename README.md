# Grassroot IRIS

Grassroot IRIS is a Django-based innovation management platform designed to facilitate the collection, evaluation, and tracking of ideas and challenges within an organization. It features a robust workflow for Challenge Owners, Reporting Managers (RM), and IBU Heads to manage the innovation pipeline.

## Key Features

- **Challenge Management:** Post new challenges with specific review parameters and timelines.
- **Idea Submission:** Users can submit ideas against specific challenges or as general "Grassroot" ideas.
- **Workflow Automation:** Multi-stage approval process involving RMs and IBU Heads.
- **Notification System:** Real-time-ish notifications for status changes and required actions.
- **Reporting & Dashboards:** Specialized dashboards for different user roles (Ideator, RM, IBU Head).
- **Oracle DB Integration:** Built to work with legacy Oracle databases for enterprise data management.

## Tech Stack

- **Backend:** Python / Django 5.2.9
- **API:** Django REST Framework
- **Database:** Oracle DB (configured for `localhost:1521/orcl`)
- **Frontend:** Django Templates with CSS/Vanilla JS
- **Integration:** `django-import-export` for data handling

## Setup and Installation

### Prerequisites

- Python 3.10+
- Oracle Instant Client (required for `oracledb`)
- Access to an Oracle Database instance

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Grassrootinivation/grassroot_iris
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # On Windows
    # source venv/bin/activate  # On Linux/Mac
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Configuration:**
    Ensure your database settings in `grassroot_iris/settings.py` are correct. By default, it looks for:
    - Host: `localhost`
    - Port: `1521`
    - Service: `orcl`
    - User/Pass: `****` / `****`

5.  **Run Migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a Superuser:**
    ```bash
    python manage.py createsuperuser
    ```

## Running the Application

Start the development server:
```bash
python manage.py runserver
```
The application will be available at `http://127.0.0.1:8000/`.

## Project Structure

- `grassroot_iris/`: Project configuration and settings.
- `iris_app/`: Main application containing models, views, and templates.
    - `templates/`: HTML templates for the UI.
    - `api_urls.py`: API endpoint definitions.
- `media/`: Uploaded files (challenge icons, documents).
- `requirements.txt`: Python package dependencies.
- `manage.py`: Django management utility.
