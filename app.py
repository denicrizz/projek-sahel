import cv2
import streamlit as st
from datetime import datetime
import os
import shutil

# Resolusi Konstanta
WIDTH = 640
HEIGHT = 480

# Ensure the captured_images directory exists
base_dir = os.path.dirname(os.path.abspath(__file__))
captured_images_dir = os.path.join(base_dir, "captured_images")
if not os.path.exists(captured_images_dir):
    os.makedirs(captured_images_dir)

# Fungsi untuk menghapus semua file dalam folder captured_images
def clear_captured_images():
    for filename in os.listdir(captured_images_dir):
        file_path = os.path.join(captured_images_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

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

    for news in st.session_state.news_data:
        try:
            st.image(news["image"], caption=news["title"], use_container_width=True)
            st.write(f"🕒 Waktu: {news['time']}")
            st.write(news["description"])
            st.markdown("---")
        except Exception as e:
            st.error(f"Error menampilkan berita: {str(e)}")

# Fungsi untuk menangkap gambar
def capture_image(frame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captured_image_{timestamp}.jpg"
    filepath = os.path.join(captured_images_dir, filename)
    cv2.imwrite(filepath, frame)
    return filepath

# Fungsi Fitur Pelaporan Kecelakaan
def laporkan_kecelakaan():
    st.subheader("Laporkan Kejadian Kecelakaan")
    title = st.text_input("Judul Laporan")
    description = st.text_area("Deskripsi Kejadian")
    location = st.text_input("Lokasi Kejadian")

    # Display captured images and allow selection
    if st.session_state.captured_images:
        st.write("Gambar yang Ditangkap:")
        selected_image = st.selectbox("Pilih Gambar untuk Laporan", st.session_state.captured_images)
        if os.path.exists(selected_image):
            try:
                st.image(selected_image, caption="Gambar Terpilih", use_container_width=True)
            except Exception as e:
                st.error(f"Error menampilkan gambar: {str(e)}")
        else:
            st.error(f"File tidak ditemukan: {selected_image}")
    else:
        st.write("Tidak ada gambar yang ditangkap. Tangkap gambar dari kamera terlebih dahulu.")
        selected_image = None

    # Option to upload a new image
    upload_new = st.checkbox("Unggah Gambar Baru")
    if upload_new:
        image_url = st.file_uploader("Unggah Gambar", type=["jpg", "jpeg", "png"])
    else:
        image_url = None

    if st.button("Kirim Laporan"):
        if title and description and location and (selected_image or image_url):
            if image_url:
                image_path = os.path.join(captured_images_dir, image_url.name)
                with open(image_path, "wb") as f:
                    f.write(image_url.getbuffer())
            else:
                image_path = selected_image

            laporan_baru = {
                "title": f"{title} di {location}",
                "description": description,
                "time": datetime.now().strftime("%H:%M"),
                "image": image_path
            }
            st.session_state.news_data.append(laporan_baru)
            st.success("Laporan berhasil dikirim!")
        else:
            st.error("Harap isi semua kolom yang diperlukan dan pilih atau unggah gambar!")

# Fungsi Utama
def main():
    # Judul Aplikasi
    st.title("📸 Blind Spot Monitor")

    # Initialize news_data in session state if not exists
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

    # Sidebar Menu
    st.sidebar.title("Menu")
    menu = st.sidebar.selectbox("Pilih Menu", ["Stream Kamera", "Berita Kecelakaan", "Laporkan Kecelakaan"])

    # Initialize session state for captured images
    if 'captured_images' not in st.session_state:
        st.session_state.captured_images = []

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

        # Initialize capture flags if not exists
        if 'capture_flags' not in st.session_state:
            st.session_state.capture_flags = [False, False, False, False]

        # Reset Capture button
        if st.sidebar.button("Reset Capture"):
            st.session_state.capture_flags = [False, False, False, False]
            clear_captured_images()  # Panggil fungsi untuk menghapus file
            st.session_state.captured_images = []  # Kosongkan list captured_images
            st.rerun()

        # Capture buttons for each camera
        capture_col1, capture_col2, capture_col3, capture_col4 = st.columns(4)
        capture_button1 = capture_col1.button("Capture Depan ", disabled=st.session_state.capture_flags[0])
        capture_button2 = capture_col2.button("Capture Belakang", disabled=st.session_state.capture_flags[1])
        capture_button3 = capture_col3.button("Capture Kanan ", disabled=st.session_state.capture_flags[2])
        capture_button4 = capture_col4.button("Capture Kiri ", disabled=st.session_state.capture_flags[3])

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

                    # Capture images if buttons are pressed (only once per camera)
                    if capture_button1 and not st.session_state.capture_flags[0]:
                        st.session_state.captured_images.append(capture_image(frame1))
                        st.session_state.capture_flags[0] = True
                    if capture_button2 and not st.session_state.capture_flags[1]:
                        st.session_state.captured_images.append(capture_image(frame2))
                        st.session_state.capture_flags[1] = True
                    if capture_button3 and not st.session_state.capture_flags[2]:
                        st.session_state.captured_images.append(capture_image(frame3))
                        st.session_state.capture_flags[2] = True
                    if capture_button4 and not st.session_state.capture_flags[3]:
                        st.session_state.captured_images.append(capture_image(frame4))
                        st.session_state.capture_flags[3] = True

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