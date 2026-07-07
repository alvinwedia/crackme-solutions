# 👾 crackme-solutions

> Kumpulan tulisan dan solusi *crackme* (mayoritas level *Easy*).  
> Repositori ini dibuat sebagai bagian dari portofolio dan catatan perjalanan saya dalam belajar *Reverse Engineering* (RE).

---

## 📖 Deskripsi Singkat
Repositori ini berisi arsip file *crackme* yang telah saya selesaikan beserta analisis langkah demi langkahnya. Tujuan utama repositori ini adalah untuk mendokumentasikan pemahaman saya terhadap cara kerja perangkat lunak di tingkat *assembly* dan mempraktikkan pembuatan *keygen*.

## 🧠 Status Kemampuan Saat Ini
Karena repositori ini adalah tempat belajar, berikut adalah gambaran jujur mengenai *skill set* saya saat ini:
* **Sudah dipelajari:** Membaca instruksi x86 assembly dasar, memahami alur percabangan (jumps), dan mencari nilai *hardcoded password* di memori.
* **Belum dikuasai:** Teknik *anti-debug bypass*, *obfuscation* tingkat lanjut.

## 🛠️ Tools yang Dipakai
Berikut adalah alat-alat yang saya gunakan untuk membedah *crackme* di repositori ini. Pastikan Anda menggunakan versi yang mirip jika ingin mereproduksi hasil analisis:
* **Ghidra (v11.x):** Sebagai *disassembler* dan *decompiler* utama untuk analisis statis.
* **x64dbg / x32dbg:** Sebagai *debugger* dinamis untuk melacak nilai register saat program berjalan.
* **Python 3:** Digunakan untuk menulis skrip *keygen* atau otomasi ekstraksi data.
