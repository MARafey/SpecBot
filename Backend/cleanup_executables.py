#!/usr/bin/env python3
"""
Utility script to manage and clean up executable files in the Specbot backend.
This script helps maintain code clarity by organizing and cleaning executable files.
"""

import os
import glob
import shutil
import argparse
from datetime import datetime


def create_executables_dir():
    """Create the executables directory if it doesn't exist."""
    if not os.path.exists("executables"):
        os.makedirs("executables")
        print("✅ Created 'executables' directory")
    else:
        print("📁 'executables' directory already exists")


def clean_executables():
    """Remove all files from the executables directory."""
    if not os.path.exists("executables"):
        print("📁 'executables' directory doesn't exist, nothing to clean")
        return
    
    files_removed = 0
    try:
        for filename in os.listdir("executables"):
            file_path = os.path.join("executables", filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"🗑️  Removed: {file_path}")
                files_removed += 1
        
        print(f"✅ Cleaned up {files_removed} files from executables directory")
    except Exception as e:
        print(f"❌ Error cleaning executables directory: {e}")


def clean_temp_files():
    """Remove temporary C++ files from the main directory."""
    patterns = ["*.cpp", "*.out.*", "output_file*"]
    files_removed = 0
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                print(f"🗑️  Removed temp file: {file}")
                files_removed += 1
            except Exception as e:
                print(f"❌ Error removing {file}: {e}")
    
    print(f"✅ Cleaned up {files_removed} temporary files")


def list_executables():
    """List all files in the executables directory."""
    if not os.path.exists("executables"):
        print("📁 'executables' directory doesn't exist")
        return
    
    files = os.listdir("executables")
    if not files:
        print("📁 'executables' directory is empty")
        return
    
    print(f"📁 Files in 'executables' directory ({len(files)} files):")
    for file in sorted(files):
        file_path = os.path.join("executables", file)
        size = os.path.getsize(file_path)
        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"   📄 {file} ({size} bytes, modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})")


def clean_all():
    """Clean both executables directory and temporary files."""
    print("🧹 Starting comprehensive cleanup...")
    clean_executables()
    clean_temp_files()
    print("✅ Comprehensive cleanup completed")


def main():
    parser = argparse.ArgumentParser(
        description="Manage executable files in Specbot backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_executables.py --clean        # Clean executables directory
  python cleanup_executables.py --list         # List files in executables directory
  python cleanup_executables.py --clean-all    # Clean everything
  python cleanup_executables.py --create       # Create executables directory
        """
    )
    
    parser.add_argument("--clean", action="store_true", 
                       help="Clean all files from executables directory")
    parser.add_argument("--clean-temp", action="store_true", 
                       help="Clean temporary files from main directory")
    parser.add_argument("--clean-all", action="store_true", 
                       help="Clean both executables and temporary files")
    parser.add_argument("--list", action="store_true", 
                       help="List files in executables directory")
    parser.add_argument("--create", action="store_true", 
                       help="Create executables directory if it doesn't exist")
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if args.create:
        create_executables_dir()
    elif args.clean:
        clean_executables()
    elif args.clean_temp:
        clean_temp_files()
    elif args.clean_all:
        clean_all()
    elif args.list:
        list_executables()
    else:
        # Default action if no arguments provided
        print("🔍 Checking executables directory status...")
        list_executables()
        print("\nUse --help for available options")


if __name__ == "__main__":
    main() 