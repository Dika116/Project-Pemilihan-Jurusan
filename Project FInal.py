import tkinter as tk
import customtkinter as ctk
import json
from tkinter import messagebox, ttk
import os

# Set appearance mode dan color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class NodeTrie:
    def __init__(self):
        self.anak = {} 
        self.adalah_akhir_kata = False  
        self.data_jurusan = []  

class TriePencarian:
   
    def __init__(self):
        self.akar = NodeTrie()
    
    def masukkan_kata(self, kata, data_jurusan):
        node_saat_ini = self.akar
        kata = kata.lower().strip()
        
        for karakter in kata:
            if karakter not in node_saat_ini.anak:
                node_saat_ini.anak[karakter] = NodeTrie()
            node_saat_ini = node_saat_ini.anak[karakter]
        
        node_saat_ini.adalah_akhir_kata = True
        node_saat_ini.data_jurusan.append(data_jurusan)
    
    def buat_trie_dari_data(self, data_jurusan):
        for item in data_jurusan:
            # Masukkan berdasarkan nama jurusan
            self.masukkan_kata(item["jurusan"], item)
            
            # Masukkan juga berdasarkan kata-kata dalam jurusan (untuk pencarian substring)
            kata_kata = item["jurusan"].lower().split()
            for kata in kata_kata:
                self.masukkan_kata(kata, item)
            
            # Masukkan berdasarkan nama kampus
            self.masukkan_kata(item["kampus"], item)
            kata_kampus = item["kampus"].lower().split()
            for kata in kata_kampus:
                self.masukkan_kata(kata, item)
    
    def cari_dengan_awalan(self, awalan):
        """Mencari semua kata yang dimulai dengan awalan tertentu"""
        node_saat_ini = self.akar
        awalan = awalan.lower().strip()
        
        # Navigasi ke node yang sesuai dengan awalan
        for karakter in awalan:
            if karakter not in node_saat_ini.anak:
                return []  # Awalan tidak ditemukan
            node_saat_ini = node_saat_ini.anak[karakter]
        
        # Kumpulkan semua hasil dari node ini ke bawah
        hasil = []
        self._kumpulkan_semua_hasil(node_saat_ini, hasil)
        return hasil
    
    def _kumpulkan_semua_hasil(self, node, hasil):
        """Mengumpulkan semua data jurusan dari node dan anak-anaknya"""
        if node.adalah_akhir_kata:
            hasil.extend(node.data_jurusan)
        
        for anak in node.anak.values():
            self._kumpulkan_semua_hasil(anak, hasil)
    
    def cari_substring(self, substring):
        """Mencari semua jurusan yang mengandung substring"""
        substring = substring.lower().strip()
        if not substring:
            return []
        
        hasil = []
        self._cari_substring_rekursif(self.akar, substring, "", hasil)
        
        # Hapus duplikat berdasarkan kombinasi jurusan dan kampus
        hasil_unik = []
        seen = set()
        for item in hasil:
            kunci = (item["jurusan"], item["kampus"])
            if kunci not in seen:
                seen.add(kunci)
                hasil_unik.append(item)
        
        return hasil_unik
    
    def _cari_substring_rekursif(self, node, substring, kata_saat_ini, hasil):
        # Jika kata saat ini mengandung substring yang dicari
        if substring in kata_saat_ini and node.adalah_akhir_kata:
            hasil.extend(node.data_jurusan)
        
        # Lanjutkan pencarian ke anak-anak
        for karakter, anak in node.anak.items():
            self._cari_substring_rekursif(anak, substring, kata_saat_ini + karakter, hasil)

class Node:
    def __init__(self, label=None, left=None, right=None, result=None):
        self.label = label
        self.left = left
        self.right = right
        self.result = result
    
    def is_leaf(self):
        return self.result is not None

