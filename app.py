"""
ForensicAI — Flask Backend
Complete rewrite from Streamlit to Flask REST API.
Phases 1–4: Flask refactor, USP modules, MongoDB history.
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import numpy as np
from keras.models import load_model
from PIL import Image
from PIL.ExifTags import TAGS
import io, base64, os, cv2
from datetime import datetime

from helper import prepare_image_for_ela
from noise_module import compute_noise_map
from edge_module import compute_edge_map
from score_fuser import fuse_scores
from copy_move_module import detect_copy_move
from gradcam_module import compute_gradcam
from report_generator import generate_report

# ── MongoDB (optional — gracefully skip if not running) ────────────────────────
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MONGO_URI = os.environ.get("MONGO_URI")

# Mask password for printing
if MONGO_URI:
    try:
        start = MONGO_URI.find("://") + 3
        end = MONGO_URI.find("@")
        if start > 2 and end > start:
            credentials = MONGO_URI[start:end]
            if ":" in credentials:
                user, password = credentials.split(":")
                masked_uri = MONGO_URI.replace(f":{password}@", f":*****@")
            else:
                masked_uri = MONGO_URI
        else:
            masked_uri = MONGO_URI
    except Exception:
        masked_uri = "<masking-failed>"
else:
    masked_uri = None

print(f"[ForensicAI] Startup: MONGO_URI loaded: {masked_uri}")

try:
    from pymongo import MongoClient
    import certifi
    ca = certifi.where()
    
    uri = MONGO_URI or "mongodb+srv://samarthburkul67_db_user:N4J8vQiYjHcGFsuT@cluster0.rld51zf.mongodb.net/forensicai?retryWrites=true&w=majority&appName=Cluster0"
    _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
    _mongo_client.server_info()  # force connection check
    _db = _mongo_client["forensicai"]
    _analyses = _db["analyses"]
    MONGO_AVAILABLE = True
    print("[ForensicAI] MongoDB connected.")
except Exception as _e:
    MONGO_AVAILABLE = False
    _analyses = None
    print(f"[ForensicAI] MongoDB unavailable ({_e}). History disabled.")


# ── App / CORS ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ── Model — loaded ONCE at startup, cached globally ───────────────────────────
_ELA_MODEL = None

def get_model():
    global _ELA_MODEL
    if _ELA_MODEL is None:
        print("[ForensicAI] Loading DenseNet ELA model …")
        _ELA_MODEL = load_model("ELA_Training/model_ela.h5")
        print("[ForensicAI] Model ready.")
    return _ELA_MODEL

CLASS_ELA = ["Real", "Tampered"]
TEMP_PATH  = "temp.jpg"

# ── Utilities ──────────────────────────────────────────────────────────────────
def pil_to_b64(pil_image, fmt="JPEG"):
    buf = io.BytesIO()
    pil_image.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def save_upload(file_storage):
    data = file_storage.read()
    with open(TEMP_PATH, "wb") as f:
        f.write(data)

def predict_ela(temp_path):
    """Return (tampered_prob, ela_pil_image, preprocessed_np_img)."""
    np_img, ela_pil = prepare_image_for_ela(temp_path)
    model = get_model()
    preds = model.predict(np_img, verbose=0)
    tampered_prob = float(preds[0][1])
    return tampered_prob, ela_pil, np_img

def draw_tampered_bbox(orig_pil, ela_pil):
    """
    Threshold the ELA heatmap at the 90th percentile, find the largest
    contour, and draw a red bounding box on a COPY of the original image.
    Returns base64-encoded JPEG string (or None if no contour found).
    """
    ela_gray = np.array(ela_pil.convert("L"))

    # Use the 90th percentile as a dynamic threshold
    p90 = np.percentile(ela_gray, 90)
    _, thresh = cv2.threshold(ela_gray, int(p90), 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 500:          # ignore tiny noise spots
        return None

    x, y, w, h = cv2.boundingRect(largest)
    # Draw on a COPY of the original — never mutate the source
    orig_bgr = cv2.cvtColor(np.array(orig_pil.convert("RGB").copy()), cv2.COLOR_RGB2BGR)
    cv2.rectangle(orig_bgr, (x, y), (x + w, y + h), (0, 0, 255), 3)
    cv2.putText(orig_bgr, "Suspected Region", (x, max(y - 10, 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    _, buf = cv2.imencode(".jpg", orig_bgr)
    return base64.b64encode(buf).decode("utf-8")

def extract_exif(pil_image):
    """Return a dict of readable EXIF tags (strings only)."""
    exif_data = {}
    try:
        raw = pil_image._getexif()
        if raw:
            for tag_id, value in raw.items():
                tag = TAGS.get(tag_id, str(tag_id))
                if isinstance(value, (str, int, float, bytes)):
                    exif_data[tag] = str(value) if not isinstance(value, str) else value
    except Exception:
        pass
    return exif_data

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mongo": MONGO_AVAILABLE})


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Lightweight endpoint — ELA only.
    Accepts: multipart/form-data with field 'image'
    Returns: { ela_confidence, prediction, ela_image_base64 }
    """
    if "image" not in request.files:
        return jsonify({"error": "No image field in request"}), 400

    save_upload(request.files["image"])

    tampered_prob, ela_pil, _ = predict_ela(TEMP_PATH)
    prediction = "Tampered" if tampered_prob > 0.35 else "Real"

    return jsonify({
        "ela_confidence":  round(tampered_prob, 4),
        "prediction":      prediction,
        "ela_image_base64": pil_to_b64(ela_pil),
    })


