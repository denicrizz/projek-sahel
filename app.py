# Import library yang diperlukan
import streamlit as st
import numpy as np
from datetime import datetime
import os
import time
import math
import cv2

# Resolusi Konstanta
WIDTH = 640
HEIGHT = 480

# Setup page config
st.set_page_config(page_title="Blind Spot Monitor", layout="wide")

# Setup direktori untuk menyimpan gambar
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURED_IMAGES_DIR = os.path.join(BASE_DIR, "captured_images")
os.makedirs(CAPTURED_IMAGES_DIR, exist_ok=True)

def init_session_state():
    """Inisialisasi semua session state yang diperlukan"""
    if 'news_data' not in st.session_state:
        st.session_state.news_data = [
            {
                "title": "Kecelakaan di Jalan A",
                "description": "Mobil menabrak pohon, menyebabkan kemacetan panjang.",
                "time": "10:30",
                "date": "2023-12-17",
                "image": "assets/1.jpeg"
            },
            {
                "title": "Tabrakan Beruntun di Jalan B",
                "description": "Kecelakaan melibatkan 3 mobil dan 1 motor.",
                "time": "14:20",
                "date": "2023-12-18",
                "image": "assets/2.jpg"
            }
        ]
    
    if 'camera_captured' not in st.session_state:
        st.session_state.camera_captured = {
            'Depan': False,
            'Belakang': False,
            'Kanan': False,
            'Kiri': False
        }
    
    if 'captured_images' not in st.session_state:
        st.session_state.captured_images = []
    
    if 'cameras_active' not in st.session_state:
        st.session_state.cameras_active = False
        
    if 'placeholders' not in st.session_state:
        st.session_state.placeholders = {}

def estimateSpeed(location1, location2):
    """Menghitung estimasi kecepatan kendaraan"""
    d_pixels = math.sqrt(math.pow(location2[0] - location1[0], 2) + math.pow(location2[1] - location1[1], 2))
    ppm = 8.8
    d_meters = d_pixels / ppm
    fps = 18
    speed = d_meters * fps * 3.6
    return speed

@st.cache_resource
def load_cascade_classifier():
    """Load cascade classifier dengan caching"""
    cascade_path = os.path.join(BASE_DIR, "vech.xml")
    if not os.path.exists(cascade_path):
        st.error("File cascade classifier (vech.xml) tidak ditemukan!")
        return None
    return cv2.CascadeClassifier(cascade_path)

def process_frame(frame, car_cascade):
    """Memproses single frame untuk deteksi kendaraan"""
    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cars = car_cascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))
    
    for (x, y, w, h) in cars:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
    
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def process_video(video_path):
    """Memproses video untuk deteksi kendaraan"""
    car_cascade = load_cascade_classifier()
    if car_cascade is None:
        return None
        
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            st.error(f"Tidak dapat membuka video: {video_path}")
            return None
        
        frame_counter = 0
        frame_skip = 2  # Process every nth frame
        
        while cap.isOpened():
            ret, frame = cap.read()
            frame_counter += 1
            
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
                continue
                
            if frame_counter % frame_skip == 0:
                processed_frame = process_frame(frame, car_cascade)
                yield processed_frame
            
    except Exception as e:
        st.error(f"Error dalam pemrosesan video: {str(e)}")
    finally:
        if 'cap' in locals():
            cap.release()

