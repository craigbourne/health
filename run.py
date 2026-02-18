import subprocess
import sys

print("=" * 60)
print("GitHub Repository Health Data Collection")
print("=" * 60)

print("\nStep 1: Collecting repository data. This may take several minutes...")

result1 = subprocess.run([sys.executable, "collect.py"])

if result1.returncode == 0:
    print("\n" + "=" * 60)
    print("Step 2: Classifying repositories...")
    print("=" * 60)
    result2 = subprocess.run([sys.executable, "classify.py"])
    
    if result2.returncode == 0:
        print("\n" + "=" * 60)
        print("Step 3: Generating report...")
        print("=" * 60)
        result3 = subprocess.run([sys.executable, "report.py"])
        
        if result3.returncode == 0:
            print("\n" + "=" * 60)
            print("✓ Complete!")
            print("=" * 60)
            print("Files created:")
            print("  - repo_data.json (full dataset)")
            print("  - report.md (summary)")
        else:
            print("\n✗ Report generation failed")
    else:
        print("\n✗ Classification failed")
else:
    print("\n✗ Data collection failed")