from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json
import os


app = Flask(__name__)

# SQLite DB Config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///metapython.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Definition of the table for logging
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    msg = db.Column(db.Text, nullable=False)


# Table creation
with app.app_context():
    db.create_all()
    # prueba1 = Log(msg='Mensaje de prueba 1')
    # prueba2 = Log(msg='Mensaje de prueba 2')
    # db.session.add(prueba1)
    # db.session.add(prueba2)
    # db.session.commit()


# Order the records by a field
def order_by_date_time(records):
    return sorted(records, key=lambda x: x.date_time, reverse=True)


@app.route('/')
def index():
    records = Log.query.all()
    ordered_records = order_by_date_time(records)
    return render_template("index.html", records=ordered_records)


log_messages = []


# Function to add log messages to the db
def add_log_message(data):
    try:
        print("******* Inside function add_log_message *******", flush=True)
        print(f"******* Message: {data} *******", flush=True)

        # Convertimos el JSON/dict a string
        json_text = json.dumps(data, ensure_ascii=False, indent=2)    

        log_messages.append(json_text)
        new_record = Log(msg=json_text)
        db.session.add(new_record)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error guardando en BD: {str(e)}", flush=True)
        raise


# Token for the configuration of the webhook
TOKEN_APPCODE = "PAMCODE"


@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    print("******* Inside function webhook *******", flush=True)

    if request.method == 'GET':
        print("******* In GET *******", flush=True)
        challenge = verify_token(request)
        return challenge
    elif request.method == 'POST':
        print("******* In POST *******", flush=True)
        response = receive_message(request)
        return response


def verify_token(req):
    print("******* Inside function verify_token *******", flush=True)
    mode = req.args.get("hub.mode")
    # mode = 'subscribe'
    print(f"******* mode: {mode}", flush=True)
    token = req.args.get("hub.verify_token")
    # token = TOKEN_APPCODE
    print(f"******* token: {token}", flush=True)
    challenge = req.args.get("hub.challenge")
    # challenge = TOKEN_APPCODE
    print(f"******* challenge: {challenge}", flush=True)
    # if token and challenge == TOKEN_APPCODE:
    if mode == 'subscribe' and token == TOKEN_APPCODE:
        print("******* Token verified. Returning the challenge *******", flush=True)
        return challenge
    else:
        print("******* Token invalid. Returning the error json *******", flush=True)
        return jsonify({"error": "Invalid Token"}), 401


def receive_message(req):
    try:
        print("******* Inside function receive_message *******", flush=True)

        data = req.get_json(silent=True)

        if data is None:
            print("No se recibió JSON válido", flush=True)
            return jsonify({'error': 'JSON inválido'}), 400

        rt_json = json.dumps(data, ensure_ascii=False, indent=2)

        print(f"******* Response Json: {rt_json} *******", flush=True)

        add_log_message(data)

        return jsonify({"message": "EVENT_RECEIVED"}), 200

    except Exception as e:
        print(f"Error en webhook POST: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    print("****************** Starting Program ********************", flush=True)
    # app.run(host="0.0.0.0", port=80, debug=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
    # En producción:
    # serve(app, host='0.0.0.0', port=port)
