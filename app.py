# Import library yang diperlukan
import cv2  # Untuk pemrosesan gambar dan video
import streamlit as st  # Untuk membuat antarmuka web
from datetime import datetime  # Untuk menangani tanggal dan waktu
import os  # Untuk operasi sistem file
import shutil  # Untuk operasi file lanjutan
import time  # Untuk fungsi waktu
import math  # Untuk perhitungan matematika

# Mengatur resolusi standar untuk video
WIDTH = 640
HEIGHT = 480

# Membuat direktori untuk menyimpan gambar yang ditangkap
base_dir = os.path.dirname(os.path.abspath(__file__))
captured_images_dir = os.path.join(base_dir, "captured_images")
if not os.path.exists(captured_images_dir):
    os.makedirs(captured_images_dir)

# Fungsi untuk membersihkan folder gambar yang ditangkap
def clear_captured_images():
    for filename in os.listdir(captured_images_dir):
        file_path = os.path.join(captured_images_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Gagal menghapus {file_path}. Alasan: {e}')

# Fungsi untuk menghitung kecepatan kendaraan
def estimateSpeed(location1, location2):
    d_pixels = math.sqrt(math.pow(location2[0] - location1[0], 2) + math.pow(location2[1] - location1[1], 2))
    ppm = 8.8  # pixels per meter (kalibrasi)
    d_meters = d_pixels / ppm
    fps = 18  # frame per detik
    speed = d_meters * fps * 3.6  # konversi ke km/jam
    return speed

# Fungsi untuk memproses video dan mendeteksi kendaraan
def process_video(video_path):
    carCascade = cv2.CascadeClassifier("vech.xml")  # Classifier untuk deteksi kendaraan
    rectangleColor = (0, 255, 255)  # Warna kuning untuk kotak pembatas

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        st.error(f"Gagal membuka video: {video_path}")
        return

    frameCounter = 0
    currentCarID = 0
    carLocation1 = {}
    carLocation2 = {}
    speed = [None] * 1000
    carIDs = []
    trackers = []

    while True:
        ret, frame = video.read()
        if not ret or frame is None:
            break

        # Menyesuaikan ukuran frame
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        resultImage = frame.copy()
        frameCounter += 1

        # Deteksi kendaraan setiap 10 frame
        if frameCounter % 10 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))
            
            trackers = []
            carLocation1.clear()
            carLocation2.clear()
            carIDs.clear()

            # Inisialisasi tracker untuk setiap kendaraan yang terdeteksi
            for (x, y, w, h) in cars:
                tracker = cv2.legacy.TrackerKCF_create()
                tracker.init(frame, (x, y, w, h))
                trackers.append(tracker)
                
                carLocation1[currentCarID] = [x, y, w, h]
                carIDs.append(currentCarID)
                currentCarID += 1

        # Update posisi kendaraan menggunakan tracker
        for idx, tracker in enumerate(trackers):
            success, box = tracker.update(frame)
            
            if success:
                x, y, w, h = [int(v) for v in box]
                cv2.rectangle(resultImage, (x, y), (x+w, y+h), rectangleColor, 2)
                
                carID = carIDs[idx]
                carLocation2[carID] = [x, y, w, h]

                # Hitung dan tampilkan kecepatan
                if frameCounter % 1 == 0:
                    [x1, y1, w1, h1] = carLocation1[carID]
                    carLocation1[carID] = [x, y, w, h]

                    if [x1, y1, w1, h1] != [x, y, w, h]:
                        if speed[carID] is None and y1 >= 275 and y1 <= 285:
                            speed[carID] = estimateSpeed([x1, y1, w1, h1], [x, y, w, h])
                        if speed[carID] is not None and y1 >= 180:
                            cv2.putText(resultImage, f"{int(speed[carID])}km/h", 
                                      (int(x1 + w1/2), int(y1-5)), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 100), 2)

        yield resultImage

    video.release()