@app.route("/analyze/full", methods=["POST"])
def analyze_full():
    """
    Full forensic pipeline — ELA + Noise + Edge + Score fusion.
    Accepts: multipart/form-data with field 'image'
    Returns: full JSON with all maps, scores, verdict, bounding box.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image field in request"}), 400

    file     = request.files["image"]
    filename = file.filename or "upload.jpg"
    save_upload(file)

    pil_orig = Image.open(TEMP_PATH).convert("RGB")

    # Detect JPEG format for artifact correction
    ext = os.path.splitext(filename)[1].lower()
    is_jpeg = ext in (".jpg", ".jpeg") or pil_orig.format == "JPEG"

    # 1 — ELA
    tampered_prob, ela_pil, np_img = predict_ela(TEMP_PATH)

    # 2 — Grad-CAM
    try:
        gradcam_b64 = compute_gradcam(get_model(), np_img, ela_pil)
    except Exception as gc_err:
        print(f"[ForensicAI] Grad-CAM failed: {gc_err}")
        gradcam_b64 = None

    # 3 — Noise map
    noise_b64, noise_score = compute_noise_map(pil_orig)

    # 4 — Edge map
    edge_b64, edge_score = compute_edge_map(pil_orig)

    # 5 — Fuse (with JPEG artifact correction)
    unified_score, verdict = fuse_scores(tampered_prob, noise_score, edge_score, is_jpeg=is_jpeg)

    # 6 — Bounding box (always attempt — shows suspected region if contour is large enough)
    annotated_b64 = draw_tampered_bbox(pil_orig, ela_pil)

    # 7 — Copy-Move detection (SIFT-based)
    copy_move = detect_copy_move(pil_orig)

    # 8 — EXIF
    exif_data = extract_exif(pil_orig)

    # 9 — Persist to MongoDB (include image base64 for PDF report)
    analysis_id = None
    if MONGO_AVAILABLE:
        try:
            doc = {
                "filename":       filename,
                "timestamp":      datetime.utcnow(),
                "ela_confidence": tampered_prob,
                "noise_score":    noise_score,
                "edge_score":     edge_score,
                "unified_score":  unified_score,
                "verdict":        verdict,
                "copy_move_detected": copy_move.get("copy_move_detected", False),
                "exif":           exif_data,
                "original_image_base64": pil_to_b64(pil_orig),
                "ela_image_base64":      pil_to_b64(ela_pil),
            }
            result = _analyses.insert_one(doc)
            analysis_id = str(result.inserted_id)
        except Exception as db_err:
            print(f"[ForensicAI] MongoDB insert failed: {db_err}")

    return jsonify({
        # Scores
        "ela_confidence":  round(tampered_prob, 4),
        "noise_score":     round(noise_score, 4),
        "edge_score":      round(edge_score, 4),
        "unified_score":   unified_score,
        "verdict":         verdict,
        # Images (base64 JPEG)
        "original_image_base64":  pil_to_b64(pil_orig),
        "ela_image_base64":       pil_to_b64(ela_pil),
        "gradcam_base64":         gradcam_b64,
        "noise_image_base64":     noise_b64,
        "edge_image_base64":      edge_b64,
        "annotated_image_base64": annotated_b64,
        # Copy-Move
        "copy_move":       copy_move,
        # Metadata
        "exif":           exif_data,
        "filename":       filename,
        "analysis_id":    analysis_id,
    })


@app.route("/history", methods=["GET"])
def history():
    """Return the last 20 analysis records from MongoDB."""
    try:
        from pymongo import MongoClient
        import certifi
        import os
        
        ca = certifi.where()
        uri = os.environ.get("MONGO_URI") or "mongodb+srv://samarthburkul67_db_user:N4J8vQiYjHcGFsuT@cluster0.rld51zf.mongodb.net/forensicai?retryWrites=true&w=majority&appName=Cluster0"
        
        # Connect strictly to return the error if it fails
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
        client.server_info() # force connection check
        db = client["forensicai"]
        analyses = db["analyses"]

        records = list(analyses.find().sort("timestamp", -1).limit(20))
        for r in records:
            r["_id"] = str(r["_id"])
            if isinstance(r.get("timestamp"), datetime):
                r["timestamp"] = r["timestamp"].isoformat() + "Z"
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/report/<analysis_id>", methods=["GET"])
def report(analysis_id):
    """Generate and stream a PDF report for a given analysis ID."""
    try:
        from bson.objectid import ObjectId
        from pymongo import MongoClient
        import certifi

        ca = certifi.where()
        uri = os.environ.get("MONGO_URI") or "mongodb+srv://samarthburkul67_db_user:N4J8vQiYjHcGFsuT@cluster0.rld51zf.mongodb.net/forensicai?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
        db = client["forensicai"]
        analyses = db["analyses"]

        doc = analyses.find_one({"_id": ObjectId(analysis_id)})
        if not doc:
            return jsonify({"error": "Analysis not found"}), 404

        pdf_bytes = generate_report(doc)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="ForensicAI_Report_{analysis_id}.pdf"'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Startup ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    get_model()          # warm-up: load model before serving any request
    app.run(host="0.0.0.0", port=5005, debug=False)
