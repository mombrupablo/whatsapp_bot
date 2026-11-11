from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import psycopg2
import requests
import time
import random
from dotenv import load_dotenv
import os

# Get envirnment variables.
load_dotenv(dotenv_path="./.env")
pg_db_name = os.getenv("AIRFLOW_DBNAME")
pg_db_user = os.getenv("AIRFLOW_DBUSER")
pg_db_password = os.getenv("AIRFLOW_DBPASSWORD")
pg_db_host = os.getenv("AIRFLOW_DBHOST")
pg_db_port = os.getenv("AIRFLOW_DBPORT")
waha_api_key = os.getenv("WAHA_API_KEY")

default_args = {
    'owner': 'whatsapp_bulk_bot',
    'start_date': datetime(2026, 11, 4),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Set connection data to PostgreSQL db.
DB_CONFIG = {
    "dbname": pg_db_name,
    "user": pg_db_user,
    "password": pg_db_password,
    "host": pg_db_host,
    "port": pg_db_port
}


def analyze_pending_messages():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Get pendings messages.
    cursor.execute(f"SELECT id, message FROM {pg_db_msg_tb_name} WHERE status = 'pending'")
    pendings = cursor.fetchall()

    for row in pendings:
        msg_id, text = row[0], row[1]

        # Analytics task example: Counts the number of words in the message.
        words_qty = len(text.split())
        analysis_results = f"Analysis: {words_qty} detected words."
        final_response = f"Hi, we've processed your analytical request. It contains {words_qty} words."
        # ----------------------------------

        # Updates record by changing the status to 'processed' and iforming datetimes
        cursor.execute(f"""
            UPDATE {pg_db_msg_tb_name}
            SET analysis = %s, response = %s, status = 'processed', processed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (analysis_results, final_response, msg_id))

    conn.commit()
    cursor.close()
    conn.close()


def send_responses_batch():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Brings the analyzed messages that are ready to send to whatsapp.
    cursor.execute(f"SELECT id, phone, user_name, response FROM {pg_db_msg_tb_name} WHERE status = 'processed'")
    ready_to_send = cursor.fetchall()

    waha_url = "http://waha:3000/api/sendText"
    headers = {
        "X-Api-Key": waha_api_key,
        "Content-Type": "application/json"
    }

    for row in ready_to_send:
        msg_id, phone, user_name, response = row[0], row[1], row[2], row[3]

        # Use a random greetings message.
        greetings = [f"Hi {user_name}, ", f"Good news {user_name}: ", "Done, ", "There you go, "]
        random_greeting = random.choice(greetings)
        final_text = f"{random_greeting}{response}"

        payload = {
            "chatId": phone,
            "text": final_text
        }

        # Generates a pause between 4 and 10 segundos to simulate human input in whatsapp.
        wait_time = random.randint(4, 10)
        print(f"[Anti-Ban] Waiting {wait_time} seconds before sending the message to {phone}...")
        time.sleep(wait_time)

        try:
            response = requests.post(waha_url, json=payload, headers=headers, timeout=10)

            if response.status_code in [200, 201]:
                cursor.execute(f"UPDATE {pg_db_msg_tb_name} SET status = 'sent' WHERE id = %s", (msg_id,))
                print(f"[SUCCESS] Message sent to {phone}")
            else:
                print(f"[WAHA ERROR] code {response.status_code}: {response.text}")

        except Exception as e:
            print(f"[NETWORK ERROR] Could not connect with WAHA: {str(e)}")

        conn.commit()  # This commit is just in case the process errors out, so the last record is saved.

    cursor.close()
    conn.close()


with DAG(
    'whatsapp_postgres_analytics',
    default_args=default_args,
    schedule_interval='*/10 * * * *',  # The dag gets fired every 10 minutes
    catchup=False
) as dag:

    task_analyze = PythonOperator(
        task_id='analizar_mensajes_postgres',
        python_callable=analyze_pending_messages
    )

    task_send = PythonOperator(
        task_id='enviar_respuestas_postgres',
        python_callable=send_responses_batch
    )

    task_analyze >> task_send
