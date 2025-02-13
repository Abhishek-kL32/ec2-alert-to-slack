from flask import Flask, request, jsonify
import mysql.connector
from rq import Queue
from worker import conn
import tasks  # Import tasks for enqueueing
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

# MySQL database configuration
DB_CONFIG = {
    'user': 'slack_user',
    'password': 'T33th123!',
    'host': 'localhost',
    'database': 'slack_ignore_db'
}

# Redis Queue setup
q = Queue(connection=conn)

# Initialize MySQL Tables
def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ignore_list (
                        instance_id VARCHAR(255) UNIQUE,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS permanent_ignore_list (
                        instance_id VARCHAR(255) UNIQUE)''')
    conn.commit()
    conn.close()

# Home Route
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the EC2 Monitoring Slack API!"})

# Slack Command Handler for Temporary/Permanent Ignore, Stop/Start
@app.route('/ignore_instance', methods=['POST'])
def slack_commands():
    """
    Handle Slack commands for temporary ignore, permanent ignore, stop, and start actions.
    """
    data = request.form  # Slack sends form-encoded data
    text = data.get('text', '').strip()
    
    # Default response message
    response_text = (
        "Unknown command. Use:\n"
        "'add <instance_id>' - Add to temporary ignore list\n"
        "'remove <instance_id>' - Remove from temporary ignore list\n"
        "'add_permanent <instance_id>' - Add to permanent ignore list\n"
        "'remove_permanent <instance_id>' - Remove from permanent ignore list\n"
        "'stop <instance_id>' - Stop an instance\n"
        "'start <instance_id>' - Start an instance"
    )

    try:
        if text.startswith("add_permanent"):
            instance_id = text.split()[1]
            tasks.add_to_permanent_ignore_list(instance_id)
            response_text = f"Instance ID {instance_id} added to the permanent ignore list."

        elif text.startswith("remove_permanent"):
            instance_id = text.split()[1]
            tasks.remove_from_permanent_ignore_list(instance_id)
            response_text = f"Instance ID {instance_id} removed from the permanent ignore list."

        elif text.startswith("add"):
            instance_id = text.split()[1]
            tasks.add_to_ignore_list(instance_id)
            response_text = f"Instance ID {instance_id} added to the temporary ignore list."

        elif text.startswith("remove"):
            instance_id = text.split()[1]
            tasks.remove_from_ignore_list(instance_id)
            response_text = f"Instance ID {instance_id} removed from the temporary ignore list."

        elif text.startswith("stop"):
            instance_id = text.split()[1]
            job = q.enqueue(tasks.stop_instance, instance_id)
            response_text = f"Instance ID {instance_id} is being stopped. Job ID: {job.id}."

        elif text.startswith("start"):
            instance_id = text.split()[1]
            job = q.enqueue(tasks.start_instance, instance_id)
            response_text = f"Instance ID {instance_id} is being started. Job ID: {job.id}."

    except (IndexError, Exception) as e:
        response_text = f"Error processing command: {str(e)}"

    return jsonify({'text': response_text})

# Stop an EC2 Instance (Manual API Trigger)
@app.route('/stop_instance', methods=['POST'])
def stop_instance():
    """
    Manually stop an EC2 instance and enqueue the task.
    """
    instance_id = request.form['instance_id']
    job = q.enqueue(tasks.stop_instance, instance_id)
    return jsonify({'message': f"Instance ID {instance_id} is being stopped. Job ID: {job.id}"}), 202

# Start an EC2 Instance (Manual API Trigger)
@app.route('/start_instance', methods=['POST'])
def start_instance():
    """
    Manually start an EC2 instance and enqueue the task.
    """
    instance_id = request.form['instance_id']
    job = q.enqueue(tasks.start_instance, instance_id)
    return jsonify({'message': f"Instance ID {instance_id} is being started. Job ID: {job.id}"}), 202

# EC2 Instance Check Route
@app.route('/check_instances', methods=['POST'])
def check_instances():
    """
    Trigger EC2 instance checks and Slack notifications.
    """
    job = q.enqueue(tasks.fetch_ec2_instances)
    return jsonify({'message': f"Instance check started. Job ID: {job.id}"}), 202

# Scheduler setup (Unchanged)
scheduler = BackgroundScheduler()
scheduler.add_job(func=tasks.fetch_ec2_instances, trigger="interval", minutes=15)
scheduler.start()
scheduler.add_job(func=lambda: cleanup_ignore_list(2), trigger="interval", days=1)

# Ensure the scheduler shuts down on app exit
atexit.register(lambda: scheduler.shutdown())

# Initialize Database Tables
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)

