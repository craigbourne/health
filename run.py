import subprocess

print("=" * 50)
print("STEP 1: Collecting repo data from GitHub...")
print("=" * 50 + "\n")
result1 = subprocess.run(["python3", "collect.py"])

if result1.returncode == 0:
    print("\n" + "=" * 50)
    print("STEP 2: Classifying repos based on metrics...")
    print("=" * 50 + "\n")
    result2 = subprocess.run(["python3", "classify.py"])
    
    if result2.returncode == 0:
        print("\n" + "=" * 50)
        print("✓ Complete! Data saved to repo_data.json")
        print("=" * 50 + "\n")
    else:
        print("\n✗ Classification failed")
else:
    print("\n✗ Data collection failed")