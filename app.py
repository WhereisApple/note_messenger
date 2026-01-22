import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ["DATABASE_URL"]
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]

engine = create_engine(DATABASE_URL)

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/notes", methods=["POST"])
def create_note():
    text_value = request.json.get("text")
    if not text_value:
        return jsonify({"error": "Text required"}), 400

    otp = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=5)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO notes (otp, encrypted_text, expires_at)
            VALUES (:otp, pgp_sym_encrypt(:text_value, :key), :expires)
        """), {"otp": otp, "text_value": text_value, "key": ENCRYPTION_KEY, "expires": expires})

    return jsonify({"otp": otp, "expires_in": "5 minutes"}), 201

@app.route("/api/notes/retrieve", methods=["POST"])
def retrieve_note():
    otp = request.json.get("otp")

    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT id, pgp_sym_decrypt(encrypted_text, :key) AS decrypted_text, expires_at
            FROM notes WHERE otp = :otp
        """), {"otp": otp, "key": ENCRYPTION_KEY}).fetchone()

        if not row:
            return jsonify({"error": "Invalid OTP"}), 404

        if datetime.utcnow() > row.expires_at:
            conn.execute(text("DELETE FROM notes WHERE id = :id"), {"id": row.id})
            return jsonify({"error": "OTP expired"}), 410
            
        conn.execute(text("DELETE FROM notes WHERE id = :id"), {"id": row.id})

    return jsonify({"text": row.decrypted_text}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
