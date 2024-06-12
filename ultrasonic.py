import serial
import time

# Konfigurasi pin UART
uart_port = "/dev/ttyS0"  # UART port pada Raspberry Pi 4B
baud_rate = 9600
# Inisialisasi objek serial
ser = serial.Serial(uart_port, baud_rate, timeout=1)

def read_distance_and_temperature():
    # Kirim perintah untuk mengukur jarak
    ser.write(b'\x55')  # Perintah untuk mengukur jarak
    time.sleep(0.5)  # Tunggu 0.5 detik
    mm_dist = None
    temp = None
    # Baca data yang dikirimkan oleh sensor
    response = ser.read(2)  # Baca 2 byte
    if len(response) == 2:
        msb_dist, lsb_dist = response
        mm_dist = msb_dist * 256 + lsb_dist  # Konversi ke milimeter
        if 1 < mm_dist < 10000:  # Periksa apakah jarak berada dalam rentang yang valid
            print("Jarak:", mm_dist, "mm")

    # Kirim perintah untuk mengukur suhu
    ser.write(b'\x50')  # Perintah untuk mengukur suhu
    time.sleep(0.5)  # Tunggu 0.5 detik

    # Baca data yang dikirimkan oleh sensor
    response = ser.read(1)  # Baca 1 byte
    if len(response) == 1:
        temp = response[0]
        if 1 < temp < 130:  # Periksa apakah suhu berada dalam rentang yang valid
            temp -= 45  # Koreksi offset suhu
            print("Suhu:", temp, "°C")
    return temp, mm_dist


