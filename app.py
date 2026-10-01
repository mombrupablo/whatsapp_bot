from flask import Flask, render_template
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


# add_log_message(json.dumps("Test_01"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