def tampilkan_berita():
    """Menampilkan daftar berita kecelakaan"""
    st.subheader("Berita Kecelakaan Lalu Lintas")
    
    for news in st.session_state.news_data:
        try:
            st.image(news["image"], caption=news["title"], use_container_width=True)
            display_date = datetime.strptime(news['date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            st.write(f"📅 Tanggal: {display_date}  |  🕒 Waktu: {news['time']}")
            st.write(news["description"])
            st.markdown("---")
        except Exception as e:
            st.error(f"Error menampilkan berita: {str(e)}")

def laporkan_kecelakaan():
    """Form untuk melaporkan kecelakaan"""
    st.subheader("Laporkan Kejadian Kecelakaan")
    
    with st.form("laporan_form"):
        title = st.text_input("Judul Laporan")
        description = st.text_area("Deskripsi Kejadian")
        location = st.text_input("Lokasi Kejadian")
        date = st.date_input("Tanggal Kejadian")
        
        # Upload gambar
        image_file = st.file_uploader("Unggah Gambar", type=["jpg", "jpeg", "png"])
        
        submitted = st.form_submit_button("Kirim Laporan")
        
        if submitted:
            if title and description and location and image_file:
                try:
                    # Simpan gambar
                    image_path = os.path.join(CAPTURED_IMAGES_DIR, image_file.name)
                    with open(image_path, "wb") as f:
                        f.write(image_file.getbuffer())
                    
                    # Tambahkan laporan baru
                    laporan_baru = {
                        "title": f"{title} di {location}",
                        "description": description,
                        "time": datetime.now().strftime("%H:%M"),
                        "date": date.strftime("%Y-%m-%d"),
                        "image": image_path
                    }
                    st.session_state.news_data.append(laporan_baru)
                    st.success("Laporan berhasil dikirim!")
                except Exception as e:
                    st.error(f"Error saat menyimpan laporan: {str(e)}")
            else:
                st.error("Harap isi semua kolom yang diperlukan!")

def setup_camera_layout():
    """Setup layout kamera dan tombol capture"""
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    st.session_state.placeholders = {
        'cam1': col1.empty(),
        'cam2': col2.empty(),
        'cam3': col3.empty(),
        'cam4': col4.empty()
    }
    
    capture_col1, capture_col2, capture_col3, capture_col4 = st.columns(4)
    return {
        'Depan': capture_col1.button("Capture Depan"),
        'Belakang': capture_col2.button("Capture Belakang"),
        'Kanan': capture_col3.button("Capture Kanan"),
        'Kiri': capture_col4.button("Capture Kiri")
    }

def handle_capture(frame, position):
    """Menangani proses capture gambar"""
    if not st.session_state.camera_captured[position]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captured_{position}_{timestamp}.jpg"
        filepath = os.path.join(CAPTURED_IMAGES_DIR, filename)
        
        # Simpan gambar dalam format BGR
        cv2.imwrite(filepath, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        
        st.session_state.captured_images.append(filepath)
        st.session_state.camera_captured[position] = True
        st.success(f"Gambar {position} berhasil diambil!")

def main():
    """Fungsi utama aplikasi"""
    st.title("📸 Blind Spot Monitor")
    
    # Inisialisasi session state
    init_session_state()
    
    # Sidebar
    st.sidebar.title("Menu")
    menu = st.sidebar.selectbox("Pilih Menu", 
                              ["Stream Kamera", "Berita Kecelakaan", "Laporkan Kecelakaan"])
    
    if menu == "Stream Kamera":
        st.write("### Streaming Kamera Blind Spot")
        
        # Kontrol kamera
        if st.sidebar.button("Mulai Semua Kamera ▶"):
            st.session_state.cameras_active = True
        if st.sidebar.button("Hentikan Semua Kamera ⛔"):
            st.session_state.cameras_active = False
        
        # Setup layout kamera
        capture_buttons = setup_camera_layout()
        
        if st.session_state.cameras_active:
            try:
                video_path = "carsVideo.mp4"  # Sesuaikan dengan path video Anda
                video_frames = process_video(video_path)
                
                if video_frames:
                    for frame in video_frames:
                        # Update semua placeholder dengan frame baru
                        for placeholder in st.session_state.placeholders.values():
                            placeholder.image(frame, use_column_width=True)
                        
                        # Handle captures
                        for pos, button in capture_buttons.items():
                            if button:
                                handle_capture(frame, pos)
                        
                        time.sleep(0.1)  # Delay untuk mengurangi penggunaan CPU
                        
            except Exception as e:
                st.error(f"Error dalam streaming kamera: {str(e)}")
        else:
            # Tampilkan placeholder saat kamera tidak aktif
            placeholder_image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            for placeholder in st.session_state.placeholders.values():
                placeholder.image(placeholder_image, caption="Kamera tidak aktif", use_column_width=True)
            st.write("Kamera tidak aktif. Tekan 'Mulai Semua Kamera' untuk memulai.")
    
    elif menu == "Berita Kecelakaan":
        tampilkan_berita()
    
    elif menu == "Laporkan Kecelakaan":
        laporkan_kecelakaan()

if __name__ == "__main__":
    main()