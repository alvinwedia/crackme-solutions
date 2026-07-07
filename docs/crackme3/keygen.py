ALPHABET = "A-CHRDw87lNS0E9B2TibgpnMVys5XzvtOGJcYLU+4mjW6fxqZeF3Qa1rPhdKIouk"
assert len(ALPHABET) == 64

def glibc_rand_seq(seed, n):
    seed &= 0xffffffff
    if seed == 0:
        seed = 1
    r = [0]*344
    r[0] = seed
    for i in range(1, 31):
        hi = r[i-1] // 127773
        lo = r[i-1] % 127773
        word = 16807*lo - 2836*hi
        if word < 0:
            word += 2147483647
        r[i] = word
    for i in range(31, 34):
        r[i] = r[i-31]
    for i in range(34, 344):
        r[i] = (r[i-31] + r[i-3]) & 0xffffffff
    out = []
    idx = 344
    for _ in range(n):
        val = (r[idx-31] + r[idx-3]) & 0xffffffff
        r.append(val)
        out.append(val >> 1)
        idx += 1
    return out

def keygen(pseudo: str) -> str:
    b = pseudo.encode()
    n = len(b)
    if n == 0:
        raise ValueError("pseudo tidak boleh kosong")

    idx0 = ((n & 0xff) ^ 0x3b) & 0x3f

    s = sum(b) & 0xff
    idx1 = (s ^ 0x4f) & 0x3f

    p = 1
    for c in b:
        p = (p * c) & 0xff
    idx2 = (p ^ 0x55) & 0x3f

    max_char = max(b)
    seed = (max_char ^ 0x0e) & 0xff
    count5 = b[0]
    total_calls = 1 + count5
    seq = glibc_rand_seq(seed, total_calls)
    idx3 = seq[0] & 0x3f
    last = seq[total_calls - 1]
    idx5 = ((last & 0xff) ^ 0xe5) & 0x3f

    acc = 0
    for c in b[:-1]:
        acc = (acc + c*c) & 0xff
    idx4 = (acc ^ 0x2f) & 0x3f

    indices = [idx0, idx1, idx2, idx3, idx4, idx5]
    return ''.join(ALPHABET[i] for i in indices)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for name in sys.argv[1:]:
            print(f"{name} -> {keygen(name)}")
    else:
        for name in ["testuser","admin","fereter","abc","x","Claude"]:
            print(f"{name} -> {keygen(name)}")
