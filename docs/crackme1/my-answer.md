# CrackMe by Fereter #1 — Writeup

> **Sumber:** [crackmes.one/crackme/5ab77f5633c5d40ad448c2cb](https://crackmes.one/crackme/5ab77f5633c5d40ad448c2cb)
> **Penulis crackme:** fereter (diimpor dari crackmes.de)
> **Platform:** Windows (PE32, GUI), x86
> **Bahasa:** Assembly (ditulis tangan, bukan hasil kompilasi bahasa tingkat tinggi)
> **Ukuran:** 3.584 byte
> **Tingkat kesulitan:** 2.0 / 6

## Daftar Isi

- [Ringkasan](#ringkasan)
- [Tools yang digunakan](#tools-yang-digunakan)
- [1. Identifikasi File](#1-identifikasi-file)
- [2. Import Table](#2-import-table)
- [3. Alur Program](#3-alur-program)
- [4. Mekanisme Proteksi](#4-mekanisme-proteksi)
- [5. Logika Validasi Inti](#5-logika-validasi-inti)
- [6. Solusi](#6-solusi)
- [7. Catatan Verifikasi](#7-catatan-verifikasi)

## Ringkasan

CrackMe ini menampilkan window kecil dengan satu **kotak input angka** dan tombol **Check**.
Tujuannya: menemukan nilai yang membuat program menampilkan pesan **"Correct numner."**
(typo "numner" memang sengaja ada di binary aslinya) alih-alih **"Incorrect number."**

Hasil akhir: kode yang valid adalah **`8294810`**.

## Tools yang digunakan

Semua analisis dilakukan secara *static analysis* (tanpa debugger/emulator Windows):

| Tool | Kegunaan |
|---|---|
| `file` | Identifikasi tipe file |
| `strings` | Ekstrak string tercetak dari binary |
| `objdump -d -M intel` | Disassembly x86 (Intel syntax) |
| `objdump -h` | Section headers (mapping VA ↔ file offset) |
| `objdump -p` | Import table (IAT) |
| `od -A x -t x1z` | Hex dump manual untuk verifikasi alamat string byte-per-byte |

## 1. Identifikasi File

```
crackme.EXE: PE32 executable (GUI) Intel 80386, for MS Windows, 4 sections
```

Section layout:

| Section | VMA | Size | Keterangan |
|---|---|---|---|
| `.data` | 0x401000 | 0x85 | String literals |
| `.data?` | 0x402000 | 0x78 | Buffer global (uninitialized) |
| `.code` | 0x403000 | 0x2F0 | Kode program |
| `.idata` | 0x404000 | 0x20C | Import table |

String penting yang ditemukan di `.data` (diverifikasi lewat hex dump, bukan sekadar `strings`):

| Alamat | String |
|---|---|
| `0x401000` | `GetNumberClass` (nama window class) |
| `0x40100F` | `CrackMe by Fereter` (judul window / caption MessageBox) |
| `0x401022` | `edit` |
| `0x401027` | `button` |
| `0x40102E` | `Check` |
| `0x401034` | `Error.` (pesan error inisialisasi window, bukan bagian dari cek serial) |
| `0x40103B` | `Incorrect number.` |
| `0x40104D` | `Correct numner.` ← pesan sukses |

## 2. Import Table

Fungsi WinAPI yang dipakai (dari `KERNEL32.DLL` dan `USER32.DLL`):

```
ExitProcess, GetModuleHandleA, IsDebuggerPresent
CreateWindowExA, DefWindowProcA, DispatchMessageA, GetDlgItemInt,
GetDlgItemTextA, GetMessageA, LoadCursorA, LoadIconA, MessageBoxA,
PostQuitMessage, RegisterClassA, SendMessageA, SetFocus, TranslateMessage
```

Alamat IAT (First Thunk RVA `0x40EC` untuk USER32) dipetakan manual ke tiap fungsi
untuk membaca `call DWORD PTR ds:0x4040xx` di disassembly sebagai nama API, bukan alamat mentah.

## 3. Alur Program

1. **WinMain** (`0x403010`): `RegisterClassA` → `CreateWindowExA` (window utama, kelas `GetNumberClass`) → message loop (`GetMessageA` / `TranslateMessage` / `DispatchMessageA`).
2. **WndProc** (`0x4030E7`) menangani 3 pesan:
   - `WM_CREATE` (1) → buat **Edit control** (id `100`, dibatasi 8 karakter via `EM_LIMITTEXT`) dan **Button "Check"** (id `101`).
   - `WM_COMMAND` (0x111) → hanya diproses jika sumbernya tombol id `101` (Check).
   - `WM_DESTROY` (2) → `PostQuitMessage`.

Saat tombol **Check** diklik:

```
GetDlgItemInt(hWnd, 100, &translated, TRUE)   ; hanya untuk cek "apakah input berupa angka valid?"
  → jika translated != 1  → tampilkan "Incorrect number."
GetDlgItemTextA(hWnd, 100, buffer@0x402028, 16) ; ambil teks asli untuk dicocokkan
```

## 4. Mekanisme Proteksi

CrackMe ini punya 3 lapis anti-debug/anti-patch, semuanya **tidak aktif kalau dijalankan normal**:

1. **`IsDebuggerPresent()`** — dipanggil di message loop utama, hasilnya dipakai di jalur kode yang praktis tidak pernah tereksekusi dalam kondisi normal (lebih ke umpan).
2. **Timing check via `RDTSC` (2×)** — mengukur selisih siklus CPU antara dua `rdtsc` berurutan. Jika selisih > `0x100` (256 cycle) → dianggap sedang di-*single-step* debugger → lompat ke kode "sampah" di akhir fungsi.
3. **Self-scan anti-patch** — program membaca byte kode di sekitar instruksi `jne` (jalur gagal) untuk mencari `0xCC` (breakpoint `INT3`) atau `0x90` (`NOP`). Jika salah satu jenis byte itu ditemukan (indikasi seseorang men-*patch* lompatan supaya selalu "berhasil"), program dialihkan ke kode jebakan.

## 5. Logika Validasi Inti

Alamat `0x402028` menyimpan hasil `GetDlgItemTextA` (string asli dari input, hingga 16 byte).
Cek dilakukan per-4-byte (dword) dengan trik immediate value yang di-`inc` untuk sedikit menyamarkan konstantanya:

```asm
40321a: mov  eax, [0x402028]      ; 4 karakter pertama input
40321f: mov  ecx, 0x34393237
403224: inc  ecx                  ; ecx = 0x34393238 -> byte LE = "8294"
403225: cmp  eax, ecx
403227: jne  fail                 ; 4 karakter pertama harus = "8294"

40322a: mov  eax, [0x40202c]      ; karakter ke-5,6,7,8 input
40322f: mov  ecx, 0x00303138      ; byte LE = '8','1','0','\0'
        ... (self-scan anti-patch di sini) ...
40328d: cmp  eax, ecx
40328f: jne  fail                 ; karakter 5-7 harus "810", karakter ke-8 harus terminator null
```

Karena dword kedua diakhiri byte null (`0x00`) di posisi ke-8, panjang string **harus tepat 7 karakter**:

```
index:   0 1 2 3 4 5 6
char:    8 2 9 4 8 1 0
```

Jika lolos kedua perbandingan + lolos anti-tamper scan + lolos timing check kedua →
`MessageBoxA(hWnd, "Correct numner.", "CrackMe by Fereter", MB_OK)`.

## 6. Solusi

Masukkan angka berikut ke kotak input, lalu klik **Check**:

```
8294810
```

## 7. Catatan Verifikasi

Analisis ini murni *static* (disassembly + hex dump manual untuk cross-check setiap alamat string dan konstanta), tanpa menjalankan biner di Windows/Wine. Nilai `"8294810"` valid secara numerik (lolos `GetDlgItemInt`) dan konsisten dengan kedua perbandingan dword di atas. Disarankan untuk mengonfirmasi langsung di mesin Windows/Wine sungguhan.

---

*Writeup ini dibuat untuk tujuan edukasi reverse engineering pada binary crackme yang memang didistribusikan secara terbuka untuk latihan di [crackmes.one](https://crackmes.one).*
