def calAmt(qty, rate=100):
    amt = qty * rate
    print(amt)

calAmt(4)
calAmt(5,200)

print("------------------")

def calAnyNums(*args):
    sum = 0
    for num in args:
        sum = sum + num
    print(sum)

calAnyNums(2, 3)
calAnyNums(2, 3, 5, 9)