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
                sender_mdp TEXT,
                receiver TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if data.get('is_identified') == "false":
        is_identified = False
    else:
        is_identified = True
    sender = data.get('sender')
    receiver = data.get('receiver')
    message = data.get('message')

    if not username or not password:
        return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400

    with sqlite3.connect(DATABASE_PATH) as conn:
        c = conn.cursor()
        if is_identified:
            # L'utilisateur doit être authentifié
            c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
            row = c.fetchone()
            if row is None:
                return jsonify({'error': 'Utilisateur non trouvé'}), 403
            stored_hash = row[0]
            if stored_hash != hash_password(password):
                return jsonify({'error': 'Mot de passe incorrect'}), 403
        else:
            # Créer un nouvel utilisateur si n'existe pas
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            if c.fetchone():
                return jsonify({'error': 'Utilisateur existe déjà, mettez is_identified à True'}), 400
            # Insérer nouvel utilisateur
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      (username, hash_password(password)))
            conn.commit()

    # Vérifier que sender correspond à username
    if sender != username:
        return jsonify({'error': 'Le champ sender doit correspondre au nom d\'utilisateur'}), 400
    if not sender or not receiver or not message:
        return jsonify({'error': 'Champs manquants'}), 400

    msg_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    with sqlite3.connect(DATABASE_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO messages VALUES (?, ?, ?, ?, ?)',
                  (msg_id, sender, receiver, message, timestamp))
        conn.commit()

    action = "Compte créé et message envoyé" if not is_identified else "Message envoyé"

    return jsonify({'status': action, 'id': msg_id})

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
