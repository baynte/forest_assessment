import os
import sqlite3
from app import app, db
from app.models import User, Assessment

def find_database():
    """Find the database file location"""
    possible_paths = [
        os.path.join(app.root_path, 'forest_assessment.db'),  # Inside app directory
        os.path.join(os.path.dirname(app.root_path), 'forest_assessment.db'),  # Parent directory
        os.path.join(os.getcwd(), 'forest_assessment.db'),  # Current working directory
        'forest_assessment.db'  # Relative path
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found database at: {path}")
            return path
    
    print("Database file not found in any of the expected locations")
    return None

def inspect_database():
    """Inspect the database structure and print table information"""
    db_path = find_database()
    
    if not db_path:
        print("Cannot inspect database: file not found")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\nTables in the database:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Get schema for each table
    for table in tables:
        table_name = table[0]
        print(f"\nSchema for table '{table_name}':")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
    
    conn.close()
    return True

def recreate_database():
    """Recreate the database from scratch"""
    # First, find the existing database if any
    existing_db = find_database()
    
    if existing_db:
        print(f"Deleting existing database: {existing_db}")
        os.remove(existing_db)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
    
    # Verify the new database
    db_path = find_database()
    if db_path:
        print(f"New database created at: {db_path}")
    else:
        print("Warning: Could not find the newly created database")

def create_test_data():
    """Create test data in the database"""
    with app.app_context():
        # Create a test user
        user = User(username="testuser", email="test@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        
        # Create a test assessment
        assessment = Assessment(
            name="Test Assessment",
            location="Test Location",
            description="Test Description",
            user_id=user.id
        )
        db.session.add(assessment)
        db.session.commit()
        
        print("Test data created successfully")
        
        # Verify the test data
        print("\nVerifying test data:")
        users = User.query.all()
        print(f"Users: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.email})")
        
        assessments = Assessment.query.all()
        print(f"Assessments: {len(assessments)}")
        for assessment in assessments:
            print(f"  - {assessment.name} ({assessment.location})")

if __name__ == "__main__":
    print("Database Diagnosis and Repair Tool")
    print("==================================")
    
    print("\nStep 1: Inspecting current database")
    inspect_database()
    
    print("\nStep 2: Recreating database")
    recreate_database()
    
    print("\nStep 3: Creating test data")
    create_test_data()
    
    print("\nDatabase diagnosis and repair completed successfully") 