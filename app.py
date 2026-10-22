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
    # Convertimos el JSON/dict a string
    json_text = json.dumps(msg, ensure_ascii=False)
    log_messages.append(json_text)
    new_record = Log(msg=json_text)
    db.session.add(new_record)
    db.session.commit()


# Token for the configuration of the webhook
TOKEN_APPCODE = "PAMCODE"


@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = verify_token(request)
        return challenge
    elif request.method == 'POST':
        response = receive_message(request)
        return response


@app.route("/")
def index():
    records = Log.query.all()
    ordered_records = order_by_date_time(records)
    return render_template("index.html", records=ordered_records)


def verify_token(req):
    token = req.args.get("hub_verify_token")
    challenge = req.args.get("hub_challenge")
    if challenge and token == TOKEN_APPCODE:
        return challenge
    else:
        return jsonify({"error": "Invalid Token"}), 401


def receive_message(req):
    try:
        message_object = req.get_json()
        if message_object:
            # add_log_message(message_object)
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
                                add_log_message(messages)
                                if type == "text":
                                    text = messages["text"]
                                    if "body" in text:
                                        message = text["body"]
                                        # add_log_message(message)
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
                                                    send_wsp_message(message, phone_number)
                                        elif type == "list_reply":
                                            if "list_reply" in interactive:
                                                list_reply = interactive["list_reply"]
                                                if "id" in list_reply:
                                                    message = list_reply["id"]
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
    elif "button" in message:
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
    elif "btnno" in message:
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
    elif "btntv" in message:
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
    elif "list" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": "Selecciona una Opción"
                },
                "footer": {
                    "text": "Selecciona una de las opciones para poder ayudarte"
                },
                "action": {
                    "button": "Ver Opciones",
                    "sections": [
                        {
                            "title": "Compra and Venta",
                            "rows": [
                                {
                                    "id": "btncompra",
                                    "title": "Comprar",
                                    "description": "Compra los mejores artículos de tecnología."
                                },
                                {
                                    "id": "btnventa",
                                    "title": "Vender",
                                    "description": "Vende lo que no uses."
                                }                                
                            ]
                        },
                        {
                            "title": "Distribución y Entrega",
                            "rows": [
                                {
                                    "id": "btndir",
                                    "title": "Local",
                                    "description": "Puedes visitar nuestro local."
                                },
                                {
                                    "id": "btnent",
                                    "title": "Entrega",
                                    "description": "La distribución se realiza todos los días."
                                }
                            ]
                        }
                    ]
                }
            }
        }
    elif "btncompra" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Muchas gracias por comprar en nuestros locales."
            }
        }
    elif "btnventa" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Que bieeeen, te animaste a vender tus productos."
            }
        }
    elif "btndir" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Que bueno, podes pasar por alguno de nuestros locales más cercanos a vos."
            }
        }
    elif "btnent" in message:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Por favor confirmanos dónde querés que te entreguemos tu pedido."
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

    header = {
        "Content-Type": "application/json",
        "Content-Length": str(len(data)),
        "Authorization": "Bearer EAAQTetXZAXtYBSxhD1dlIb8gMuhDV4f4KCreBaos8ZANikUTojVZB1YAd0LqwnNTkOddndZBEsSbxAJ4e70eBG6ZBggqMECAIdqIZAi2DPVsIsINCTM4LTZCBCMXmCiBI531RH7GhvRT2ShyUUmPoripgS5Kafh1bZCCRrC9hP3t9RLUQ4NNUeIejZBPeXVLiVy7RDgZDZD"
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")
    # connection.set_debuglevel(1)

    try:
        connection.request("POST", "/v25.0/1407042512488552/messages", data, header)
        response = connection.getresponse()
        # response_body = response.read().decode('utf-8')
        # add_log_message(response.status)
        # add_log_message(response.reason)
        # add_log_message(response_body)
    except Exception as e:
        add_log_message(e)
    finally:
        connection.close


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=80, debug=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
    # En producción:
    # serve(app, host='0.0.0.0', port=port)
