import subprocess
import os

def run_migrations():
    # Create migrations directory if it doesn't exist
    if not os.path.exists('migrations'):
        os.makedirs('migrations')
        os.makedirs('migrations/versions')
        # Initialize Alembic
        subprocess.run(['alembic', 'init', 'migrations'])
    
    # Create a new migration
    subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'add barcode field'])
    
    # Apply the migration
    subprocess.run(['alembic', 'upgrade', 'head'])

if __name__ == '__main__':
    run_migrations() 