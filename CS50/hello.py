import sys

if len(sys.argv) < 2:
    sys.exit("Usage: python hello.py <name>")
elif len(sys.argv) > 2:
    sys.exit("Error: Too many arguments provided. Please provide only one name.")
else:
    name = sys.argv[1]
    print(f"Hello, {name}!")