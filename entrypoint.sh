#!/bin/bash
set -e
python -c "from app import app, db
with app.app_context():
    db.create_all()
    print('DB tables ready')"
exec gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:8000 app:app