class CollegeRecommendationGUI:
    def __init__(self):
        self.jalur_keputusan = []
        self.pohon_keputusan = self.muat_pohon_dari_json()
        self.data_jurusan = self.muat_data_jurusan()
        
        # Inisialisasi Trie untuk pencarian cepat
        self.trie_pencarian = TriePencarian()
        self.trie_pencarian.buat_trie_dari_data(self.data_jurusan)
        
        # Setup main window
        self.root = ctk.CTk()
        self.root.title("Sistem Rekomendasi Jurusan Kuliah dengan Pencarian Trie")
        self.center_window()
        
        self.buat_widget()
    
    def muat_pohon_dari_json(self):
        """Load pohon keputusan dari file JSON"""
        try:
            with open("tree_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return self.bangun_pohon_dari_dict(data["root"])
        except:
            return None
    
    def bangun_pohon_dari_dict(self, data):
        """Membangun node tree dari dictionary"""
        if "result" in data:
            return Node(result=data["result"])
        
        node = Node(label=data["label"])
        node.condition_type = data.get("condition_type")
        node.value = data.get("value")
        node.threshold = data.get("threshold")
        node.subject = data.get("subject")
        node.subjects = data.get("subjects")
        
        if "left" in data:
            node.left = self.bangun_pohon_dari_dict(data["left"])
        if "right" in data:
            node.right = self.bangun_pohon_dari_dict(data["right"])
        
        return node
    
    def muat_data_jurusan(self):
        """Load data jurusan dari file JSON"""
        try:
            with open("jurusan_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def buat_widget(self):
        """Membuat widget GUI"""
        # Header
        header_frame = ctk.CTkFrame(self.root)
        header_frame.pack(fill="x", pady=10, padx=20)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🎓 SISTEM REKOMENDASI JURUSAN KULIAH DENGAN TRIE SEARCH", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=15)
        
        # Notebook untuk tab
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.buat_tab_rekomendasi()
        self.buat_tab_pencarian()


    def buat_tab_rekomendasi(self):
        """Membuat tab rekomendasi"""
        self.tab1 = self.notebook.add("🔍 Rekomendasi Jurusan")
        
        # Buat container utama untuk form input
        self.container_input = ctk.CTkFrame(self.tab1)
        self.container_input.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Scrollable frame untuk input
        self.scroll_frame = ctk.CTkScrollableFrame(self.container_input)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.buat_form_input()
    
    def buat_form_input(self):
        """Membuat form input yang dapat dibersihkan"""
        # Input fields
        input_frame = ctk.CTkFrame(self.scroll_frame)
        input_frame.pack(fill="x", pady=10)
        
        # Nama
        ctk.CTkLabel(input_frame, text="👤 Nama:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.entry_nama = ctk.CTkEntry(input_frame, width=300)
        self.entry_nama.grid(row=0, column=1, padx=10, pady=5)
        
        # Sekolah
        ctk.CTkLabel(input_frame, text="🏫 Sekolah:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.entry_sekolah = ctk.CTkEntry(input_frame, width=300)
        self.entry_sekolah.grid(row=1, column=1, padx=10, pady=5)
        
        # Minat
        ctk.CTkLabel(input_frame, text="💡 Minat Utama:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.combo_minat = ctk.CTkComboBox(input_frame, values=["Teknologi", "Sains", "Kesehatan", "Sosial", "Ekonomi", "Seni", "Bahasa"], width=300)
        self.combo_minat.grid(row=2, column=1, padx=10, pady=5)
        
        # Nilai
        nilai_frame = ctk.CTkFrame(self.scroll_frame)
        nilai_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(nilai_frame, text="📊 NILAI AKADEMIK (0-100)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        nilai_grid = ctk.CTkFrame(nilai_frame)
        nilai_grid.pack(pady=10)
        
        # Grid nilai
        mata_pelajaran = [("📐 Matematika:", "matematika"), ("🧪 IPA:", "ipa"), ("📚 Bahasa:", "bahasa"), ("🎨 Seni:", "seni")]
        self.entry_nilai = {}
        
        for i, (label, key) in enumerate(mata_pelajaran):
            row = i // 2
            col = (i % 2) * 2
            
            ctk.CTkLabel(nilai_grid, text=label, font=ctk.CTkFont(size=14, weight="bold")).grid(row=row, column=col, sticky="w", padx=10, pady=5)
            entry = ctk.CTkEntry(nilai_grid, width=100)
            entry.grid(row=row, column=col+1, padx=10, pady=5)
            self.entry_nilai[key] = entry
        
        # Karier
        karier_frame = ctk.CTkFrame(self.scroll_frame)
        karier_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(karier_frame, text="💼 Karier Impian:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        pilihan_karier = ["Programmer", "Dokter", "Psikolog", "Guru", "Manager", "Akuntan", 
                        "Engineer", "Peneliti", "Seniman", "Content Creator", "Diplomat", "Perawat", "Lainnya"]
        self.combo_karier = ctk.CTkComboBox(karier_frame, values=pilihan_karier, width=400)
        self.combo_karier.pack(padx=10, pady=5)
        
        # Tombol rekomendasi
        tombol_rekomendasi = ctk.CTkButton(
            self.scroll_frame, 
            text="🎯 REKOMENDASIKAN JURUSAN", 
            command=self.rekomendasikan_jurusan,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50
        )
        tombol_rekomendasi.pack(pady=20)

    
    def buat_tab_pencarian(self):
        """Membuat tab pencarian dengan implementasi Trie"""
        tab2 = self.notebook.add("🔎 Pencarian Jurusan")
        
        # Search frame
        frame_pencarian = ctk.CTkFrame(tab2)
        frame_pencarian.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(frame_pencarian, text="🔍 PENCARIAN JURUSAN DENGAN ALGORITMA TRIE", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Input pencarian
        input_frame = ctk.CTkFrame(frame_pencarian)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="🔍 Kata Kunci:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        self.entry_pencarian = ctk.CTkEntry(input_frame, width=300, placeholder_text="Contoh: teknik, informatika,")
        self.entry_pencarian.pack(side="left", padx=10)
        self.entry_pencarian.bind("<KeyRelease>", self.pencarian_real_time)
        
        # Tombol pencarian
        tombol_cari = ctk.CTkButton(input_frame, text="🔍 Cari", command=self.cari_jurusan_trie)
        tombol_cari.pack(side="left", padx=10)
        
        # Filter tambahan
        filter_frame = ctk.CTkFrame(frame_pencarian)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        # Filter by city
        ctk.CTkLabel(filter_frame, text="🏙️ Kota:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        daftar_kota = ["Semua"] + list(set([item["kota"] for item in self.data_jurusan]))
        self.combo_kota = ctk.CTkComboBox(filter_frame, values=daftar_kota, width=150)
        self.combo_kota.grid(row=0, column=1, padx=10, pady=5)
        
        # Filter by akreditasi
        ctk.CTkLabel(filter_frame, text="🏆 Akreditasi:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=2, sticky="w", padx=10, pady=5)
        self.combo_akreditasi = ctk.CTkComboBox(filter_frame, values=["Semua", "A", "B", "C"], width=100)
        self.combo_akreditasi.grid(row=0, column=3, padx=10, pady=5)
        
        # Tombol reset
        tombol_reset = ctk.CTkButton(filter_frame, text="🔄 Reset", command=self.reset_pencarian)
        tombol_reset.grid(row=0, column=4, padx=10, pady=5)
        
        # Label informasi
        self.label_info = ctk.CTkLabel(frame_pencarian, text="💡 Ketik untuk pencarian real-time atau gunakan tombol Cari", 
                                      font=ctk.CTkFont(size=12))
        self.label_info.pack(pady=5)
        
        # Results frame
        frame_hasil = ctk.CTkFrame(tab2)
        frame_hasil.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Treeview for results
        kolom = ("Kota", "Jurusan", "Kampus", "Akreditasi")
        self.tree = ttk.Treeview(frame_hasil, columns=kolom, show="headings", height=15)
        
        for col in kolom:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(frame_hasil, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Load all data initially
        self.tampilkan_semua_data()
    
    def pencarian_real_time(self, event):

        kata_kunci = self.entry_pencarian.get()
        if len(kata_kunci) >= 2: 
            self.cari_jurusan_trie()
        elif kata_kunci == "":
            self.tampilkan_semua_data()
    
    def cari_jurusan_trie(self):

        kata_kunci = self.entry_pencarian.get().strip()
        kota_terpilih = self.combo_kota.get()
        akreditasi_terpilih = self.combo_akreditasi.get()
        
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Jika tidak ada kata kunci, tampilkan semua data dengan filter
        if not kata_kunci:
            data_terfilter = self.data_jurusan
        else:
            # Gunakan Trie untuk pencarian
            data_terfilter = self.trie_pencarian.cari_substring(kata_kunci)
        
        # Apply additional filters
        if kota_terpilih and kota_terpilih != "Semua":
            data_terfilter = [item for item in data_terfilter if item["kota"] == kota_terpilih]
        
        if akreditasi_terpilih and akreditasi_terpilih != "Semua":
            data_terfilter = [item for item in data_terfilter if item["akreditasi"] == akreditasi_terpilih]
        
        # Insert filtered data to treeview
        for item in data_terfilter:
            self.tree.insert("", "end", values=(
                item["kota"], 
                item["jurusan"], 
                item["kampus"], 
                item["akreditasi"]
            ))
        
        # Update info label
        if kata_kunci:
            self.label_info.configure(text=f"🔍 Pencarian '{kata_kunci}': {len(data_terfilter)} hasil ditemukan")
        else:
            self.label_info.configure(text=f"📊 Total: {len(data_terfilter)} hasil")
    
    def reset_pencarian(self):
        """Reset semua filter dan pencarian"""
        self.entry_pencarian.delete(0, "end")
        self.combo_kota.set("Semua")
        self.combo_akreditasi.set("Semua")
        self.tampilkan_semua_data()
    
    def tampilkan_semua_data(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert all data
        for item in self.data_jurusan:
            self.tree.insert("", "end", values=(
                item["kota"], 
                item["jurusan"], 
                item["kampus"], 
                item["akreditasi"]
            ))
        
        self.label_info.configure(text=f"📊 Menampilkan semua data: {len(self.data_jurusan)} jurusan")
    
    def evaluasi_kondisi(self, node, data_user):
        """Evaluasi kondisi berdasarkan data user"""
        try:
            tipe_kondisi = getattr(node, 'condition_type', None)
            
            if tipe_kondisi == "minat_check":
                return data_user['minat'].lower() == node.value.lower()
            
            elif tipe_kondisi == "karier":
                return data_user['karier'].lower() == node.value.lower()
            
            elif tipe_kondisi == "nilai":
                return data_user[f'nilai_{node.subject}'] > node.threshold
            
            elif tipe_kondisi == "combined_nilai":
                total = sum(data_user[f'nilai_{subject}'] for subject in node.subjects)
                return total > node.threshold
            
            else:
                return True
                
        except Exception as e:
            return False
    
    def prediksi_pohon(self, node, data_user):
        """Menelusuri pohon untuk mendapatkan rekomendasi"""
        self.jalur_keputusan = []
        return self._telusuri_pohon(node, data_user)
    
    def _telusuri_pohon(self, node, data_user):
        """Fungsi rekursif untuk menelusuri pohon"""
        if node.is_leaf():
            return node.result
        
        hasil_kondisi = self.evaluasi_kondisi(node, data_user)
        self.jalur_keputusan.append(f"├─ {node.label} → {'✅ YA' if hasil_kondisi else '❌ TIDAK'}")
        
        if hasil_kondisi and node.left:
            return self._telusuri_pohon(node.left, data_user)
        elif not hasil_kondisi and node.right:
            return self._telusuri_pohon(node.right, data_user)
        else:
            return "Jurusan tidak ditemukan"
    
    
    def bersihkan_tab_dan_tampilkan_hasil(self, data_user, rekomendasi, kampus_tersedia=None):
        # Hapus semua widget di container input
        for widget in self.container_input.winfo_children():
            widget.destroy()
        
        # Buat frame untuk hasil
        hasil_frame = ctk.CTkScrollableFrame(self.container_input)
        hasil_frame.pack(fill="both", expand=True, padx=10, pady=10)
        hasil_frame.grid_columnconfigure(0, weight=1)
        
        # Header dengan tombol kembali
        header_frame = ctk.CTkFrame(hasil_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Tombol kembali
        tombol_kembali = ctk.CTkButton(
            header_frame,
            text="⬅️ Kembali ke Form",
            command=self.kembali_ke_form,
            font=ctk.CTkFont(size=12, weight="bold"),
            width=150
        )
        tombol_kembali.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Title
        header_label = ctk.CTkLabel(
            header_frame,
            text="🎓 HASIL REKOMENDASI JURUSAN",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f538d", "#3d8bff")
        )
        header_label.grid(row=0, column=1, pady=15, sticky="ew")
        
        # Info Siswa Frame
        info_frame = ctk.CTkFrame(hasil_frame)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        info_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(info_frame, text="👤 INFORMASI SISWA", 
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=("#2b7a0b", "#5cb85c")).grid(row=0, column=0, columnspan=2, pady=(15, 10), sticky="w", padx=15)
        
        ctk.CTkLabel(info_frame, text="Nama:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(info_frame, text=data_user.get('nama', '-'), font=ctk.CTkFont(size=12)).grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(info_frame, text="🏫 Sekolah:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(info_frame, text=data_user.get('sekolah', '-'), font=ctk.CTkFont(size=12)).grid(row=2, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(info_frame, text="💡 Minat:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=3, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(info_frame, text=data_user.get('minat', '-'), font=ctk.CTkFont(size=12)).grid(row=3, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(info_frame, text="💼 Karier Impian:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=4, column=0, sticky="w", padx=15, pady=(5, 15))
        ctk.CTkLabel(info_frame, text=data_user.get('karier', '-'), font=ctk.CTkFont(size=12)).grid(row=4, column=1, sticky="w", padx=15, pady=(5, 15))
        
        # Nilai Akademik Frame
        nilai_frame = ctk.CTkFrame(hasil_frame)
        nilai_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        nilai_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(nilai_frame, text="📊 NILAI AKADEMIK", 
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=("#8b4513", "#d2691e")).grid(row=0, column=0, columnspan=2, pady=(15, 10), sticky="w", padx=15)
        
        ctk.CTkLabel(nilai_frame, text="📐 Matematika:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(nilai_frame, text=f"{data_user.get('nilai_matematika', 0):.0f}", font=ctk.CTkFont(size=12)).grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(nilai_frame, text="🧪 IPA:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(nilai_frame, text=f"{data_user.get('nilai_ipa', 0):.0f}", font=ctk.CTkFont(size=12)).grid(row=2, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(nilai_frame, text="📚 Bahasa:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=3, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(nilai_frame, text=f"{data_user.get('nilai_bahasa', 0):.0f}", font=ctk.CTkFont(size=12)).grid(row=3, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(nilai_frame, text="🎨 Seni:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=4, column=0, sticky="w", padx=15, pady=(5, 15))
        ctk.CTkLabel(nilai_frame, text=f"{data_user.get('nilai_seni', 0):.0f}", font=ctk.CTkFont(size=12)).grid(row=4, column=1, sticky="w", padx=15, pady=(5, 15))
        
        # Rekomendasi Frame
        rekomendasi_frame = ctk.CTkFrame(hasil_frame)
        rekomendasi_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        rekomendasi_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(rekomendasi_frame, text="🎯 JURUSAN YANG DIREKOMENDASIKAN", 
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=("#d2691e", "#ff8c00")).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        rekomendasi_label = ctk.CTkLabel(
            rekomendasi_frame,
            text=f"✨ {rekomendasi}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#3d8bff"),
            fg_color=("gray90", "gray20"),
            corner_radius=10
        )
        rekomendasi_label.grid(row=1, column=0, pady=(0, 15), padx=15, sticky="ew")
        
        # Kampus Frame
        if kampus_tersedia:
            kampus_frame = ctk.CTkFrame(hasil_frame)
            kampus_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15))
            kampus_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(kampus_frame, text="🏛️ KAMPUS YANG TERSEDIA", 
                        font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=("#8b008b", "#da70d6")).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
            
            kampus_scroll = ctk.CTkScrollableFrame(kampus_frame, height=150)
            kampus_scroll.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
            kampus_scroll.grid_columnconfigure(0, weight=1)
            
            for i, kampus in enumerate(kampus_tersedia[:5]):
                kampus_label = ctk.CTkLabel(
                    kampus_scroll,
                    text=kampus,
                    font=ctk.CTkFont(size=12),
                    anchor="w",
                    justify="left"
                )
                kampus_label.grid(row=i, column=0, sticky="ew", padx=10, pady=2)

    def kembali_ke_form(self):
        """Kembali ke form input"""
        # Hapus semua widget di container
        for widget in self.container_input.winfo_children():
            widget.destroy()
        
        # Buat ulang scroll frame dan form
        self.scroll_frame = ctk.CTkScrollableFrame(self.container_input)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.buat_form_input()

    def rekomendasikan_jurusan(self):

        try:
            # Validasi input
            if not self.entry_nama.get().strip():
                messagebox.showerror("Error", "Nama harus diisi!")
                return
            
            if not self.combo_minat.get():
                messagebox.showerror("Error", "Pilih minat utama!")
                return
            
            if not self.combo_karier.get():
                messagebox.showerror("Error", "Pilih karier impian!")
                return
            
            # Validasi nilai
            data_user = {
                'nama': self.entry_nama.get().strip(),
                'sekolah': self.entry_sekolah.get().strip(),
                'minat': self.combo_minat.get(),
                'karier': self.combo_karier.get()
            }
            
            for mata_pelajaran, entry in self.entry_nilai.items():
                try:
                    nilai = float(entry.get())
                    if not (0 <= nilai <= 100):
                        messagebox.showerror("Error", f"Nilai {mata_pelajaran} harus antara 0-100!")
                        return
                    data_user[f'nilai_{mata_pelajaran}'] = nilai
                except ValueError:
                    messagebox.showerror("Error", f"Nilai {mata_pelajaran} harus berupa angka!")
                    return
            
            # Proses rekomendasi
            if self.pohon_keputusan:
                rekomendasi = self.prediksi_pohon(self.pohon_keputusan, data_user)
                
                # Cari kampus yang memiliki jurusan yang direkomendasikan
                kampus_tersedia = []
                for item in self.data_jurusan:
                    if rekomendasi.lower() in item["jurusan"].lower():
                        kampus_tersedia.append(f"🏛️ {item['kampus']} - {item['kota']} (Akreditasi: {item['akreditasi']})")
                
                # Bersihkan tab dan tampilkan hasil
                self.bersihkan_tab_dan_tampilkan_hasil(data_user, rekomendasi, kampus_tersedia)
            else:
                messagebox.showerror("Error", "Pohon keputusan tidak dapat dimuat!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")
   
    def jalankan(self):
        """Menjalankan aplikasi"""
        self.root.mainloop()

    def center_window(self,):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

# Fungsi untuk menjalankan aplikasi
def main():
    """Fungsi utama untuk menjalankan aplikasi"""
    app = CollegeRecommendationGUI()
    app.jalankan()
    
if __name__ == "__main__":
    main()