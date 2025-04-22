import os
import subprocess

def init_migrations():
    # Create migrations directory if it doesn't exist
    if not os.path.exists('migrations'):
        os.makedirs('migrations')
        os.makedirs('migrations/versions')
    
    # Initialize Alembic
    subprocess.run(['alembic', 'init', 'migrations'])
    
    # Create the first migration
    subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'initial migration'])

if __name__ == '__main__':
    init_migrations() 