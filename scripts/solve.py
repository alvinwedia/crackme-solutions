#!/usr/bin/env python3

"""
Script Solve / Keygen untuk [Nama Crackme]
Dibuat untuk mempermudah generasi password berdasarkan username.
"""

def generate_key(username):
    """
    Fungsi ini mereplikasi algoritma yang ditemukan saat analisis statis.
    Berdasarkan Ghidra, setiap huruf pada username di-XOR dengan angka 0x1F.
    """
    print(f"[*] Menghitung key untuk username: {username}")
    
    key = ""
    for char in username:
        # Replikasi logika XOR dari assembly program
        xor_val = ord(char) ^ 0x1F
        key += chr(xor_val)
        
    return key

if __name__ == "__main__":
    print("=== Keygen Sederhana ===")
    user_input = input("Masukkan Username: ")
    
    if len(user_input) < 4:
        print("[!] Error: Username minimal 4 karakter.")
    else:
        final_key = generate_key(user_input)
        print(f"[+] Key berhasil didapatkan: {final_key}")
        print("========================")
