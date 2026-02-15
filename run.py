# Suppress TensorFlow oneDNN and other INFO messages before any TF import
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')  # 0=all, 1=no INFO, 2=no INFO/WARNING

from app import app, db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 