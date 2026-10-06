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
    print("******* Inside function add_log_message *******", flush=True)
    print(f"******* Message: {msg} *******", flush=True)
    log_messages.append(msg)
    new_record = log(msg=msg)
    db.session.add(new_record)
    db.session.commit()


# Token for the configuration of the webhook
TOKEN_APPCODE = "PAMCODE"

@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    print("******* Inside function webhook *******", flush=True)
    print(f"******* Request Method {request.method}", flush=True)

    if request.method == 'GET':
        print("******* In GET *******", flush=True)
        # response = request.get(URL_WEBHOOK, params=parameters)
        print(f"******* Request {request}", flush=True)
        challenge = verify_token(request)
        return challenge
    elif request.method == 'POST':
        print("******* In POST *******", flush=True)
        response = receive_messages(request)
        return response


# # @app.route("/webhook")
# def verify_webhook(request):
#     print("******* Inside function verify_webhook *******", flush=True)
#     print(f"******* Request: {request} *******", flush=True)
#     mode = request.args.get('hub.mode')
#     print(f"******* Mode: {mode} *******", flush=True)
#     token = request.args.get("hub.verify_token")
#     print(f"******* Token: {token} *******", flush=True)
#     challenge = request.args.get('hub.challenge')
#     print(f"******* Challenge: {challenge} *******", flush=True)
#     if mode == "subscribe" and token == "PAMCODE":
#         # Retorna una respuesta de texto plano directa
#         return str(challenge), 200
#     return f'Invalid verification Token - mode: {mode} - token: {token} - challenge: {challenge} - request: {request}', 403


def verify_token(req):
    print("******* Inside function verify_token *******", flush=True)
    mode = 'subscribe'
    print(f"******* mode: {mode}", flush=True)
    # token = req.args.get("hub.verify_token")
    token = TOKEN_APPCODE
    print(f"******* token: {token}", flush=True)
    # challenge = req.args.get("hub.challenge")
    challenge = TOKEN_APPCODE
    print(f"******* challenge: {challenge}", flush=True)
    if token and challenge == TOKEN_APPCODE:
        print("******* Returning the challenge *******", flush=True)
        return challenge
    else:
        print("******* Returning the error json *******", flush=True)
        return jsonify({"error": "Invalid Token"}), 401


@app.route('/receive')
def receive_messages():
    print("******* Inside function receive_message *******", flush=True)
    print(f"******* Req: {request} *******", flush=True)
    rt = request.get_json(force=True)
    print(f"******* Response Json: {rt} *******", flush=True)
    add_log_message(request)
    return jsonify({"message": "EVENT_RECEIVED"})


if __name__ == "__main__":
    print("****************** Starting Program ********************", flush=True)
    app.run(host="0.0.0.0", port=80, debug=True)
