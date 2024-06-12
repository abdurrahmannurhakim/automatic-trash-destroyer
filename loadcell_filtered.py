from hx711 import HX711
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

def average(data):
    total = sum(data)
    rata_rata = total / len(data)
    return rata_rata

def constant(real_value, raw_value):
    return (real_value / raw_value)

def detect_outliers(data, threshold):
    
    #Deteksi nilai mayoritas dan minoritas berdasarkan threshold setelah pengurutan.
    
    sorted_data = sorted(data)
    majorities = []
    minorities = []
    major_indices = []
    minor_indices = []
    
    # Cari kelompok mayoritas
    temp_majorities = [sorted_data[0]]
    for i in range(1, len(sorted_data)):
        if abs(sorted_data[i] - sorted_data[i - 1]) <= threshold:
            temp_majorities.append(sorted_data[i])
        else:
            if len(temp_majorities) > len(majorities):
                majorities = temp_majorities
            temp_majorities = [sorted_data[i]]
    if len(temp_majorities) > len(majorities):
        majorities = temp_majorities

    # Tentukan nilai minoritas berdasarkan nilai mayoritas
    for i, value in enumerate(data):
        if value in majorities:
            major_indices.append(i)
        else:
            minorities.append(value)
            minor_indices.append(i)

    return majorities, minorities, major_indices, minor_indices

def replace_minorities(data, majorities, minor_indices):

    #Ganti nilai minoritas dengan rata-rata nilai mayoritas.
    if not majorities:
        return data

    major_avg = average(majorities)

    for index in minor_indices:
        data[index] = major_avg

    return data

def read_hx711(window_size=10, threshold=500):
    hx711 = HX711(dout_pin=5, pd_sck_pin=6, channel='A', gain=64)
    hx711.reset()  # Sebelum memulai, reset HX711 (tidak wajib)
    measures = hx711.get_raw_data()
    
    majorities, minorities, major_indices, minor_indices = detect_outliers(measures, threshold)
    
    print("Majorities: ", majorities)
    print("Minorities: ", minorities)
    print("Majority indices: ", major_indices)
    print("Minority indices: ", minor_indices)
    
    filtered_measures = replace_minorities(measures, majorities, minor_indices)
    total_measures = average(filtered_measures)

    GPIO.cleanup()  # Selalu lakukan pembersihan GPIO di skrip Anda!

    print("Raw measures: ", measures)
    print("Filtered measures: ", filtered_measures)
    print("Filtered average value: ", total_measures)

    return -total_measures, minorities
    #return -total_measures
# Contoh penggunaan
#if __name__ == "__main__":
#    filtered_value = read_hx711(window_size=10, threshold=500)
#    print("Filtered value (mode filter):", filtered_value)


