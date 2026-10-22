def main():
    number = int(input("What is the number?"))
    print (f"The squared is {square(number)}")

def square(number):
    return number * number    

if __name__ == "__main__":
    main()