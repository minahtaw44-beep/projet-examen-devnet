# Image de base Python
FROM python:3.9-slim

# Dossier de travail
WORKDIR /app

# Copier les fichiers
COPY requirements.txt .
COPY app.py .
COPY templates ./templates

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Port exposé
EXPOSE 5000

# Commande au démarrage
CMD ["python", "app.py"]