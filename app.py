from flask import Flask, render_template, jsonify
import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

print("=== DÉMARRAGE DE L'APPLICATION ===")

app = Flask(__name__)

# Données en mémoire par défaut
equipements_memory = [
    {"id": 1, "nom": "Routeur principal", "ip": "192.168.1.1", "status": "up", "type": "routeur"},
    {"id": 2, "nom": "Switch cœur", "ip": "192.168.1.2", "status": "up", "type": "switch"},
    {"id": 3, "nom": "Serveur web", "ip": "192.168.1.10", "status": "down", "type": "serveur"}
]

# Historique des alertes
historique_pannes = []

def get_db():
    """Connexion à la base de données monitoring"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'db'),
                database='monitoring',
                user=os.getenv('DB_USER', 'admin'),
                password=os.getenv('DB_PASSWORD', 'secret')
            )
            return conn
        except psycopg2.OperationalError:
            if attempt < max_attempts - 1:
                time.sleep(2)
            else:
                raise

def envoyer_alerte(equipement):
    """Simulation d'envoi d'alerte email avec historique"""
    # Créer l'entrée d'historique
    alerte = {
        "id": len(historique_pannes) + 1,
        "equipement": equipement['nom'],
        "ip": equipement['ip'],
        "status": equipement['status'],
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": f"⚠️ L'équipement {equipement['nom']} est hors ligne !"
    }
    historique_pannes.append(alerte)
    
    print(f"\n📧 [ALERTE] Équipement DOWN : {equipement['nom']} ({equipement['ip']})")
    print(f"   → Alerte envoyée à admin@monitoring.local")
    print(f"   → {alerte['message']}\n")

def init_db():
    """Initialisation de la base de données"""
    try:
        print("🔄 Connexion à PostgreSQL...")
        
        # Connexion directe à monitoring
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'db'),
            database=os.getenv('DB_NAME', 'monitoring'),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASSWORD', 'secret')
        )
        cur = conn.cursor()
        
        # Créer la table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS equipements (
                id SERIAL PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                ip VARCHAR(15) NOT NULL,
                status VARCHAR(10) DEFAULT 'unknown',
                type VARCHAR(50),
                last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insérer données test
        cur.execute("SELECT COUNT(*) FROM equipements")
        if cur.fetchone()[0] == 0:
            equipements_test = [
                ('Routeur principal', '192.168.1.1', 'up', 'routeur'),
                ('Switch cœur', '192.168.1.2', 'up', 'switch'),
                ('Serveur web', '192.168.1.10', 'down', 'serveur')
            ]
            for eq in equipements_test:
                cur.execute(
                    'INSERT INTO equipements (nom, ip, status, type) VALUES (%s, %s, %s, %s)',
                    eq
                )
            print("✅ Données de test insérées")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Base de données prête !")
        
    except Exception as e:
        print(f"⚠️ Erreur: {e}")
        print("⚠️ Utilisation des données en mémoire")

# Initialisation
init_db()

@app.route('/')
def accueil():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM equipements')
        equipements = cur.fetchall()
        cur.close()
        conn.close()
    except:
        equipements = equipements_memory
    
    return render_template('index.html', 
                         message="Monitoring réseau",
                         date=datetime.datetime.now(),
                         equipements=equipements)

@app.route('/api/equipements')
def api_liste():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM equipements')
        equipements = cur.fetchall()
        cur.close()
        conn.close()
        
        # Vérifier les équipements DOWN
        for eq in equipements:
            if eq['status'] == 'down':
                envoyer_alerte(eq)
        
        return jsonify(equipements)
    except:
        # Fallback mémoire
        for eq in equipements_memory:
            if eq['status'] == 'down':
                envoyer_alerte(eq)
        return jsonify(equipements_memory)

@app.route('/api/stats')
def api_stats():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM equipements')
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM equipements WHERE status='up'")
        up = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM equipements WHERE status='down'")
        down = cur.fetchone()[0]
        cur.close()
        conn.close()
    except:
        total = len(equipements_memory)
        up = sum(1 for eq in equipements_memory if eq['status'] == 'up')
        down = sum(1 for eq in equipements_memory if eq['status'] == 'down')
    
    return jsonify({
        "total": total,
        "up": up,
        "down": down,
        "taux": round((up/total)*100 if total > 0 else 0, 2)
    })

@app.route('/historique')
def historique_page():
    """Page web de l'historique"""
    return render_template('historique.html', 
                         historique=historique_pannes,
                         date=datetime.datetime.now())

@app.route('/api/historique')
def api_historique():
    """API pour l'historique"""
    return jsonify(historique_pannes)

if __name__ == '__main__':
    print("="*60)
    print("🚀 SERVEUR FLASK DÉMARRÉ")
    print("="*60)
    print("📌 Interface web: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/equipements")
    print("📊 Stats: http://localhost:5000/api/stats")
    print("="*60)
    
    # Démarrer le serveur
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"Erreur au démarrage: {e}")