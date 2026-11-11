from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Get envirnment variables.
load_dotenv(dotenv_path="./.env")
pg_db_name = os.getenv("DBNAME")
pg_db_user = os.getenv("DBUSER")
pg_db_password = os.getenv("DBPASSWORD")
pg_db_host = os.getenv("DBHOST")
pg_db_port = os.getenv("DBPORT")
pg_db_msg_tb_name = os.getenv("MSG_TABLENAME")

# Set connection data to PostgreSQL db.
DB_CONFIG = {
    "dbname": pg_db_name,
    "user": pg_db_user,
    "password": pg_db_password,
    "host": pg_db_host,
    "port": pg_db_port
}


def db_connect():
    try:
        # Connect to PostgreSQL db.
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        return jsonify({"error": f"Database error in db_connect(): {str(e)}"}), 500


# Function to insert a whatsapp message to the db.
def db_insert_message(conn, phone, message, user_name):
    try:
        cursor = conn.cursor()
        # Insert message
        cursor.execute(
            f"""INSERT INTO {pg_db_msg_tb_name} 
            (phone, message, user_name) VALUES (%s, %s, %s)""",
            (phone, message, user_name)
        )
        conn.commit()
        cursor.close()
        return jsonify({"status": "received_and_queued"}), 200
    except Exception as e:
        return jsonify({"error": f"Database error in db_insert_message(): {str(e)}"}), 500


# Function to retrieve the messages in the DB
def db_select_messages(conn):
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"SELECT * FROM {pg_db_msg_tb_name} ORDER BY created_at DESC"
        )
        records = cursor.fetchall()
        conn.close()
        return records
    except Exception as e:
        return jsonify({"error": f"Database error in db_select_messages(): {str(e)}"}), 500


# Function to get the response from whatsapp
@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json()

    if not data or 'phone' not in data or 'message' not in data:
        return jsonify({"error": "Incomplete data"}), 400

    phone = data.get('phone')
    message = data.get('message')
    user_name = data.get('user_name', 'John Doe')

    conn = db_connect()
    db_insert_message(conn, phone, message, user_name)


# Function to access to the index web page
@app.route("/")
def index():
    try:
        conn = db_connect()
        # db_insert_message(conn, '1111', 'Hola', 'Pablo')
        records = db_select_messages(conn)
        return render_template("bulk_bot_index.html", records=records)
    except Exception as e:
        return jsonify({"error": f"Database error in index(): {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
