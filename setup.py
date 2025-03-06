#!/usr/bin/env python3
"""
Setup script for the Store Performance Visualization System.
This script helps set up the project environment and run the initial data analysis.
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

def check_python_version():
    """Check if the Python version is compatible."""
    required_version = (3, 7)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required.")
        print(f"Current version is {current_version[0]}.{current_version[1]}.{current_version[2]}")
        sys.exit(1)
    
    print(f"✓ Python version {current_version[0]}.{current_version[1]}.{current_version[2]} is compatible.")

def setup_virtual_environment(env_name='venv'):
    """Set up a virtual environment for the project."""
    if os.path.exists(env_name):
        print(f"✓ Virtual environment '{env_name}' already exists.")
        return
    
    print(f"Creating virtual environment '{env_name}'...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', env_name], check=True)
        print(f"✓ Virtual environment '{env_name}' created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

def install_requirements(env_name='venv'):
    """Install required packages from requirements.txt."""
    if not os.path.exists('requirements.txt'):
        print("Error: requirements.txt not found.")
        sys.exit(1)
    
    print("Installing required packages...")
    
    # Determine the pip executable path based on OS
    if os.name == 'nt':  # Windows
        pip_path = os.path.join(env_name, 'Scripts', 'pip')
    else:  # Unix/Linux/Mac
        pip_path = os.path.join(env_name, 'bin', 'pip')
    
    try:
        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
        print("✓ Required packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def create_project_structure():
    """Create the project directory structure."""
    directories = ['data', 'src', 'maps', 'dashboard']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Create __init__.py in src directory
    init_file = os.path.join('src', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('# Package initialization\n')
    
    print("✓ Project directory structure created.")

def check_data_files():
    """Check if required data files are present."""
    data_dir = 'data'
    
    # Check for GeoJSON file
    geojson_file = os.path.join(data_dir, 'mexico_estados.geojson')
    if not os.path.exists(geojson_file):
        print(f"Warning: GeoJSON file '{geojson_file}' not found. You need to add this file manually.")
    else:
        print(f"✓ GeoJSON file '{geojson_file}' found.")
    
    # Check for monthly data files
    monthly_files = [f for f in os.listdir(data_dir) if f.startswith('datos') and f.endswith('.csv')]
    if not monthly_files:
        print(f"Warning: No monthly data files found in '{data_dir}'. You need to add at least one data file.")
    else:
        print(f"✓ Found {len(monthly_files)} monthly data files: {', '.join(monthly_files)}")
    
    return bool(monthly_files and os.path.exists(geojson_file))

def run_analysis(env_name='venv'):
    """Run the main analysis script."""
    if not os.path.exists('main.py'):
        print("Error: main.py not found.")
        return False
    
    print("Running data analysis...")
    
    # Determine the python executable path based on OS
    if os.name == 'nt':  # Windows
        python_path = os.path.join(env_name, 'Scripts', 'python')
    else:  # Unix/Linux/Mac
        python_path = os.path.join(env_name, 'bin', 'python')
    
    try:
        subprocess.run([python_path, 'main.py'], check=True)
        print("✓ Data analysis completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running analysis: {e}")
        return False

def generate_dashboard(env_name='venv'):
    """Generate the interactive dashboard."""
    if not os.path.exists('dashboard_generator.py'):
        print("Error: dashboard_generator.py not found.")
        return False
    
    print("Generating interactive dashboard...")
    
    # Determine the python executable path based on OS
    if os.name == 'nt':  # Windows
        python_path = os.path.join(env_name, 'Scripts', 'python')
    else:  # Unix/Linux/Mac
        python_path = os.path.join(env_name, 'bin', 'python')
    
    script = '''
from src import data_processing
from dashboard_generator import generate_dashboard

# Load data
monthly_data, combined_df = data_processing.load_multiple_months('data')

# Generate dashboard
generate_dashboard(monthly_data, combined_df, 'dashboard')
'''
    
    try:
        subprocess.run([python_path, '-c', script], check=True)
        print("✓ Dashboard generated successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating dashboard: {e}")
        return False

def open_dashboard():
    """Open the dashboard in the default web browser."""
    dashboard_path = os.path.join('dashboard', 'index.html')
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard file '{dashboard_path}' not found.")
        return False
    
    import webbrowser
    print("Opening dashboard in web browser...")
    webbrowser.open(f'file://{os.path.abspath(dashboard_path)}')
    return True

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Set up the Store Performance Visualization System')
    parser.add_argument('--env-name', default='venv', help='Name of the virtual environment')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip running the data analysis')
    parser.add_argument('--skip-dashboard', action='store_true', help='Skip generating the dashboard')
    parser.add_argument('--open-browser', action='store_true', help='Open the dashboard in a web browser')
    
    args = parser.parse_args()
    
    print("\n===== Store Performance Visualization System Setup =====\n")
    
    # Check Python version
    check_python_version()
    
    # Create project structure
    create_project_structure()
    
    # Check for required data files
    data_files_ok = check_data_files()
    
    # Set up virtual environment
    setup_virtual_environment(args.env_name)
    
    # Install requirements
    install_requirements(args.env_name)
    
    # Run analysis if data files are present and not skipped
    analysis_ok = True
    if data_files_ok and not args.skip_analysis:
        analysis_ok = run_analysis(args.env_name)
    elif not data_files_ok:
        print("Skipping analysis due to missing data files.")
    elif args.skip_analysis:
        print("Skipping analysis as requested.")
    
    # Generate dashboard if analysis succeeded and not skipped
    dashboard_ok = True
    if analysis_ok and not args.skip_dashboard:
        dashboard_ok = generate_dashboard(args.env_name)
    elif not analysis_ok:
        print("Skipping dashboard generation due to analysis failure.")
    elif args.skip_dashboard:
        print("Skipping dashboard generation as requested.")
    
    # Open dashboard in browser if requested and dashboard was generated
    if args.open_browser and dashboard_ok:
        open_dashboard()
    
    print("\n===== Setup Completed =====\n")
    
    # Print next steps
    if not data_files_ok:
        print("Next steps:")
        print("1. Add your data files to the 'data' directory")
        print("2. Add the 'mexico_estados.geojson' file to the 'data' directory")
        print("3. Run 'python main.py' to process the data")
        print("4. Run 'python -c \"from src import data_processing; from dashboard_generator import generate_dashboard; monthly_data, combined_df = data_processing.load_multiple_months('data'); generate_dashboard(monthly_data, combined_df, 'dashboard')\"' to generate the dashboard")
    elif dashboard_ok:
        print("Your visualization system is ready!")
        print(f"To view the dashboard, open 'dashboard/index.html' in your web browser")
        if not args.open_browser:
            print("Or run 'python setup.py --open-browser' to open it now")

if __name__ == "__main__":
    main()