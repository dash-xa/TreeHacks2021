import os
with open("data/counter.txt", 'r+') as counterFile:
    i = int(counterFile.read())
    counterFile.seek(0)
    counterFile.write(str(i + 1))
    os.mkdir(f"data/{i}")
    
