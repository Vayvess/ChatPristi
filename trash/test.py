def testing(n):
    if n < 1:
        return None
    
    while n > 0:
        yield n
        n -= 1
    return None

for x in testing(-8):
    print(x)