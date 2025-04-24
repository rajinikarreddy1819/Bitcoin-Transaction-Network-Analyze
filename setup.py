import subprocess
import os
import sys
import platform

def check_python_version():
    """Check if Python version is 3.7 or higher."""
    required_version = (3, 7)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required.")
        print(f"Current version: {current_version[0]}.{current_version[1]}.")
        sys.exit(1)
    
    print(f"Python version check passed: {current_version[0]}.{current_version[1]}")

def create_virtual_environment():
    """Create a virtual environment."""
    if os.path.exists('venv'):
        print("Virtual environment already exists.")
        return
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError:
        print("Error creating virtual environment.")
        sys.exit(1)

def install_dependencies():
    """Install dependencies from requirements.txt."""
    venv_pip = os.path.join('venv', 'Scripts', 'pip') if platform.system() == 'Windows' else os.path.join('venv', 'bin', 'pip')
    
    try:
        subprocess.run([venv_pip, "install", "--upgrade", "pip"], check=True)
        subprocess.run([venv_pip, "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("Error installing dependencies.")
        sys.exit(1)

def create_data_directory():
    """Create data directory if it doesn't exist."""
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Data directory created.")
    else:
        print("Data directory already exists.")

def generate_sample_data():
    """Generate sample Bitcoin transaction data."""
    venv_python = os.path.join('venv', 'Scripts', 'python') if platform.system() == 'Windows' else os.path.join('venv', 'bin', 'python')
    
    try:
        subprocess.run([venv_python, "generate_sample_data.py"], check=True)
        print("Sample data generated successfully.")
    except subprocess.CalledProcessError:
        print("Error generating sample data.")
        sys.exit(1)

def setup():
    """Run the setup process."""
    print("===== Setting up Bitcoin Transaction Network Analyzer =====")
    
    check_python_version()
    create_virtual_environment()
    install_dependencies()
    create_data_directory()
    generate_sample_data()
    
    print("\nSetup completed successfully!")
    print("\nTo run the application:")
    
    if platform.system() == 'Windows':
        print("1. Double-click on run.bat")
        print("   OR")
        print("2. Open command prompt and run:")
        print("   venv\\Scripts\\python run.py")
    else:
        print("1. Run: source venv/bin/activate")
        print("2. Then: python run.py")
    
    print("\nThen open your web browser to: http://127.0.0.1:5000/")

if __name__ == "__main__":
    setup() 