# Fungsi untuk menampilkan berita kecelakaan
def tampilkan_berita():
    st.subheader("Berita Kecelakaan Lalu Lintas")

    for news in st.session_state.news_data:
        try:
            st.image(news["image"], caption=news["title"], use_container_width=True)
            
            # Format tanggal untuk ditampilkan
            try:
                if isinstance(news['date'], str):
                    display_date = datetime.strptime(news['date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                else:
                    display_date = news['date'].strftime("%d-%m-%Y")
            except Exception:
                display_date = news['date']
                
            st.write(f"📅 Tanggal: {display_date}  |  🕒 Waktu: {news['time']}")
            st.write(news["description"])
            st.markdown("---")
        except Exception as e:
            st.error(f"Error menampilkan berita: {str(e)}")

# Fungsi untuk menangkap gambar dari kamera
def capture_image(frame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captured_image_{timestamp}.jpg"
    filepath = os.path.join(captured_images_dir, filename)
    cv2.imwrite(filepath, frame)
    return filepath

# Fungsi untuk memeriksa status capture kamera
def can_capture(camera):
    if not st.session_state.camera_captured[camera]:
        st.session_state.camera_captured[camera] = True
        return True
    return False

# Fungsi untuk melaporkan kecelakaan
def laporkan_kecelakaan():
    st.subheader("Laporkan Kejadian Kecelakaan")
    title = st.text_input("Judul Laporan")
    description = st.text_area("Deskripsi Kejadian")
    location = st.text_input("Lokasi Kejadian")
    date = st.date_input("Tanggal Kejadian")

    # Menampilkan gambar yang sudah ditangkap
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

    # Opsi untuk mengunggah gambar baru
    upload_new = st.checkbox("Unggah Gambar Baru")
    if upload_new:
        image_url = st.file_uploader("Unggah Gambar", type=["jpg", "jpeg", "png"])
    else:
        image_url = None

    # Proses pengiriman laporan
    if st.button("Kirim Laporan"):
        if title and description and location and (selected_image or image_url):
            if image_url:
                image_path = os.path.join(captured_images_dir, image_url.name)
                with open(image_path, "wb") as f:
                    f.write(image_url.getbuffer())
            else:
                image_path = selected_image

            # Format tanggal sebelum disimpan
            formatted_date = date.strftime("%Y-%m-%d")
            
            laporan_baru = {
                "title": f"{title} di {location}",
                "description": description,
                "time": datetime.now().strftime("%H:%M"),
                "date": formatted_date,
                "image": image_path
            }
            st.session_state.news_data.append(laporan_baru)
            st.success("Laporan berhasil dikirim!")
        else:
            st.error("Harap isi semua kolom yang diperlukan dan pilih atau unggah gambar!")

# Fungsi utama aplikasi
def main():
    # Judul aplikasi
    st.title("📸 Blind Spot Monitor")

    # Inisialisasi data berita dalam session state
    if 'news_data' not in st.session_state:
        st.session_state.news_data = [
            {
                "title": "Kecelakaan di Jalan A", 
                "description": "Mobil menabrak pohon, menyebabkan kemacetan panjang.", 
                "time": "10:30", 
                "date": "2024-04-17",  # Format YYYY-MM-DD
                "image": "assets/1.jpeg"
            },
            {
                "title": "Tabrakan Beruntun di Jalan B", 
                "description": "Kecelakaan melibatkan 3 mobil dan 1 motor.", 
                "time": "14:20",  
                "date": "2024-09-18",  # Format YYYY-MM-DD
                "image": "assets/2.jpg"
            },
        ]

    # Inisialisasi status capture kamera
    if 'camera_captured' not in st.session_state:
        st.session_state.camera_captured = {
            'Depan': False, 'Belakang': False, 'Kanan': False, 'Kiri': False
        }

    # Inisialisasi daftar gambar yang ditangkap
    if 'captured_images' not in st.session_state:
        st.session_state.captured_images = []

    # Menu sidebar
    st.sidebar.title("Menu")
    menu = st.sidebar.selectbox("Pilih Menu", ["Stream Kamera", "Berita Kecelakaan", "Laporkan Kecelakaan"])

    # Path video default
    video_path1 = "carsVideo.mp4"  # Kamera Depan
    video_path2 = "carsVideo.mp4"  # Kamera Belakang
    video_path3 = "carsVideo.mp4"  # Kamera Kanan
    video_path4 = "carsVideo.mp4"  # Kamera Kiri

    # Mengatur tampilan berdasarkan menu yang dipilih
    if menu == "Stream Kamera":
        st.write("### Streaming Kamera Blind Spot")

        # Layout 2x2 untuk 4 kamera
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        cam1_placeholder = col1.empty()  # Kamera Depan
        cam2_placeholder = col2.empty()  # Kamera Belakang
        cam3_placeholder = col3.empty()  # Kamera Kanan
        cam4_placeholder = col4.empty()  # Kamera Kiri

        # Tombol kontrol kamera
        if 'cameras_active' not in st.session_state:
            st.session_state.cameras_active = False

        if st.sidebar.button("Mulai Semua Kamera ▶"):
            st.session_state.cameras_active = True
        if st.sidebar.button("Hentikan Semua Kamera ⛔"):
            st.session_state.cameras_active = False

        # Tombol capture untuk setiap kamera
        capture_col1, capture_col2, capture_col3, capture_col4 = st.columns(4)
        capture_button1 = capture_col1.button("Capture Depan", disabled=st.session_state.camera_captured['Depan'])
        capture_button2 = capture_col2.button("Capture Belakang", disabled=st.session_state.camera_captured['Belakang'])
        capture_button3 = capture_col3.button("Capture Kanan", disabled=st.session_state.camera_captured['Kanan'])
        capture_button4 = capture_col4.button("Capture Kiri", disabled=st.session_state.camera_captured['Kiri'])

        # Menjalankan semua kamera
        if st.session_state.cameras_active:
            st.write("Kamera aktif. Mendeteksi kendaraan...")

            video_feed1 = process_video(video_path1)
            video_feed2 = process_video(video_path2)
            video_feed3 = process_video(video_path3)
            video_feed4 = process_video(video_path4)

            while st.session_state.cameras_active:
                try:
                    # Mengambil frame dari setiap video
                    frame1 = next(video_feed1)
                    frame2 = next(video_feed2)
                    frame3 = next(video_feed3)
                    frame4 = next(video_feed4)

# Menampilkan frame di masing-masing kotak
                    cam1_placeholder.image(frame1, channels="BGR", use_container_width=True, caption="Kamera Depan")
                    cam2_placeholder.image(frame2, channels="BGR", use_container_width=True, caption="Kamera Belakang")
                    cam3_placeholder.image(frame3, channels="BGR", use_container_width=True, caption="Kamera Kanan")
                    cam4_placeholder.image(frame4, channels="BGR", use_container_width=True, caption="Kamera Kiri")

                    # Mengambil gambar jika tombol capture ditekan
                    if capture_button1 and can_capture('Depan'):
                        st.session_state.captured_images.append(capture_image(frame1))
                        st.success("Gambar Depan berhasil diambil!")
                    if capture_button2 and can_capture('Belakang'):
                        st.session_state.captured_images.append(capture_image(frame2))
                        st.success("Gambar Belakang berhasil diambil!")
                    if capture_button3 and can_capture('Kanan'):
                        st.session_state.captured_images.append(capture_image(frame3))
                        st.success("Gambar Kanan berhasil diambil!")
                    if capture_button4 and can_capture('Kiri'):
                        st.session_state.captured_images.append(capture_image(frame4))
                        st.success("Gambar Kiri berhasil diambil!")

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