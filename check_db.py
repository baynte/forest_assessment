import os
import sqlite3
from app import app, db
from app.models import User, Assessment

def find_database():
    """Find the database file location"""
    possible_paths = [
        os.path.join(app.root_path, 'forest_assessment.db'),  # Inside app directory
        os.path.join(os.path.dirname(app.root_path), 'forest_assessment.db'),  # Current working directory
        'forest_assessment.db',  # Relative path
        os.path.join(os.getcwd(), 'instance', 'forest_assessment.db'),  # Flask default instance folder
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found database at: {path}")
            return path
    
    print("Database file not found in any of the expected locations")
    return None

def list_database_contents():
    """List all data in the database"""
    with app.app_context():
        # List users
        users = User.query.all()
        print(f"\nUsers ({len(users)}):")
        for user in users:
            print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")
        
        # List assessments
        assessments = Assessment.query.all()
        print(f"\nAssessments ({len(assessments)}):")
        for assessment in assessments:
            print(f"  - ID: {assessment.id}, Name: {assessment.name}, Location: {assessment.location}, User ID: {assessment.user_id}")
            print(f"    Processed: {assessment.processed}, Damage: {assessment.damage_percentage}%")

def check_assessment_model():
    """Check if the Assessment model has all required fields"""
    print("\nChecking Assessment model fields:")
    assessment = Assessment()
    for column in Assessment.__table__.columns:
        print(f"  - {column.name}: {column.type}")
    
    # Try to access some key fields to verify they exist
    try:
        print("\nTesting field access:")
        print(f"  - Can access 'name': {hasattr(assessment, 'name')}")
        print(f"  - Can access 'location': {hasattr(assessment, 'location')}")
        print(f"  - Can access 'damage_percentage': {hasattr(assessment, 'damage_percentage')}")
    except Exception as e:
        print(f"Error accessing fields: {str(e)}")

def check_database_schema():
    """Check the database schema directly using SQLite"""
    db_path = find_database()
    if not db_path:
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\nDatabase Schema:")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get columns for this table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for column in columns:
            # Column format: (cid, name, type, notnull, dflt_value, pk)
            print(f"  - {column[1]} ({column[2]}), {'NOT NULL' if column[3] else 'NULL'}, {'PK' if column[5] else ''}")
    
    conn.close()

if __name__ == "__main__":
    print("Database Check Tool")
    print("==================")
    
    # Find the database
    db_path = find_database()
    
    # Check the database schema
    check_database_schema()
    
    # Check the Assessment model
    check_assessment_model()
    
    # List database contents
    list_database_contents()
    
    print("\nDatabase check completed") 