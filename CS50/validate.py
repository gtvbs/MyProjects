import re

mail = input("Whats your email?").strip()

if re.search("@", mail):
    print("Valid")

else : 
    print("invalid")    