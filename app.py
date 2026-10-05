from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone


app = Flask(__name__)

# SQLite DB Config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///metapython.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Definition of the table for logging
class log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    msg = db.Column(db.TEXT)


# Table creation
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    records = log.query.all()
    ordered_records = order_by_date_time(records)
    return render_template("index.html", records=ordered_records)


# Order the records by a field
def order_by_date_time(records):
    return sorted(records, key=lambda x: x.date_time, reverse=True)


log_messages = []


# Function to add log messages to the db
def add_log_message(msg):
    log_messages.append(msg)
    new_record = log(msg=msg)
    db.session.add(new_record)
    db.session.commit()


# Token for the configuration of the webhook
TOKEN_APPCODE = "PAMCODE"


@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    print(f"****************** Inside function webhook ********************")
    print(f"******** Request Method {request.method}")
    if request.method == 'GET':
        challenge = verify_webhook(request)
        return challenge
    elif request.method == 'POST':
        response = receive_messages(request)
        return response


@app.route("/webhook")
def verify_webhook():
    print("***************** Inside function verify_webhook *******************")
    mode = request.args.get('hub.mode') or request.args.get('hub_mode')
    token = request.args.get("hub.verify_token") or request.args.get("hub_verify_token")
    challenge = request.args.get('hub.challenge') or request.args.get('hub_challenge')
    if mode == "subscribe" and token == "PAMCODE":
        # Retorna una respuesta de texto plano directa
        return str(challenge), 200
    return 'Invalid verification Token - mode: {0} - token: {1} - challenge: {2}'.format(mode, token, challenge), 403


# def verify_token(req):
#     token = req.args.get("hub.verify_token")
#     challenge = req.args.get("hub.challenge")
#     if token and challenge == TOKEN_APPCODE:
#         return challenge
#     else:
#         return jsonify({"error": "Invalid Token"}), 401


def receive_messages(req):
    req = request.get_json()
    add_log_message(req)
    return jsonify({"message": "EVENT_RECEIVED"})


if __name__ == "__main__":
    print("****************** Starting Program ********************")
    app.run(host="0.0.0.0", port=80, debug=True)
