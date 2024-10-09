def clip(val: int, min_: int, max_: int):
    val = max(min_, val)
    val = min(max_, val)
    return val


def sign_extend(val, nbits=24):
    sgn = 1 << (nbits-1)
    return (val & (sgn-1)) - (val & sgn)
