import os
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

fernet = Fernet(os.environ["FERNET_KEY"].encode())

def get_db():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require"
    )


def generate_otp():
    return str(random.randint(100000, 999999))

def encrypt(text):
    return fernet.encrypt(text.encode()).decode()

def decrypt(token):
    return fernet.decrypt(token.encode()).decode()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/notes", methods=["POST"])
def create_note():
    text = request.json.get("text")
    if not text:
        return jsonify({"error": "Text required"}), 400

    otp = generate_otp()
    encrypted = encrypt(text)
    expires = datetime.utcnow() + timedelta(minutes=5)

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO notes (otp, encrypted_text, expires_at)
        VALUES (%s, %s, %s)
    """, (otp, encrypted, expires))
    db.commit()
    cur.close()
    db.close()

    return jsonify({"otp": otp, "expires_in": "5 minutes"}), 201

@app.route("/api/notes/retrieve", methods=["POST"])
def retrieve_note():
    otp = request.json.get("otp")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, encrypted_text, expires_at
        FROM notes WHERE otp = %s
    """, (otp,))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Invalid OTP"}), 404

    if datetime.utcnow() > row[2]:
        cur.execute("DELETE FROM notes WHERE id = %s", (row[0],))
        db.commit()
        return jsonify({"error": "OTP expired"}), 410

    text = decrypt(row[1])

    # One-time delete
    cur.execute("DELETE FROM notes WHERE id = %s", (row[0],))
    db.commit()
    cur.close()
    db.close()

    return jsonify({"text": text}), 200

if __name__ == "__main__":
    port=int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
