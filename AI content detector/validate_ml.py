#!/usr/bin/env python3
"""
Validation script for AI Content Detector ML implementation
Checks that all components are properly installed and working
"""

import sys
import os
import importlib.util
import py_compile

def check_imports():
    """Check if all required packages are installed"""
    print("\n" + "="*60)
    print("Checking Python Dependencies...")
    print("="*60)
    
    required = {
        'flask': 'Flask',
        'PIL': 'Pillow',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'nltk': 'NLTK',
        'sklearn': 'scikit-learn',
        'torch': 'PyTorch',
        'transformers': 'Transformers',
    }
    
    missing = []
    installed = []
    
    for module, name in required.items():
        try:
            # find_spec avoids importing heavy libs (e.g. torch) just to verify installation
            if importlib.util.find_spec(module) is None:
                raise ImportError(module)
            print(f"  [OK] {name:20} installed")
            installed.append(name)
        except ImportError:
            print(f"  [XX] {name:20} MISSING")
            missing.append(name)
    
    print(f"\n{len(installed)}/{len(required)} packages installed")
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: python setup_ml.py")
        return False
    
    return True

def check_files():
    """Check if all required files exist"""
    print("\n" + "="*60)
    print("Checking Project Files...")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    required_files = {
        'backend/app.py': 'Flask backend',
        'backend/analyzer/text_analyzer.py': 'Text analyzer',
        'backend/analyzer/image_analyzer.py': 'Image analyzer',
        'backend/analyzer/ml_models.py': 'ML models utility (NEW)',
        'backend/requirements.txt': 'Dependencies',
        'setup_ml.py': 'ML setup script (NEW)',
        'frontend/index.html': 'Frontend',
        'frontend/main.js': 'Frontend JS',
    }
    
    missing = []
    found = []
    
    for file_path, description in required_files.items():
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"  [OK] {description:30} {file_path}")
            found.append(description)
        else:
            print(f"  [XX] {description:30} {file_path} - MISSING")
            missing.append(file_path)
    
    print(f"\n{len(found)}/{len(required_files)} files found")
    
    if missing:
        print(f"\nMissing files: {', '.join(missing)}")
        return False
    
    return True

def check_ml_models():
    """Check if ML models can be loaded"""
    print("\n" + "="*60)
    print("Checking ML Models...")
    print("="*60)
    
    try:
        # Add backend to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        from analyzer.ml_models import predict_text_ai
        print("  [OK] ML models module imports successfully")
        if callable(predict_text_ai):
            print("  [OK] predict_text_ai() is available")
            print("  [INFO] Full model download/check is deferred to first app use")
            return True
        print("  ✗ predict_text_ai() is not callable")
        return False
            
    except Exception as e:
        print(f"  [XX] ML models error: {e}")
        return False

def check_analyzer_modules():
    """Check if analyzer modules load correctly"""
    print("\n" + "="*60)
    print("Checking Analyzer Modules...")
    print("="*60)
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        from analyzer.text_analyzer import analyze_text
        print("  [OK] Text analyzer module loads")
        
        from analyzer.image_analyzer import analyze_image_bytes
        print("  [OK] Image analyzer module loads")
        
        # Keep test text short to avoid triggering optional ML model downloads
        test_result = analyze_text("Short test.")
        if 'verdict' in test_result:
            print("  [OK] Text analysis produces valid output")
        else:
            print("  [XX] Text analysis output invalid")
            return False
            
        return True
        
    except Exception as e:
        print(f"  [XX] Analyzer module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_flask_app():
    """Check if Flask app source is valid without running startup side effects"""
    print("\n" + "="*60)
    print("Checking Flask Application...")
    print("="*60)
    
    try:
        backend_app_path = os.path.join(os.path.dirname(__file__), 'backend', 'app.py')
        if not os.path.exists(backend_app_path):
            print("  ✗ Flask app file missing")
            return False

        py_compile.compile(backend_app_path, doraise=True)
        print("  [OK] Flask app source compiles successfully")
        return True
        
    except Exception as e:
        print(f"  [XX] Flask app error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_pytorch_gpu():
    """Check if PyTorch can detect CUDA (optional)"""
    print("\n" + "="*60)
    print("Checking PyTorch Configuration...")
    print("="*60)
    
    try:
        import torch
        print(f"  [OK] PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"  [OK] GPU detected: {torch.cuda.get_device_name(0)}")
            print("    (ML will run faster on GPU)")
        else:
            print("  [INFO] GPU not detected (using CPU is fine)")
        
        return True
        
    except BaseException as e:
        print(f"  [WARNING] PyTorch check failed: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("AI Content Detector - ML Implementation Validation")
    print("="*60)
    
    results = []
    
    # Run all checks
    results.append(("Dependencies", check_imports()))
    results.append(("Files", check_files()))
    results.append(("ML Models", check_ml_models()))
    results.append(("Analyzers", check_analyzer_modules()))
    results.append(("Flask App", check_flask_app()))
    
    # Optional checks
    check_pytorch_gpu()
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for component, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] - {component}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n" + "="*60)
        print("[SUCCESS] ALL CHECKS PASSED!")
        print("="*60)
        print("\nYour ML-enabled AI Content Detector is ready!")
        print("\nTo start the application:")
        print("  cd backend")
        print("  python app.py")
        print("\nThen open: http://localhost:5000")
        print("="*60)
        return True
    else:
        print("\n" + "="*60)
        print("[ERROR] SOME CHECKS FAILED")
        print("="*60)
        print("\nTo fix issues:")
        print("  1. Run: python setup_ml.py")
        print("  2. Check error messages above")
        print("  3. Re-run this validation script")
        print("="*60)
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
