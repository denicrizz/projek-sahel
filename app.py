import cv2
import streamlit as st
from datetime import datetime

# Resolusi Konstanta
WIDTH = 640
HEIGHT = 480

# Fungsi Deteksi Kendaraan
def process_video(video_path):
    carCascade = cv2.CascadeClassifier("vech.xml")  # File XML untuk deteksi kendaraan
    rectangleColor = (0, 255, 255)  # Warna bounding box

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        st.error(f"Gagal membuka video: {video_path}")
        return

    while True:
        ret, frame = video.read()
        if not ret or frame is None:
            break

        # Resize frame
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Deteksi kendaraan
        cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))
        for (x, y, w, h) in cars:
            cv2.rectangle(frame, (x, y), (x + w, y + h), rectangleColor, 2)

        yield frame  # Kirim frame ke Streamlit

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
             "image": "assets/1.jpeg"},
            {"title": "Tabrakan Beruntun di Jalan B", 
             "description": "Kecelakaan melibatkan 3 mobil dan 1 motor.", 
             "time": "14:20", 
             "image": "assets/2.jpg"},
        ]

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
    image_url = st.file_uploader("Unggah Gambar (Opsional)", type=["jpg", "jpeg", "png"])

    if st.button("Kirim Laporan"):
        if title and description and location:
            image_path = "https://via.placeholder.com/400x200.png?text=Tidak+Ada+Gambar"
            if image_url:
                image_path = f"uploaded_images/{image_url.name}"
                with open(image_path, "wb") as f:
                    f.write(image_url.getbuffer())

            laporan_baru = {
                "title": f"{title} di {location}",
                "description": description,
                "time": datetime.now().strftime("%H:%M"),
                "image": image_path
            }
            st.session_state.news_data.append(laporan_baru)
            st.success("Laporan berhasil dikirim!")
        else:
            st.error("Harap isi semua kolom yang diperlukan!")

# Fungsi Utama
def main():
    # Judul Aplikasi
    st.title("📸 Blind Spot Monitor")

    # Sidebar Menu
    st.sidebar.title("Menu")
    menu = st.sidebar.selectbox("Pilih Menu", ["Stream Kamera", "Berita Kecelakaan", "Laporkan Kecelakaan"])

    # Path Video Default
    video_path1 = "carsVideo.mp4"  # Kamera Depan
    video_path2 = "carsVideo.mp4"  # Kamera Belakang
    video_path3 = "carsVideo.mp4"  # Kamera Kanan
    video_path4 = "carsVideo.mp4"  # Kamera Kiri

    if menu == "Stream Kamera":
        st.write("### Streaming Kamera Blind Spot")

        # Layout 2x2 untuk 4 Kamera
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        cam1_placeholder = col1.empty()  # Kamera Depan
        cam2_placeholder = col2.empty()  # Kamera Belakang
        cam3_placeholder = col3.empty()  # Kamera Kanan
        cam4_placeholder = col4.empty()  # Kamera Kiri

        # Tombol Start dan Stop
        if 'cameras_active' not in st.session_state:
            st.session_state.cameras_active = False

        if st.sidebar.button("Mulai Semua Kamera"):
            st.session_state.cameras_active = True
        if st.sidebar.button("Hentikan Semua Kamera"):
            st.session_state.cameras_active = False

        # Menjalankan Keempat Kamera
        if st.session_state.cameras_active:
            st.write("Kamera aktif. Mendeteksi kendaraan...")

            video_feed1 = process_video(video_path1)
            video_feed2 = process_video(video_path2)
            video_feed3 = process_video(video_path3)
            video_feed4 = process_video(video_path4)

            while st.session_state.cameras_active:
                try:
                    # Ambil frame dari setiap video
                    frame1 = next(video_feed1)
                    frame2 = next(video_feed2)
                    frame3 = next(video_feed3)
                    frame4 = next(video_feed4)

                    # Tampilkan frame di 4 kotak
                    cam1_placeholder.image(frame1, channels="BGR", use_container_width=True, caption="Kamera Depan")
                    cam2_placeholder.image(frame2, channels="BGR", use_container_width=True, caption="Kamera Belakang")
                    cam3_placeholder.image(frame3, channels="BGR", use_container_width=True, caption="Kamera Kanan")
                    cam4_placeholder.image(frame4, channels="BGR", use_container_width=True, caption="Kamera Kiri")

                except StopIteration:
                    st.warning("Salah satu atau lebih video telah selesai.")
                    break
        else:
            st.write("Kamera tidak aktif. Tekan 'Mulai Semua Kamera' untuk memulai.")

    elif menu == "Berita Kecelakaan":
        tampilkan_berita()

    elif menu == "Laporkan Kecelakaan":
        laporkan_kecelakaan()

if __name__ == "__main__":
    main()
