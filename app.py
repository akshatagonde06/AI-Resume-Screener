import os
from functools import wraps
import docx
import pypdf
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-change-this")


# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def extract_text_from_file(file) -> str:
    """Extract text from uploaded PDF, DOCX, or TXT file."""
    if not file or file.filename == "":
        return ""

    filename = file.filename.lower()
    text = ""

    try:
        if filename.endswith(".pdf"):
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        elif filename.endswith(".docx"):
            doc = docx.Document(file)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        elif filename.endswith(".txt"):
            text = file.read().decode("utf-8")
    except Exception as e:
        print(f"Error reading file: {e}")

    return text.strip()


# --- ROUTES ---


@app.route("/")
@login_required
def home():
    """Home Dashboard Page (Protected)"""
    return render_template("index.html", user=session.get("user"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login Page Route - Accepts ANY Username & Password"""
    if "user" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Check if both fields are filled in
        if username and password:
            session["user"] = username
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Please enter both a username and password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout Action Route"""
    session.pop("user", None)
    return render_template("logout.html")


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    """CrewAI Analysis Endpoint (Protected)"""
    resume_text = request.form.get("resume_text", "")
    if "resume_file" in request.files:
        resume_text = extract_text_from_file(request.files["resume_file"])

    jd_text = request.form.get("jd_text", "")
    if "jd_file" in request.files:
        jd_text = extract_text_from_file(request.files["jd_file"])

    if not resume_text or not jd_text:
        return (
            jsonify({"error": "Both Resume and Job Description are required."}),
            400,
        )

    # Simulated CrewAI Response
    result = {
        "score": 85,
        "matched_skills": [
            "Python",
            "Machine Learning",
            "SQL",
            "REST APIs",
            "Pandas",
        ],
        "missing_skills": ["Docker", "Git", "Kubernetes", "AWS"],
        "strengths": [
            "Strong foundation in Python development.",
            "Experience deploying ML models.",
        ],
        "weaknesses": [
            "Missing explicit containerization experience (Docker/Kubernetes).",
            "No Git workflows mentioned.",
        ],
        "verdict_type": "Strong",
        "verdict_msg": "✅ Strong — Candidate shows strong technical alignment.",
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)