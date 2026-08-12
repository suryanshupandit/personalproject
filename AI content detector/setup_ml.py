#!/usr/bin/env python3
"""
Setup script for AI Content Detector with ML models
Installs dependencies and preloads ML models for better startup performance
"""

import sys
import subprocess
import os

def install_dependencies():
    """Install required Python packages"""
    print("=" * 60)
    print("AI Content Detector - ML Setup")
    print("=" * 60)
    
    requirements_file = os.path.join(os.path.dirname(__file__), 'backend', 'requirements.txt')
    
    print(f"\n📦 Installing dependencies from {requirements_file}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
        print("✓ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    
    return True

def preload_ml_models():
    """Preload ML models for faster startup"""
    print("\n🤖 Preloading ML models...")
    try:
        from backend.analyzer.ml_models import preload_models
        preload_models()
        print("✓ ML models loaded successfully!")
    except Exception as e:
        print(f"⚠ Note: ML models not available yet. Will use heuristics only.")
        print(f"  Error: {e}")
    
    return True

def main():
    print("\n🚀 Initializing AI Content Detector with ML capabilities...\n")
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed. Please install dependencies manually:")
        print(f"   pip install -r backend/requirements.txt")
        return False
    
    # Preload models
    preload_ml_models()
    
    print("\n" + "=" * 60)
    print("✓ Setup complete! You can now run the application")
    print("=" * 60)
    print("\nTo start the application:")
    print("  cd backend")
    print("  python app.py")
    print("\nOr from the project root:")
    print("  python app.py")
    print("\nThe detector uses:")
    print("  ✓ Machine Learning models for text detection")
    print("  ✓ Advanced feature extraction for image analysis")
    print("  ✓ Heuristic analysis for robust predictions")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
