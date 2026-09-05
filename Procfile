web: gunicorn -w 4 -k gthread --threads 4 -b 0.0.0.0:$PORT run:app
release: flask init-db
