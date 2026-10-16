from datetime import date, datetime
from urllib.parse import urlparse

from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from database import (
    APPLICATION_STATUSES,
    TRASH_RETENTION_DAYS,
    add_application,
    cleanup_expired_trash,
    delete_application,
    get_all_applications,
    get_application_by_id,
    get_dashboard_stats,
    get_trashed_applications,
    initialize_database,
    permanently_delete_application,
    restore_application,
    update_application,
)

app = Flask(__name__)
app.secret_key = "job-application-tracker-local-secret-key"

JOB_TYPES = (
    "Full-time",
    "Internship",
    "Part-time",
    "Contract",
    "Remote",
)


def valid_date(value, required=False):
    if not value:
        return not required

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def valid_url(value):
    if not value:
        return True

    try:
        parsed = urlparse(value)
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
            and not any(char.isspace() for char in value)
        )
    except ValueError:
        return False


def read_application_form():
    data = {
        "company": request.form.get("company", "").strip(),
        "role": request.form.get("role", "").strip(),
        "location": request.form.get("location", "").strip(),
        "job_type": request.form.get("job_type", "").strip(),
        "application_date": request.form.get(
            "application_date", ""
        ).strip(),
        "status": request.form.get("status", "").strip(),
        "interview_date": request.form.get(
            "interview_date", ""
        ).strip(),
        "job_url": request.form.get("job_url", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }

    if not data["company"] or not data["role"]:
        return None, "Company and job role are required."

    if data["job_type"] not in JOB_TYPES:
        return None, "Select a valid job type."

    if data["status"] not in APPLICATION_STATUSES:
        return None, "Select a valid application status."

    if not valid_date(data["application_date"], required=True):
        return None, "Enter a valid application date."

    if not valid_date(data["interview_date"]):
        return None, "Enter a valid interview date."

    if not valid_url(data["job_url"]):
        return None, "Job URL must begin with http:// or https://."

    return data, None


def render_application_form(template, application=None):
    return render_template(
        template,
        application=application,
        statuses=APPLICATION_STATUSES,
        job_types=JOB_TYPES,
        today=date.today().isoformat(),
    )


@app.route("/")
def index():
    stats = get_dashboard_stats()
    applications = get_all_applications()

    return render_template(
        "index.html",
        stats=stats,
        applications=applications[:5],
    )


@app.route("/applications", methods=["GET", "POST"])
def applications():
    if request.method == "POST":
        data, error = read_application_form()

        if error:
            flash(error, "error")
            return redirect(url_for("applications"))

        try:
            add_application(**data)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("applications"))

        flash("Application added successfully.", "success")
        return redirect(url_for("applications"))

    search_text = request.args.get("search", "").strip()
    selected_status = request.args.get("status", "").strip()
    selected_job_type = request.args.get("job_type", "").strip()

    if selected_status not in APPLICATION_STATUSES:
        selected_status = ""

    if selected_job_type not in JOB_TYPES:
        selected_job_type = ""

    application_list = get_all_applications(
        search=search_text,
        status=selected_status,
        job_type=selected_job_type,
    )

    return render_template(
        "applications.html",
        applications=application_list,
        statuses=APPLICATION_STATUSES,
        job_types=JOB_TYPES,
        search_text=search_text,
        selected_status=selected_status,
        selected_job_type=selected_job_type,
        today=date.today().isoformat(),
    )


@app.route(
    "/applications/edit/<int:application_id>",
    methods=["GET", "POST"],
)
def edit_application(application_id):
    application = get_application_by_id(application_id)

    if application is None:
        flash("Application not found.", "error")
        return redirect(url_for("applications"))

    if request.method == "POST":
        data, error = read_application_form()

        if error:
            flash(error, "error")
            return redirect(
                url_for(
                    "edit_application",
                    application_id=application_id,
                )
            )

        try:
            updated = update_application(application_id, **data)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(
                url_for(
                    "edit_application",
                    application_id=application_id,
                )
            )

        if updated:
            flash("Application updated successfully.", "success")
        else:
            flash("No changes were saved.", "error")

        return redirect(url_for("applications"))

    return render_application_form(
        "edit_application.html",
        application=application,
    )


@app.route(
    "/applications/delete/<int:application_id>",
    methods=["POST"],
)
def remove_application(application_id):
    # This is now a soft delete: the record enters the Recycle Bin.
    deleted = delete_application(application_id)

    if deleted:
        flash(
            "Application moved to the Recycle Bin. "
            "It will be permanently deleted after 15 days.",
            "success",
        )
    else:
        flash("Application not found.", "error")

    return redirect(url_for("applications"))


@app.route("/recycle-bin")
def recycle_bin():
    # Remove expired records whenever the Recycle Bin is opened.
    cleanup_expired_trash()
    trashed_applications = get_trashed_applications()

    return render_template(
        "recycle_bin.html",
        applications=trashed_applications,
        retention_days=TRASH_RETENTION_DAYS,
    )


@app.route(
    "/recycle-bin/restore/<int:application_id>",
    methods=["POST"],
)
def restore_trashed_application(application_id):
    restored = restore_application(application_id)

    if restored:
        flash("Application restored successfully.", "success")
    else:
        flash(
            "Application could not be restored. "
            "It may have expired or already been removed.",
            "error",
        )

    return redirect(url_for("recycle_bin"))


@app.route(
    "/recycle-bin/delete/<int:application_id>",
    methods=["POST"],
)
def permanently_delete_trashed_application(application_id):
    deleted = permanently_delete_application(application_id)

    if deleted:
        flash(
            "Application permanently deleted. This cannot be undone.",
            "success",
        )
    else:
        flash(
            "Application not found in the Recycle Bin.",
            "error",
        )

    return redirect(url_for("recycle_bin"))


@app.route("/export/csv")
def export_csv():
    import csv
    import io

    application_list = get_all_applications(
        search=request.args.get("search", "").strip(),
        status=request.args.get("status", "").strip(),
        job_type=request.args.get("job_type", "").strip(),
    )

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Company",
        "Role",
        "Location",
        "Job Type",
        "Application Date",
        "Status",
        "Interview Date",
        "Job URL",
        "Notes",
        "Created At",
        "Updated At",
    ])

    for item in application_list:
        writer.writerow([
            item["id"],
            item["company"],
            item["role"],
            item["location"],
            item["job_type"],
            item["application_date"],
            item["status"],
            item["interview_date"],
            item["job_url"],
            item["notes"],
            item["created_at"],
            item["updated_at"],
        ])

    response = Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=job_applications.csv"
    )

    return response


# Create or migrate the database before serving requests.
initialize_database()


if __name__ == "__main__":
    app.run(debug=True)
