import sqlite3
from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import hashlib  # pour hasher le mot de passe simplement

app = Flask(__name__)

DATABASE_PATH = 'chat.db'  # même fichier pour simplifier, peut être séparé

def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        c = conn.cursor()
        # Table messages
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender TEXT,
                receiver TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        # Table users
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT
            )
        ''')
        conn.commit()

def hash_password(password):
    # Hash simple avec sha256 (pour l'exemple uniquement, pas recommandé en prod)
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth(username, password):
    with sqlite3.connect(DATABASE_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        if row is None:
            return False
        stored_hash = row[0]
        return stored_hash == hash_password(password)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    is_identified = data.get('is_identified', False)  # Par défaut False
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

if __name__ == '__main__':
    init_db()

    # Pour l'exemple, on insère un utilisateur au démarrage s'il n'existe pas
    with sqlite3.connect(DATABASE_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', ('alice',))
        if c.fetchone() is None:
            c.execute('INSERT INTO users VALUES (?, ?)', ('alice', hash_password('password123')))
            conn.commit()

    app.run(host='0.0.0.0', port=5000)
