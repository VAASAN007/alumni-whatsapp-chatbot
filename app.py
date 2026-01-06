from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3

app = Flask(__name__)

# ---------------- DATABASE ----------------
def db():
    return sqlite3.connect("alumni.db")


# ---------------- WHATSAPP BOT ----------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.values.get("Body", "").strip()
    sender = request.values.get("From")

    resp = MessagingResponse()
    conn = db()
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alumni (
            whatsapp TEXT,
            step INTEGER,
            name TEXT,
            yop TEXT,
            role TEXT,
            company TEXT,
            location TEXT,
            mobile TEXT,
            photo TEXT
        )
    """)

    cur.execute("SELECT step FROM alumni WHERE whatsapp=?", (sender,))
    row = cur.fetchone()

    # -------- STEP 0 : INTRODUCTION TEXT ONLY --------
    if msg.lower() in ["hi", "hello", "start"] and not row:
        cur.execute("INSERT INTO alumni (whatsapp, step) VALUES (?, 0)", (sender,))
        conn.commit()

        resp.message(
            "🎓 *Bishop Heber College*\n"
            "*PG Department of Computer Science (SF–II)*\n\n"
            "Dear Alumni,\n\n"
            "This WhatsApp chatbot is created to collect alumni details for:\n"
            "• Department records\n"
            "• Alumni engagement\n"
            "• Placement and academic development\n\n"
            "🔐 Your information will be kept confidential and used only for official purposes.\n\n"
            "👉 Please reply *OK* to continue."
        )

        conn.close()
        return str(resp)

    # -------- STEP 1 : WAIT FOR OK --------
    if row and row[0] == 0 and msg.lower() == "ok":
        cur.execute("UPDATE alumni SET step=1 WHERE whatsapp=?", (sender,))
        conn.commit()

        resp.message("✍️ Please enter your *Full Name*:")

        conn.close()
        return str(resp)

    # -------- DATA COLLECTION FLOW --------
    if row:
        step = row[0]

        if step == 1:
            cur.execute("UPDATE alumni SET name=?, step=2 WHERE whatsapp=?", (msg, sender))
            resp.message("📅 Year of Passing?")
        elif step == 2:
            cur.execute("UPDATE alumni SET yop=?, step=3 WHERE whatsapp=?", (msg, sender))
            resp.message("💼 Current Job Role?")
        elif step == 3:
            cur.execute("UPDATE alumni SET role=?, step=4 WHERE whatsapp=?", (msg, sender))
            resp.message("🏢 Company Name?")
        elif step == 4:
            cur.execute("UPDATE alumni SET company=?, step=5 WHERE whatsapp=?", (msg, sender))
            resp.message("📍 Current Location?")
        elif step == 5:
            cur.execute("UPDATE alumni SET location=?, step=6 WHERE whatsapp=?", (msg, sender))
            resp.message("📞 Mobile Number?")
        elif step == 6:
            cur.execute("UPDATE alumni SET mobile=?, step=7 WHERE whatsapp=?", (msg, sender))
            resp.message("📷 Please upload your *Photo*")
        elif step == 7:
            photo_url = request.values.get("MediaUrl0")
            if photo_url:
                cur.execute(
                    "UPDATE alumni SET photo=?, step=8 WHERE whatsapp=?",
                    (photo_url, sender)
                )
                resp.message("✅ Thank you! Your alumni details have been successfully recorded.")
            else:
                resp.message("❌ Please upload a valid photo.")

    conn.commit()
    conn.close()
    return str(resp)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
