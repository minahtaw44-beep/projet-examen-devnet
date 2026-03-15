from flask import Flask, render_template, jsonify
import datetime

app = Flask(__name__)

equipements = [
    {"id": 1, "nom": "Routeur principal", "ip": "192.168.1.1", "status": "up", "type": "routeur"},
    {"id": 2, "nom": "Switch cœur", "ip": "192.168.1.2", "status": "up", "type": "switch"},
    {"id": 3, "nom": "Serveur web", "ip": "192.168.1.10", "status": "down", "type": "serveur"}
]

@app.route('/')
def accueil():
    return render_template('index.html', 
                         message="Monitoring réseau",
                         date=datetime.datetime.now(),
                         equipements=equipements)

@app.route('/api/equipements')
def api_liste():
    return jsonify(equipements)

@app.route('/api/stats')
def api_stats():
    total = len(equipements)
    up = sum(1 for eq in equipements if eq['status'] == 'up')
    down = sum(1 for eq in equipements if eq['status'] == 'down')
    return jsonify({"total": total, "up": up, "down": down})

if __name__ == '__main__':
    print("✅ Serveur démarré sur http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)