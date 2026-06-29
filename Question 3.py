import math

lambda_e = 1.0
lambda_i_base = 0.375
lambda_i_amp = 1.5 * math.pi

def lambda_i(h):
    if 9  <= h < 12: return lambda_i_base + lambda_i_amp*math.sin(math.pi*(h-9)/3)
    if 12 <= h < 15: return lambda_i_base + lambda_i_amp*math.sin(math.pi*(h-12)/3)
    return lambda_i_base

def slot_start(n):
    return 8 + (n - 1) * 0.25

def arr(n):
    return (lambda_e + lambda_i(slot_start(n))) * 0.25

for n in range(1, 33):
    h  = slot_start(n)
    li = lambda_i(h)
    arrei = arr(n)
    print(f"slot:{n}, time:{h:.2f}, lambdaI:{li:.4f}, arrival: {arrei:7.4f} ")
