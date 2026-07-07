# first_keygenme (by twistedtux) — Writeup

> **Sumber:** [crackmes.one/crackme/5ab77f5733c5d40ad448c363](https://crackmes.one/crackme/5ab77f5733c5d40ad448c363)
> **Penulis crackme:** twistedtux (diimpor dari crackmes.de)
> **Platform:** Linux, ELF 32-bit (x86)
> **Bahasa:** C (GCC 4.4.5, Ubuntu/Linaro), dikompilasi statis-dinamis biasa, **di-strip** (tanpa nama fungsi)
> **Jenis:** Keygenme — tujuannya bukan menebak satu password, tapi menemukan **algoritma** yang mengubah *username* menjadi *key* yang valid, lalu menulis **keygen**.

## Daftar Isi

- [Ringkasan](#ringkasan)
- [Tools yang digunakan](#tools-yang-digunakan)
- [1. Identifikasi File](#1-identifikasi-file)
- [2. Alur Program](#2-alur-program)
- [3. Tabel Alphabet (64 karakter)](#3-tabel-alphabet-64-karakter)
- [4. Enam Fungsi Penghasil Karakter Key](#4-enam-fungsi-penghasil-karakter-key)
- [5. Keygen (Python)](#5-keygen-python)
- [6. Catatan Verifikasi](#6-catatan-verifikasi)

## Ringkasan

Program dijalankan lewat command line: `./keygenme <pseudo> <clef>` (bahasa Prancis:
*pseudo* = username, *clef* = key/password). Jika `clef` valid untuk `pseudo` yang diberikan,
program mencetak `Bravo !!`.

`key` harus tepat **6 karakter**, dan tiap karakter diambil dari sebuah **tabel 64 karakter**
custom (mirip base64 tapi urutannya diacak) memakai indeks 0-63 yang dihitung dari 6 fungsi
berbeda — masing-masing menghasilkan 1 karakter key, dari operasi matematis atas byte-byte
`pseudo` (panjang, jumlah, hasil kali, kuadrat, bahkan `rand()` dari libc).

## Tools yang digunakan

| Tool | Kegunaan |
|---|---|
| `file`, `strings` | Identifikasi awal & string tertanam |
| `objdump -d -M intel` | Disassembly (binary di-strip, jadi navigasi murni lewat alamat) |
| `objdump -s -j .data` | Hex dump untuk ekstraksi tabel alphabet & string pesan |
| `gcc` (lokal) | Kompilasi program C kecil untuk **memverifikasi ulang** logika secara independen — termasuk memanggil `srand()`/`rand()` asli dari libc untuk memastikan reimplementasi Python-nya identik bit-per-bit |

## 1. Identifikasi File

```
keygenme: ELF 32-bit LSB executable, Intel 80386, dynamically linked, stripped
```

Pesan penting dari `strings`:

```
Utilisation : %s <pseudo> <clef>
A-CHRDw87lNS0E9B2TibgpnMVys5XzvtOGJcYLU+4mjW6fxqZeF3Qa1rPhdKIouk
Bravo !!
```

## 2. Alur Program

```
main(argc, argv):
    if argc < 3:
        printf("Utilisation : %s <pseudo> <clef>", argv[0]); exit(1)

    pseudo = argv[1]
    clef   = argv[2]

    if strlen(clef) != 6:
        exit(1)

    key_valid = true
    for i in 0..5:
        expected_char = ALPHABET[ f_i(pseudo) ]     # f_i berbeda tiap posisi i
        if clef[i] != expected_char:
            key_valid = false; break

    if key_valid:
        printf("Bravo !!\n")
```

Karena binary **di-strip**, tidak ada nama fungsi — 6 fungsi `f_0..f_5` diidentifikasi lewat
alamat call target-nya di `main` (`0x8048450`), lalu dianalisis satu per satu.

## 3. Tabel Alphabet (64 karakter)

Ditemukan di alamat `0x804a042` (diverifikasi lewat hex dump `.data`, byte demi byte):

```
Index:  0123456789...............................................63
Isi  :  A-CHRDw87lNS0E9B2TibgpnMVys5XzvtOGJcYLU+4mjW6fxqZeF3Qa1rPhdKIouk
```

Tepat 64 karakter — cocok dengan setiap indeks yang selalu di-`AND 0x3F` (0–63) di kode.

## 4. Enam Fungsi Penghasil Karakter Key

Tiap fungsi menghasilkan sebuah **indeks 0–63** ke tabel alphabet di atas. `pseudo` = username
sebagai array byte, `n` = panjang `pseudo`.

| Key | Fungsi | Rumus indeks |
|---|---|---|
| `key[0]` | `f_0(n)` | `(n & 0x3F) XOR 0x3B` |
| `key[1]` | `f_1(pseudo)` | `(sum(pseudo) & 0x3F) XOR 0x0F` |
| `key[2]` | `f_2(pseudo)` | `(product(pseudo) mod 256 & 0x3F) XOR 0x15` |
| `key[3]` | `f_3(pseudo)` | `srand(max(pseudo) XOR 0x0E)`, lalu **rand() pertama** `& 0x3F` |
| `key[4]` | `f_4(pseudo)` | `(sum(pseudo[i]² untuk i=0..n-2) mod 256 & 0x3F) XOR 0x2F` |
| `key[5]` | `f_5(pseudo)` | lanjutkan stream `rand()` dari `f_3` sebanyak `pseudo[0]` kali lagi, ambil **hasil terakhir** `& 0xFF`, XOR `0xE5`, `& 0x3F` |

Detail menarik:

- `key[0]` hanya bergantung pada **panjang** username.
- `key[1]` = jumlah (sum) seluruh byte username.
- `key[2]` = hasil kali (product) seluruh byte username, dipotong ke 1 byte tiap langkah.
- `key[3]` dan `key[5]` **berbagi satu stream `rand()`** dari libc C — penulis crackme sengaja
  memakai PRNG standar (`srand`/`rand`) sebagai bagian dari algoritma, bukan cuma dekorasi.
  Seed-nya deterministik: `karakter terbesar dalam username, XOR 0x0E`.
- `key[4]` = jumlah kuadrat byte-byte username **kecuali byte terakhir**.

Karena `key[3]`/`key[5]` memakai `rand()` asli dari glibc, keygen butuh **reimplementasi PRNG
glibc yang identik** (algoritma `TYPE_3`, deret aditif, standar sejak lama di glibc) — bukan
`rand()` bawaan bahasa lain, yang pasti beda.

## 5. Keygen (Python)

```python
ALPHABET = "A-CHRDw87lNS0E9B2TibgpnMVys5XzvtOGJcYLU+4mjW6fxqZeF3Qa1rPhdKIouk"

def glibc_rand_seq(seed, n):
    """Reimplementasi PRNG glibc (TYPE_3) — deret aditif derajat 31."""
    seed &= 0xffffffff
    if seed == 0:
        seed = 1
    r = [0] * 344
    r[0] = seed
    for i in range(1, 31):
        hi, lo = divmod(r[i - 1], 127773)
        word = 16807 * lo - 2836 * hi
        if word < 0:
            word += 2147483647
        r[i] = word
    for i in range(31, 34):
        r[i] = r[i - 31]
    for i in range(34, 344):
        r[i] = (r[i - 31] + r[i - 3]) & 0xffffffff
    out, idx = [], 344
    for _ in range(n):
        val = (r[idx - 31] + r[idx - 3]) & 0xffffffff
        r.append(val)
        out.append(val >> 1)
        idx += 1
    return out

def keygen(pseudo: str) -> str:
    b = pseudo.encode()
    n = len(b)

    idx0 = ((n & 0xff) ^ 0x3b) & 0x3f

    idx1 = (sum(b) & 0xff ^ 0x4f) & 0x3f

    p = 1
    for c in b:
        p = (p * c) & 0xff
    idx2 = (p ^ 0x55) & 0x3f

    max_char = max(b)
    seed = (max_char ^ 0x0e) & 0xff
    count5 = b[0]
    seq = glibc_rand_seq(seed, 1 + count5)
    idx3 = seq[0] & 0x3f
    idx5 = ((seq[count5] & 0xff) ^ 0xe5) & 0x3f

    acc = 0
    for c in b[:-1]:
        acc = (acc + c * c) & 0xff
    idx4 = (acc ^ 0x2f) & 0x3f

    return ''.join(ALPHABET[i] for i in (idx0, idx1, idx2, idx3, idx4, idx5))

if __name__ == "__main__":
    import sys
    for name in sys.argv[1:]:
        print(f"{name} -> {keygen(name)}")
```

Contoh hasil:

| Username | Key |
|---|---|
| `testuser` | `3ZaGFt` |
| `admin` | `uwE-Ya` |
| `fereter` | `IJaJ6A` |
| `Claude` | `o-DG0s` |

Jalankan: `./keygenme <username> <key_hasil_keygen>` → mencetak `Bravo !!`.

## 6. Catatan Verifikasi

Karena binary ini ELF 32-bit dan sandbox analisis yang dipakai adalah Linux 64-bit tanpa
paket i386 (dan tanpa akses jaringan untuk memasang paket 32-bit), binary aslinya **tidak bisa
dijalankan langsung** untuk verifikasi end-to-end.

Sebagai gantinya, verifikasi dilakukan dengan menerjemahkan ulang logika assembly ke **C**
(dikompilasi native 64-bit) dan membandingkannya dengan formula Python yang disederhanakan:

- `idx0`, `idx1`, `idx2`, `idx4` — versi "mentah" (meniru instruksi mask/xor satu-satu di C)
  dibandingkan dengan versi formula yang disederhanakan di Python → **hasilnya identik** untuk
  semua string uji.
- `idx3`, `idx5` — reimplementasi PRNG glibc di Python dibandingkan dengan pemanggilan
  `srand()`/`rand()` **asli** dari libc lewat program C kecil → **hasilnya identik bit-per-bit**
  untuk berbagai seed.

Dengan kata lain, setiap komponen algoritma sudah diuji silang secara independen terhadap
implementasi C asli (walau bukan biner crackme itu sendiri). Tetap disarankan untuk
mengonfirmasi langsung di mesin Linux x86/i386 (atau lewat `qemu-i386` + pustaka 32-bit) jika
memungkinkan.

---

*Writeup ini dibuat untuk tujuan edukasi reverse engineering pada binary crackme yang memang didistribusikan secara terbuka untuk latihan di [crackmes.one](https://crackmes.one), lengkap dengan keygen yang bisa dijalankan (bukan sekadar satu password statis) sesuai anjuran submission rules situs tersebut.*
