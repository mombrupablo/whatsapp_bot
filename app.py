from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix  # <-- Requerido para Gunicorn en Render
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import http.client
import json
import os


app = Flask(__name__)

# Esto le enseña a Flask a leer los argumentos detrás del proxy de Render
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# SQLite DB Config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///metapython.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Definition of the table for logging
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    msg = db.Column(db.Text, nullable=False)


# Table creation
with app.app_context():
    db.create_all()


# Order the records by a field
def order_by_date_time(records):
    return sorted(records, key=lambda x: x.date_time, reverse=True)


log_messages = []


# Function to add log messages to the db
def add_log_message(msg):
    print("******* Inside function add_log_message *******", flush=True)
    # print(f"******* Message: {data} *******", flush=True)

    # Convertimos el JSON/dict a string
    json_text = json.dumps(msg, ensure_ascii=False)
    # print(f"******* json_text: {json_text} *******", flush=True)

    log_messages.append(json_text)
    new_record = Log(msg=json_text)
    db.session.add(new_record)
    db.session.commit()


# Token for the configuration of the webhook
TOKEN_APPCODE = "PAMCODE"


@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    print("******* Inside function webhook *******", flush=True)

    if request.method == 'GET':
        # print("******* In GET *******", flush=True)
        challenge = verify_token(request)
        return challenge
    elif request.method == 'POST':
        # print("******* In POST *******", flush=True)
        response = receive_message(request)
        return response


@app.route("/")
def index():
    # print("************ Estoy en Index ************", flush=True)
    records = Log.query.all()
    ordered_records = order_by_date_time(records)
    return render_template("index.html", records=ordered_records)


def verify_token(req):
    # print("******* Inside function verify_token *******", flush=True)
    token = req.args.get("hub_verify_token")
    # print(f"******* token: {token}", flush=True)
    challenge = req.args.get("hub_challenge")
    # print(f"******* challenge: {challenge}", flush=True)
    if challenge and token == TOKEN_APPCODE:
        # print("******* Token verified. Returning the challenge *******", flush=True)
        return challenge
    else:
        # print("******* Token invalid. Returning the error json *******", flush=True)
        return jsonify({"error": "Invalid Token"}), 401


def receive_message(req):
    try:
        # print("******* Inside function receive_message *******", flush=True)
        rt = req.get_json()
        # print(f"******* Response Json: {rt} *******", flush=True)

        entry = rt["entry"][0]
        print(f"******* entry: {entry} *******", flush=True)
        changes = entry["changes"][0]
        print(f"******* changes: {changes} *******", flush=True)
        value = changes["value"]
        print(f"******* value: {value} *******", flush=True)
        message_object = value["messages"][0]
        if message_object:
            print(f"******* message: {message_object} *******", flush=True)
            if "type" in message_object:
                msg_type = message_object["type"]
                print(f"******* Message Type: {msg_type} *******", flush=True)
                if msg_type == "interactive":
                    return 0
                if msg_type == "text":
                    if "text" in message_object:
                        message = message_object["text"]["body"]
                        print(f"******* Text: {message} *******", flush=True)
                        from_number = message_object["from"]
                        print(f"******* From number: {from_number} *******", flush=True)
                        # add_log_message(json.dumps(message, ensure_ascii=False))
                        add_log_message(message)
                        # add_log_message(json.dumps(from_number, ensure_ascii=False))
                        add_log_message(from_number)
                        send_wsp_message(message, from_number)

        return jsonify({"message": "EVENT_RECEIVED"}), 200

    except Exception as e:
        return jsonify({"message": "EVENT_RECEIVED"}), 200


def send_wsp_message(message, phone_number):
    message = message.lower()

    data = {}
    if "hola" in message:
        data = {
            "messaging_product": "whatsapp",   
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, como estás? Bienvenido!"
            }
        }
    else:
        data = {
            "messaging_product": "whatsapp",   
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, como estás? Bienvenido!.\nPor favor indica la opción:\n💬1.Hablar\n📳2.Llamar\n🚪3.Huir"
            }
        }
    data = json.dumps(data)

    header = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EAAQTetXZAXtYBSsHBYHEZAiusUQmdXM0MPxawmkfBMdMJORQiXLrpiSBZCm4ZCR1v6Kc4dD5iLnmmcyt0ZBgcRQXU471roxJP5tPz8DAXIXDB02uEpD4slN9lBfDltVRmyQ70fRZCI5OLxxIRMdgBGN5DL8Hhf99RP8H1OdMU0vNTlgZCvxvBjKojALuYLX4mhrjM1PgpsFBUnMvW0E56XgzWDDyamw3dMfa9WfWOtk2CZCDWZBaRggaCYpUsZCEMsFYjae65i5t8oWvxgwgRg4BxKZBBEZD"
    }

    connection = http.client.HTTPConnection("graph.facebook.com")

    try:
        connection.request("POST", "/v25.0/1407042512488552/messages", data, header)
        response = connection.getresponse()
        add_log_message(response.status)
        add_log_message(response.reason)
        # print(f"******** Response Status: {response.status}", flush=True)
        # print(f"******** Response Reason: {response.reason}", flush=True)
    except Exception as e:
        add_log_message(e)
    finally:
        connection.close


if __name__ == "__main__":
    # print("****************** Starting Program ********************", flush=True)
    # app.run(host="0.0.0.0", port=80, debug=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
    # En producción:
    # serve(app, host='0.0.0.0', port=port)
