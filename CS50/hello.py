try:
    x = int(input("Please enter a number: "))
    print(f"You entered: {x}")
except ValueError:
    print("That's not a valid number. Please try again.")