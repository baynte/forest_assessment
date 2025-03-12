import os
from app import app, db

# Delete the existing database file
db_path = os.path.join(app.root_path, 'forest_assessment.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted existing database: {db_path}")

# Create all tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully")

print("Database recreation completed") 