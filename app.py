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
    # print("******* Inside function add_log_message *******", flush=True)
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
    # print("******* Inside function webhook *******", flush=True)

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
        # print(f"******* entry: {entry} *******", flush=True)
        changes = entry["changes"][0]
        # print(f"******* changes: {changes} *******", flush=True)
        value = changes["value"]
        # print(f"******* value: {value} *******", flush=True)
        message_object = value["messages"][0]
        if message_object:
            # print(f"******* message: {message_object} *******", flush=True)
            if "type" in message_object:
                msg_type = message_object["type"]
                # print(f"******* Message Type: {msg_type} *******", flush=True)
                if msg_type == "interactive":
                    return 0
                if msg_type == "text":
                    if "text" in message_object:
                        message = message_object["text"]["body"]
                        # print(f"******* Text: {message} *******", flush=True)
                        from_number = message_object["from"]
                        phone_number = from_number.replace("9", "", 1)
                        # print(f"******* From number: {phone_number} *******", flush=True)
                        # add_log_message(json.dumps(message, ensure_ascii=False))
                        add_log_message(message)
                        # add_log_message(json.dumps(from_number, ensure_ascii=False))
                        # add_log_message(from_number)
                        send_wsp_message(message, phone_number)

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
    elif "1" in message:
        data = {
            "messaging_product": "whatsapp",   
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Irure aliqua libero"
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
                "body": """🚀 Hola, como estás? Bienvenido!.
                Por favor indica el número de opción para obtener información:
                1️⃣ Información del Curso.❓ 
                2️⃣ Ubicación del Local.📍
                3️⃣ Enviar Temarion en PDF.📄
                4️⃣ Audio explicando el Curso.🎧
                5️⃣ Video de Introducción.⏯️
                6️⃣ Hablar con un Representante.🙋🏻‍♂️🙋🏼‍♀️
                7️⃣ Horario de Atención.⏱️
                8️⃣ Volver al Menú.↩️
                """
            }
        }
    data = json.dumps(data)
    data = data.encode('utf-8')
    # print(f"******** Data sent: {data}", flush=True)

    header = {
        "Content-Type": "application/json",
        "Content-Length": str(len(data)),
        "Authorization": "Bearer EAAQTetXZAXtYBS5vz40KyYp9I0PEnZC2NJqr1n8q4lIiLMCrcaGOxTLKrn1I8uYVXLZAZAiJXlZBs2HiwRT6aVD9JZBp0I6XjEUq48quJFLf6LoJKz5WHZBAUV0Ps5ME1u4HXoAgoPXv3pwQPmmZAIBVvccbpby5uGgChL5SwgI5rRUM1k7yN8CipKaQZCLJAVPNmwZBpYhjIorCEpOoe6dfZBeGa947bYx1dr3CughrmKZCalIFjW74ZA66lyc77fZAF5YpBK7n3DzFJuDmKLkNXCu6GG2QZDZD"
    }

    # print(f"******** Header sent: {header}", flush=True)
    connection = http.client.HTTPSConnection("graph.facebook.com")
    # print(f"******** Connection: {connection}", flush=True)
    # connection.set_debuglevel(1)

    try:
        # print(f"******** Inside try ************", flush=True)
        connection.request("POST", "/v25.0/1407042512488552/messages", data, header)
        response = connection.getresponse()
        response_body = response.read().decode('utf-8')
        # print(f"********* HTTP Response: {response_body}", flush=True)
        # add_log_message(response.status)
        # add_log_message(response.reason)
        # add_log_message(response_body)
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
