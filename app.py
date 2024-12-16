import cv2
import streamlit as st
from datetime import datetime

# Resolusi Konstanta
WIDTH = 640
HEIGHT = 480

# Fungsi Deteksi Kendaraan
def process_video(video_path):
    carCascade = cv2.CascadeClassifier("vech.xml")
    rectangleColor = (0, 255, 255)

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        st.error(f"Gagal membuka video: {video_path}")
        return

    while True:
        ret, frame = video.read()
        if not ret or frame is None:
            break

        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))

        for (x, y, w, h) in cars:
            cv2.rectangle(frame, (x, y), (x+w, y+h), rectangleColor, 2)

        yield frame

    video.release()

# Fungsi Menampilkan Berita Kecelakaan
def tampilkan_berita():
    st.subheader("Berita Kecelakaan Lalu Lintas")

    # Data berita dengan gambar
    if 'news_data' not in st.session_state:
        st.session_state.news_data = [
            {"title": "Kecelakaan di Jalan A", 
             "description": "Mobil menabrak pohon, menyebabkan kemacetan panjang.", 
             "time": "10:30", 
             "image": "https://via.placeholder.com/400x200.png?text=Kecelakaan+Jalan+A"},
            {"title": "Tabrakan Beruntun di Jalan B", 
             "description": "Kecelakaan melibatkan 3 mobil dan 1 motor.", 
             "time": "14:20", 
             "image": "https://via.placeholder.com/400x200.png?text=Tabrakan+Beruntun"},
        ]

    # Menampilkan berita dengan gambar
    for news in st.session_state.news_data:
        st.image(news["image"], caption=news["title"], use_container_width=True)
        st.write(f"🕒 Waktu: {news['time']}")
        st.write(news["description"])
        st.markdown("---")

# Fungsi Fitur Pelaporan Kecelakaan
def laporkan_kecelakaan():
    st.subheader("Laporkan Kejadian Kecelakaan")
    title = st.text_input("Judul Laporan")
    description = st.text_area("Deskripsi Kejadian")
    location = st.text_input("Lokasi Kejadian")
    image_url = st.text_input("Link Gambar (Opsional)")

    if st.button("Kirim Laporan"):
        if title and description and location:
            laporan_baru = {
                "title": f"{title} di {location}",
                "description": description,
                "time": datetime.now().strftime("%H:%M"),
                "image": image_url if image_url else "https://via.placeholder.com/400x200.png?text=Tidak+Ada+Gambar"
            }
            st.session_state.news_data.append(laporan_baru)
            st.success("Laporan berhasil dikirim dan ditambahkan ke berita!")
        else:
            st.error("Harap isi semua kolom yang diperlukan!")

# Fungsi Utama
def main():
    # Judul Aplikasi
    st.title("Kamera Blind Spot Pada Kendaraan Besar")

    # Sidebar Menu
    st.sidebar.title("Menu")
    menu = st.sidebar.selectbox("Pilih Menu", ["Stream Kamera", "Berita Kecelakaan", "Laporkan Kecelakaan"])

    # Path Video Default (Disembunyikan)
    video_path1 = "carsVideo.mp4"
    video_path2 = "carsVideo.mp4"

    if menu == "Stream Kamera":
        st.write("### Kamera 1")
        cam1_placeholder = st.empty()
        st.write("<div style='text-align: center;'>Kamera 1</div>", unsafe_allow_html=True)

        st.write("### Kamera 2")
        cam2_placeholder = st.empty()
        st.write("<div style='text-align: center;'>Kamera 2</div>", unsafe_allow_html=True)

        # Tombol Start dan Stop
        if 'cameras_active' not in st.session_state:
            st.session_state.cameras_active = False

        if st.sidebar.button("Mulai Kedua Kamera"):
            st.session_state.cameras_active = True
        if st.sidebar.button("Hentikan Kedua Kamera"):
            st.session_state.cameras_active = False

        # Menjalankan Kedua Kamera
        if st.session_state.cameras_active:
            st.write("Kamera aktif. Mendeteksi kendaraan...")

            video_feed1 = process_video(video_path1)
            video_feed2 = process_video(video_path2)

            while st.session_state.cameras_active:
                try:
                    frame1 = next(video_feed1)
                    frame2 = next(video_feed2)

                    cam1_placeholder.image(frame1, channels="BGR", use_container_width=True)
                    cam2_placeholder.image(frame2, channels="BGR", use_container_width=True)
                except StopIteration:
                    st.warning("Salah satu atau kedua video telah selesai.")
                    break
        else:
            st.write("Kamera tidak aktif. Tekan 'Mulai Kedua Kamera' untuk memulai.")

    elif menu == "Berita Kecelakaan":
        tampilkan_berita()

    elif menu == "Laporkan Kecelakaan":
        laporkan_kecelakaan()

if __name__ == "__main__":
    main()
