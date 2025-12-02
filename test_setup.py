#!/usr/bin/env python3
"""
Quick setup validation script
Tests that all dependencies and configurations are correct before running the ETL pipeline
"""

import sys
import os


def test_python_version():
    """Check Python version is 3.9+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required. Found:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def test_imports():
    """Check all required packages are installed"""
    required_packages = {
        'psycopg2': 'psycopg2-binary',
        'pandas': 'pandas',
        'requests': 'requests',
        'dotenv': 'python-dotenv',
        'fuzzywuzzy': 'fuzzywuzzy',
    }

    all_ok = True
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - run: pip install {package}")
            all_ok = False

    return all_ok


def test_env_file():
    """Check .env file exists"""
    if os.path.exists('.env'):
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file not found - run: cp .env.example .env")
        return False


def test_database_config():
    """Check database configuration"""
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    all_ok = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            display_value = '****' if var == 'DB_PASSWORD' else value
            print(f"✅ {var}={display_value}")
        else:
            print(f"❌ {var} not set in .env")
            all_ok = False

    return all_ok


def test_database_connection():
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()

        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n   Start PostgreSQL with:")
        print("   docker run --name gridcare-postgres -e POSTGRES_PASSWORD=postgres \\")
        print("     -p 5432:5432 -d postgres:14")
        return False


def test_data_files():
    """Check required data files exist"""
    required_files = {
        'data/sample_data.json': 'Mock data',
        'sql/schema.sql': 'Database schema',
    }

    all_ok = True
    for filepath, description in required_files.items():
        if os.path.exists(filepath):
            print(f"✅ {description}: {filepath}")
        else:
            print(f"❌ {description} not found: {filepath}")
            all_ok = False

    return all_ok


def main():
    """Run all tests"""
    print("=" * 70)
    print("GridCARE ETL Pipeline - Setup Validation")
    print("=" * 70)
    print()

    tests = [
        ("Python Version", test_python_version),
        ("Python Packages", test_imports),
        ("Environment File", test_env_file),
        ("Database Config", test_database_config),
        ("Data Files", test_data_files),
        ("Database Connection", test_database_connection),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((name, False))

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    all_passed = all(result for _, result in results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    if all_passed:
        print("🎉 All tests passed! You're ready to run: python main.py")
        return 0
    else:
        print("⚠️  Some tests failed. Fix the issues above before running the ETL pipeline.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
