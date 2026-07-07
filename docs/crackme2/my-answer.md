# get the password (by moveax41h) — Writeup

> **Sumber:** [crackmes.one/crackme/5c83501333c5d4776a837df7](https://crackmes.one/crackme/5c83501333c5d4776a837df7)
> **Penulis crackme:** moveax41h
> **Platform:** Windows (PE32, console), x86
> **Bahasa:** C/C++ (dikompilasi dengan MinGW GCC 6.3.0, simbol debug tidak di-strip)
> **Ukuran:** 44,55 KB
> **Tingkat kesulitan:** 2.2 / 6
> **Deskripsi resmi:** *"No nopping… Get the password :)"*

## Daftar Isi

- [Ringkasan](#ringkasan)
- [Tools yang digunakan](#tools-yang-digunakan)
- [1. Identifikasi File](#1-identifikasi-file)
- [2. Alur Program](#2-alur-program)
- [3. Pembuatan Password Acak (`get_pwd`)](#3-pembuatan-password-acak-get_pwd)
- [4. Bug di `check_password`](#4-bug-di-check_password)
- [5. Solusi](#5-solusi)
- [6. Catatan Verifikasi](#6-catatan-verifikasi)

## Ringkasan

Program konsol ini meminta **username** lalu **password**. Berbeda dari crackme pertama,
di sini binary **tidak di-strip** — semua nama fungsi (`main`, `prompt_user`, `check_password`,
`get_pwd`) dan variabel masih ada di symbol table, jadi navigasinya jauh lebih mudah.

Judul crackme-nya sendiri sudah kasih petunjuk: *"No nopping…"* — penulis crackme tampaknya
sudah antisipasi orang akan mencoba menge-*patch* (NOP) instruksi lompatan, tapi ternyata
programnya sendiri punya **bug logika** yang membuatnya bisa ditembus tanpa patch sama sekali.

## Tools yang digunakan

Sama seperti writeup sebelumnya — murni *static analysis* command-line:

| Tool | Kegunaan |
|---|---|
| `file` | Identifikasi tipe file |
| `strings` | Ekstrak string tercetak |
| `objdump -t` | Symbol table (alamat fungsi, karena tidak di-strip) |
| `objdump -d -M intel` | Disassembly x86 (Intel syntax) |
| `objdump -h` / `objdump -s` | Section headers & hex dump `.rdata` untuk verifikasi string |

## 1. Identifikasi File

```
check_pass3.exe: PE32 executable (console) Intel 80386, for MS Windows, 13 sections
```

Dikompilasi dengan **MinGW GCC 6.3.0**. Nama file sumber asli: `check_pass_dynamic.c`.
String penting yang langsung terlihat lewat `strings`:

```
Congrats, you're logged in!
Wrong password.
Enter your username
Now enter your password
check_password: struct user_data is NULL
```

Fungsi kunci (dari symbol table, `objdump -t`):

| Fungsi | Alamat |
|---|---|
| `_main` | `0x401460` |
| `_prompt_user` | `0x4014c4` |
| `_check_password` | `0x401575` |
| `_get_pwd` | `0x4015fc` |

## 2. Alur Program

```
main()
 ├─ user_data = calloc(1, 0x32)          ; alokasi struct (50 byte): username + password
 ├─ prompt_user(user_data)                ; baca username & password via fgets, buang newline
 ├─ check_password(user_data)
 └─ if (check_password(...) == 1)
        printf("Congrats, you're logged in!\n")
    else
        printf("Wrong password.\n")
```

Layout struct `user_data` (offset relatif):

| Offset | Field | Ukuran baca (`fgets`) |
|---|---|---|
| `+0x00` | `username` | 0x13 (19) byte |
| `+0x1e` | `password` | 0x1d (29) byte |

Username **tidak pernah dibandingkan ke apa pun** — hanya password yang divalidasi.

## 3. Pembuatan Password Acak (`get_pwd`)

Ini bagian paling "berat" dari crackme — dan juga sumber bug-nya. `get_pwd()` melakukan:

1. `malloc(7)` → buffer kecil, diisi konstanta **byte-per-byte**:
   ```
   'v', '/', 'm', '0', 's', '3', 0xFF (sentinel akhir)
   ```
2. `malloc(1000)` → buffer besar (`answer`), dipakai sebagai "kanvas" 1000 posisi.
3. `srand(time(NULL))`, lalu `rand() % 1000` dipanggil **6 kali** → menghasilkan 6 indeks acak
   (0–999), disimpan sebagai array 6 `int` di parameter yang diteruskan dari `check_password`.
4. Loop `for i in 0..7`: ambil karakter ke-`i` dari buffer konstanta di langkah 1, **tambah 1**
   (`+1`, semacam Caesar-shift sederhana), lalu tulis hasilnya ke `answer[ index_acak[i] ]`
   menggunakan `switch`/jump-table.

Kalau konstanta `'v','/','m','0','s','3'` masing-masing di-`+1`, hasilnya:

```
v -> w
/ -> 0
m -> n
0 -> 1
s -> t
3 -> 4
```

= password sebenarnya adalah **`w0n1t4`**, tapi 6 karakter ini **disebar di posisi acak**
(berbeda tiap kali program dijalankan, karena seed-nya `time(NULL)`) di dalam buffer 1000 byte.
Ini teknik obfuscation yang cukup rapi — nilai password-nya sendiri deterministik ("w0n1t4"),
tapi *lokasi*-nya di memori berubah-ubah tiap run, supaya tidak bisa langsung dibaca dari
alamat tetap.

## 4. Bug di `check_password`

```asm
4015be: mov  DWORD PTR [ebp-0x10], 0     ; i = 0
4015c5: cmp  DWORD PTR [ebp-0x10], 0x6   ; batas niatnya: loop selama i <= 6
4015c9: ja   4015fa                       ; keluar HANYA jika i > 6

4015cb: mov  edx, [ebp+0x8]               ; user_data
4015d1: add  eax, edx
4015d3: add  eax, 0x1e                    ; -> &password[i]
4015d6: movzx edx, BYTE PTR [eax]         ; edx = password_input[i]

4015dc: mov  ecx, [ebp+eax*4-0x2c]        ; ecx = index_acak[i]
4015e0: mov  eax, [ebp-0xc]               ; eax = base buffer 'answer'
4015e3: add  eax, ecx
4015e5: movzx eax, BYTE PTR [eax]         ; eax = answer[index_acak[i]] = karakter ke-i seharusnya
4015e8: cmp  dl, al
4015ea: je   4015f3                       ; cocok -> return 1
4015ec: mov  eax, 0
4015f1: jmp  4015fa                       ; tidak cocok -> return 0
4015f3: mov  eax, 1
4015f8: jmp  4015fa
4015fa: leave
4015fb: ret
```

Struktur `cmp ... ja ...` di atas **terlihat** seperti setup loop untuk memeriksa 6/7 karakter.
Tapi setelah blok pembanding (`cmp dl,al` → `je`/fallthrough), kode **langsung `return`**
(1 atau 0) — **tidak ada instruksi yang increment `i` dan lompat balik ke `0x4015c5`**.

Akibatnya: fungsi ini **hanya pernah mengeksekusi iterasi `i = 0`**, lalu selalu `return`.
Karakter ke-2 sampai ke-6 dari password **tidak pernah diperiksa sama sekali**.

Karena karakter pertama dari password asli selalu `'w'` (lihat bagian 3, apa pun posisi
acaknya), maka syarat login yang sebenarnya diperiksa cuma:

> **Karakter pertama password yang diketik harus `'w'`.**

Username bebas, dan karakter ke-2 dan seterusnya pada password juga bebas.

## 5. Solusi

- **Username:** bebas, contoh `apa saja`
- **Password:** apa saja yang **diawali huruf `w`** — misalnya cukup ketik:

```
w
```

Password lengkap "asli" yang sebenarnya di-generate program adalah **`w0n1t4`**
(bisa dipakai juga, tetap valid), tapi karena bug di atas, password sesingkat `w` saja
sudah cukup untuk memicu pesan:

```
Congrats, you're logged in!
```

## 6. Catatan Verifikasi

Karena binary ini tidak di-strip, seluruh alamat fungsi dan nama variabel diambil langsung
dari symbol table (bukan tebakan), dan setiap konstanta karakter (`'v','/','m','0','s','3'`)
diverifikasi byte-per-byte dari disassembly `get_pwd`. Temuan ini konsisten dengan beberapa
writeup publik lain untuk crackme yang sama, yang juga melaporkan password asli `w0n1t4`
dan bug "hanya karakter pertama yang dicek" — writeup ini disusun secara independen dari
disassembly binary yang diunggah, lalu dicocokkan ulang untuk memastikan hasilnya konsisten.
Disarankan tetap mengonfirmasi langsung dengan menjalankan binary di Windows/Wine.

---

*Writeup ini dibuat untuk tujuan edukasi reverse engineering pada binary crackme yang memang didistribusikan secara terbuka untuk latihan di [crackmes.one](https://crackmes.one).*
