from flask import Flask, request, jsonify
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)


# Création de la DB simple
def init_db():
    with sqlite3.connect('chat.db') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender TEXT,
                receiver TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    sender = data.get('sender')
    receiver = data.get('receiver')
    message = data.get('message')
    if not sender or not receiver or not message:
        return jsonify({'error': 'Champs manquants'}), 400

    msg_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    with sqlite3.connect('chat.db') as conn:
        c = conn.cursor()
        c.execute('INSERT INTO messages VALUES (?, ?, ?, ?, ?)',
                  (msg_id, sender, receiver, message, timestamp))
        conn.commit()

    return jsonify({'status': 'Message envoyé', 'id': msg_id})


@app.route('/get_messages/<user>', methods=['GET'])
def get_messages(user):
    with sqlite3.connect('chat.db') as conn:
        c = conn.cursor()
        c.execute('SELECT sender, message, timestamp FROM messages WHERE receiver = ?', (user,))
        msgs = c.fetchall()

    messages = [{'sender': s, 'message': m, 'timestamp': t} for s, m, t in msgs]
    return jsonify({'messages': messages})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
