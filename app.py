from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from firebase_config import db, bucket
import uuid, os, json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "campusedge_secret_2024"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(role):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session or session.get("role") != role:
                return redirect(url_for(f"{role}_login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ── LANDING ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── TPO ─────────────────────────────────────────────────
@app.route("/tpo/register", methods=["GET", "POST"])
def tpo_register():
    if request.method == "POST":
        data = request.form.to_dict()
        uid = str(uuid.uuid4())
        data["uid"] = uid
        data["role"] = "tpo"
        data["created_at"] = datetime.now().isoformat()
        db.collection("users").document(uid).set(data)
        db.collection("tpo").document(uid).set(data)
        flash("TPO registered successfully!", "success")
        return redirect(url_for("tpo_login"))
    return render_template("tpo_register.html")

@app.route("/tpo/login", methods=["GET", "POST"])
def tpo_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        users = db.collection("tpo").where("email", "==", email).where("password", "==", password).stream()
        user = next(users, None)
        if user:
            d = user.to_dict()
            session["user_id"] = d["uid"]
            session["role"] = "tpo"
            session["name"] = d.get("full_name", "TPO")
            return redirect(url_for("tpo_dashboard"))
        flash("Invalid credentials", "error")
    return render_template("tpo_login.html")

@app.route("/tpo/dashboard")
def tpo_dashboard():
    if session.get("role") != "tpo":
        return redirect(url_for("tpo_login"))
    drives = [d.to_dict() for d in db.collection("placement_drives").stream()]
    students = [s.to_dict() for s in db.collection("students").stream()]
    referrals = [r.to_dict() for r in db.collection("referrals").where("status", "==", "pending").stream()]
    return render_template("tpo_dashboard.html",
        drives=drives, students=students, referrals=referrals,
        total_drives=len(drives), total_students=len(students))

@app.route("/tpo/create_drive", methods=["POST"])
def create_drive():
    if session.get("role") != "tpo":
        return redirect(url_for("tpo_login"))
    data = request.form.to_dict()
    drive_id = str(uuid.uuid4())
    data["drive_id"] = drive_id
    data["created_by"] = session["user_id"]
    data["created_at"] = datetime.now().isoformat()
    data["status"] = "active"
    data["allowed_branches"] = request.form.getlist("allowed_branches")
    db.collection("placement_drives").document(drive_id).set(data)
    # auto-notify eligible students
    students = db.collection("students").stream()
    count = 0
    for s in students:
        sd = s.to_dict()
        try:
            cgpa_ok = float(sd.get("cgpa", 0)) >= float(data.get("min_cgpa", 0))
            backlogs_ok = int(sd.get("backlogs", 99)) <= int(data.get("max_backlogs", 0))
            branch_ok = sd.get("branch", "") in data["allowed_branches"] or "ALL" in data["allowed_branches"]
            if cgpa_ok and backlogs_ok and branch_ok:
                notif = {"uid": str(uuid.uuid4()), "student_id": sd["uid"],
                         "message": f"You are eligible for {data['company_name']} – {data['job_role']}",
                         "drive_id": drive_id, "read": False, "created_at": datetime.now().isoformat()}
                db.collection("notifications").add(notif)
                count += 1
        except: pass
    flash(f"Drive created! {count} students notified.", "success")
    return redirect(url_for("tpo_dashboard"))

@app.route("/tpo/update_application", methods=["POST"])
def update_application():
    if session.get("role") != "tpo":
        return jsonify({"error": "unauthorized"}), 401
    app_id = request.form["app_id"]
    new_status = request.form["status"]
    db.collection("applications").document(app_id).update({"status": new_status, "updated_at": datetime.now().isoformat()})
    return jsonify({"success": True})

@app.route("/tpo/approve_referral", methods=["POST"])
def approve_referral():
    if session.get("role") != "tpo":
        return jsonify({"error": "unauthorized"}), 401
    ref_id = request.form["ref_id"]
    action = request.form["action"]
    db.collection("referrals").document(ref_id).update({"status": action})
    if action == "approved":
        ref = db.collection("referrals").document(ref_id).get().to_dict()
        students = db.collection("students").stream()
        for s in students:
            sd = s.to_dict()
            notif = {"uid": str(uuid.uuid4()), "student_id": sd["uid"],
                     "message": f"New referral opportunity: {ref.get('job_title')} at {ref.get('company')}",
                     "read": False, "created_at": datetime.now().isoformat()}
            db.collection("notifications").add(notif)
    return jsonify({"success": True})

# ── STUDENT ─────────────────────────────────────────────
@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        data = request.form.to_dict()
        uid = str(uuid.uuid4())
        data["uid"] = uid
        data["role"] = "student"
        data["skills"] = request.form.get("skills", "").split(",")
        data["created_at"] = datetime.now().isoformat()
        if "resume" in request.files:
            file = request.files["resume"]
            if file and allowed_file(file.filename):
                fname = secure_filename(f"{uid}_{file.filename}")
                fpath = os.path.join(UPLOAD_FOLDER, fname)
                file.save(fpath)
                data["resume_path"] = fpath
        db.collection("users").document(uid).set(data)
        db.collection("students").document(uid).set(data)
        flash("Student registered successfully!", "success")
        return redirect(url_for("student_login"))
    return render_template("student_register.html")

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        users = db.collection("students").where("email", "==", email).where("password", "==", password).stream()
        user = next(users, None)
        if user:
            d = user.to_dict()
            session["user_id"] = d["uid"]
            session["role"] = "student"
            session["name"] = d.get("full_name", "Student")
            return redirect(url_for("student_dashboard"))
        flash("Invalid credentials", "error")
    return render_template("student_login.html")

@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("student_login"))
    uid = session["user_id"]
    profile = db.collection("students").document(uid).get().to_dict() or {}
    drives = [d.to_dict() for d in db.collection("placement_drives").where("status", "==", "active").stream()]
    applications = [a.to_dict() for a in db.collection("applications").where("student_id", "==", uid).stream()]
    notifs = [n.to_dict() for n in db.collection("notifications").where("student_id", "==", uid).stream()]
    sessions_ref = [s.to_dict() for s in db.collection("mentorship_sessions").stream()]
    applied_drives = {a["drive_id"] for a in applications}
    return render_template("student_dashboard.html",
        profile=profile, drives=drives, applications=applications,
        notifications=notifs, mentorship_sessions=sessions_ref,
        applied_drives=applied_drives)

@app.route("/student/apply", methods=["POST"])
def student_apply():
    if session.get("role") != "student":
        return jsonify({"error": "unauthorized"}), 401
    drive_id = request.form["drive_id"]
    uid = session["user_id"]
    existing = list(db.collection("applications").where("student_id", "==", uid).where("drive_id", "==", drive_id).stream())
    if existing:
        return jsonify({"error": "Already applied"})
    app_id = str(uuid.uuid4())
    data = {"app_id": app_id, "student_id": uid, "drive_id": drive_id,
            "status": "Applied", "applied_at": datetime.now().isoformat()}
    db.collection("applications").document(app_id).set(data)
    return jsonify({"success": True, "app_id": app_id})

@app.route("/student/analyze_resume", methods=["POST"])
def analyze_resume():
    if session.get("role") != "student":
        return jsonify({"error": "unauthorized"}), 401
    # Mock AI response — replace with real OpenAI call
    result = {
        "score": 78,
        "technical_skills": 85,
        "project_relevance": 65,
        "communication": 72,
        "missing_skills": ["System Design", "Docker", "Kubernetes", "CI/CD"],
        "existing_skills": ["Python", "React", "SQL", "Git"],
        "suggestions": [
            "Add quantified achievements to each project",
            "Include a GitHub profile link",
            "Expand project descriptions with tech stack used",
            "Add relevant certifications section"
        ]
    }
    return jsonify(result)

# ── ALUMNI ─────────────────────────────────────────────
@app.route("/alumni/register", methods=["GET", "POST"])
def alumni_register():
    if request.method == "POST":
        data = request.form.to_dict()
        uid = str(uuid.uuid4())
        data["uid"] = uid
        data["role"] = "alumni"
        data["created_at"] = datetime.now().isoformat()
        db.collection("users").document(uid).set(data)
        db.collection("alumni").document(uid).set(data)
        flash("Alumni registered successfully!", "success")
        return redirect(url_for("alumni_login"))
    return render_template("alumni_register.html")

@app.route("/alumni/login", methods=["GET", "POST"])
def alumni_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        users = db.collection("alumni").where("email", "==", email).where("password", "==", password).stream()
        user = next(users, None)
        if user:
            d = user.to_dict()
            session["user_id"] = d["uid"]
            session["role"] = "alumni"
            session["name"] = d.get("full_name", "Alumni")
            return redirect(url_for("alumni_dashboard"))
        flash("Invalid credentials", "error")
    return render_template("alumni_login.html")

@app.route("/alumni/dashboard")
def alumni_dashboard():
    if session.get("role") != "alumni":
        return redirect(url_for("alumni_login"))
    uid = session["user_id"]
    profile = db.collection("alumni").document(uid).get().to_dict() or {}
    referrals = [r.to_dict() for r in db.collection("referrals").where("alumni_id", "==", uid).stream()]
    sessions_ref = [s.to_dict() for s in db.collection("mentorship_sessions").where("alumni_id", "==", uid).stream()]
    return render_template("alumni_dashboard.html",
        profile=profile, referrals=referrals, mentorship_sessions=sessions_ref)

@app.route("/alumni/submit_referral", methods=["POST"])
def submit_referral():
    if session.get("role") != "alumni":
        return jsonify({"error": "unauthorized"}), 401
    data = request.form.to_dict()
    ref_id = str(uuid.uuid4())
    data["ref_id"] = ref_id
    data["alumni_id"] = session["user_id"]
    data["alumni_name"] = session["name"]
    data["status"] = "pending"
    data["created_at"] = datetime.now().isoformat()
    db.collection("referrals").document(ref_id).set(data)
    return jsonify({"success": True})

@app.route("/alumni/create_session", methods=["POST"])
def create_session():
    if session.get("role") != "alumni":
        return jsonify({"error": "unauthorized"}), 401
    data = request.form.to_dict()
    sess_id = str(uuid.uuid4())
    data["session_id"] = sess_id
    data["alumni_id"] = session["user_id"]
    data["alumni_name"] = session["name"]
    data["status"] = "available"
    data["created_at"] = datetime.now().isoformat()
    db.collection("mentorship_sessions").document(sess_id).set(data)
    return jsonify({"success": True})

@app.route("/student/book_session", methods=["POST"])
def book_session():
    if session.get("role") != "student":
        return jsonify({"error": "unauthorized"}), 401
    sess_id = request.form["session_id"]
    db.collection("mentorship_sessions").document(sess_id).update({
        "student_id": session["user_id"],
        "student_name": session["name"],
        "status": "booked"
    })
    return jsonify({"success": True})

# ── MARKET INTELLIGENCE ─────────────────────────────────
@app.route("/market")
def market_intelligence():
    drives = [d.to_dict() for d in db.collection("placement_drives").stream()]
    applications = [a.to_dict() for a in db.collection("applications").stream()]
    return render_template("market_intelligence.html", drives=drives, applications=applications)

# ── ADMIN ─────────────────────────────────────────────
@app.route("/admin")
def admin_dashboard():
    students = list(db.collection("students").stream())
    companies = list(db.collection("placement_drives").stream())
    applications = list(db.collection("applications").stream())
    alumni_list = list(db.collection("alumni").stream())
    placed = [a for a in applications if a.to_dict().get("status") == "Selected"]
    placement_pct = round(len(placed) / len(students) * 100) if students else 0
    return render_template("admin_dashboard.html",
        total_students=len(students),
        total_drives=len(companies),
        total_alumni=len(alumni_list),
        total_applications=len(applications),
        placement_pct=placement_pct,
        applications=[a.to_dict() for a in applications])

# ── LOGOUT ─────────────────────────────────────────────
@app.route("/logout")
def logout():
    role = session.get("role", "")
    session.clear()
    if role == "tpo": return redirect(url_for("tpo_login"))
    if role == "student": return redirect(url_for("student_login"))
    if role == "alumni": return redirect(url_for("alumni_login"))
    return redirect(url_for("index"))

# ── API: NOTIFICATIONS ──────────────────────────────────
@app.route("/api/notifications")
def get_notifications():
    if "user_id" not in session:
        return jsonify([])
    notifs = [n.to_dict() for n in db.collection("notifications").where("student_id", "==", session["user_id"]).stream()]
    return jsonify(notifs)


@app.route("/api/notifications/mark_read", methods=["POST"])
def mark_notifications_read():
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401
    notifs = db.collection("notifications").where("student_id", "==", session["user_id"]).stream()
    for n in notifs:
        n.reference.update({"read": True})
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
