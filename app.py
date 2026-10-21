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
    date_time = db.Column(db.DateTime, default=datetime.now())
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
        message_object = req.get_json()
        if message_object:
            if "entry" in message_object:
                entry = message_object["entry"][0]
                if "changes" in entry:
                    changes = entry["changes"][0]
                    if "value" in changes:
                        value = changes["value"]
                        if "messages" in value:
                            messages = value["messages"][0]
                            if "from" in messages and "type" in messages:
                                from_number = messages["from"]
                                phone_number = from_number.replace("9", "", 1)
                                type = messages["type"]
                                if type == "text":
                                    text = messages["text"]
                                    if "body" in text:
                                        message = text["body"]
                                        add_log_message(message)
                                        send_wsp_message(message, phone_number)
                                elif type == "interactive":
                                    interactive = messages["interactive"]
                                    if "type" in interactive:
                                        type = interactive["type"]
                                        if type == "button_reply":
                                            if "button_reply" in interactive:
                                                button_reply = interactive["button_reply"]
                                                if "id" in button_reply:
                                                    message = button_reply["id"]
                                                    add_log_message(message)
                                                    send_wsp_message(message, phone_number)
        return jsonify({"message": "EVENT_RECEIVED"}), 200
    except Exception as e:
        return jsonify({"message": "EVENT_RECEIVED"}), 200


def send_wsp_message(message, phone_number):
    message = message.lower()

    data = {}
    if "hola" in message or "0" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": """
                🚀 Hola, como estás? Bienvenido!.

            Por favor indica el número de opción para obtener información:
            1️⃣ Información del Curso.❓
            2️⃣ Ubicación del Local.📍
            3️⃣ Enviar Temario en PDF.📄
            4️⃣ Audio explicando el Curso.🎧
            5️⃣ Video de Introducción.⏯️
            6️⃣ Hablar con un Representante.🙋🏻‍♂️🙋🏼‍♀️
            7️⃣ Horario de Atención.⏱️
            0️⃣ Volver al Menú.↩️
            """
            }
        }
        add_log_message(message)
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
        add_log_message(message)        
    elif "2" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "location",
            "location": {
                "latitude": "-34.457146883363045",
                "longitude": "-58.883724346443834",
                "name": "La Campiña Barrio Privado",
                "address": "Las Glicinas 1600"
            }
        }
        add_log_message(message)        
    elif "3" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "document",
            "document": {
                "link": "http://file-examples.com/storage/fe557d50296ad628796165d/2017/10/file-sample_150kB.pdf",
                "caption": "Curso PDF"
            }
        }
        add_log_message(message)        
    elif "4" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "audio",
            "audio": {
                "link": "http://file-examples.com/storage/fe557d50296ad628796165d/2017/11/file_example_MP3_1MG.mp3",
                "voice": True
            }
        }
        add_log_message(message)        
    elif "5" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "video",
            "video": {
                "link": "http://file-examples.com/storage/fe557d50296ad628796165d/2017/04/file_example_MP4_480_1_5MG.mp4",
                "caption": "Video del Curso"
            }
        }
        add_log_message(message)        
    elif "6" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": """En breve nos contactaremos con vos 📡"""
            }
        }
        add_log_message(message)
    elif "7" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": """Nuestros horarios de atención son: Lun a Vie: 8 a 15 y Sab: 8 a 12"""
            }
        }
        add_log_message(message)        
    elif "button" in message:
        add_log_message("Entered in 'button in message'")
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "Confirmas tu registro?"
                },
                "footer": {
                    "text": "Selecciona una de las opciones"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btnsi",
                                "title": "Si"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btnno",
                                "title": "No"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btntv",
                                "title": "Tal Vez"
                            }
                        }
                    ]
                }
            }
        }
    elif "btnsi" in message:
        add_log_message("Entered in message == btnsi")
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Que bueno!!, Avancemos...."
            }
        }
        add_log_message(message)   
    elif "btnno" in message:
        add_log_message("Entered in message == btnno")
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Es una lástima........"
            }
        }
        add_log_message(message)        
    elif "btntv" in message:
        add_log_message("Entered in message == btntv")
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Quedamos a la espera. Animate!"
            }
        }
        add_log_message(message)        
    else:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": """
                🚀 Hola, como estás? Bienvenido!.

            Por favor indica el número de opción para obtener información:
            1️⃣ Información del Curso.❓
            2️⃣ Ubicación del Local.📍
            3️⃣ Enviar Temario en PDF.📄
            4️⃣ Audio explicando el Curso.🎧
            5️⃣ Video de Introducción.⏯️
            6️⃣ Hablar con un Representante.🙋🏻‍♂️🙋🏼‍♀️
            7️⃣ Horario de Atención.⏱️
            0️⃣ Volver al Menú.↩️
            """
            }
        }
        add_log_message(message)

    data = json.dumps(data)
    data = data.encode('utf-8')
    # add_log_message(data)
    # print(f"******** Data sent: {data}", flush=True)

    header = {
        "Content-Type": "application/json",
        "Content-Length": str(len(data)),
        "Authorization": "Bearer EAAQTetXZAXtYBS064OkKRmZCiK4Vff5vpLZBZBeRvpnnWRvCthEmZAaRU3F4hL9NvXCFEoEhbFZBDTGFtiskz02dr0nDZAqZAesZCGZA4h7eYIwM416gkiiekNEfuwcAigiXMhIuYwDccQUfm6ZAOJYS3rZCASYJqjy3pQtgAjGe6708waoZBaw8sK7oN4KVXTe64HQmUMPZBpH34ZAHiaE7YMHEQfpUpfjzZAF9mGLUnOG9qVja9Eq4iBKAUb8qhE69G7CYCPi2U0FZCoUfmR3oOZBAawp8wWmwZDZD"
    }

    # print(f"******** Header sent: {header}", flush=True)
    connection = http.client.HTTPSConnection("graph.facebook.com")
    # print(f"******** Connection: {connection}", flush=True)
    # connection.set_debuglevel(1)

    try:
        # print(f"******** Inside try ************", flush=True)
        connection.request("POST", "/v25.0/1407042512488552/messages", data, header)
        response = connection.getresponse()
        # response_body = response.read().decode('utf-8')
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
