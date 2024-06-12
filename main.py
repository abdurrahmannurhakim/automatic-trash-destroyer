import loadcell_filtered as lc #library bikinan untuk ngitung loadcell
import read_config as rc #library buat baca nilai config dari config.csv
import ultrasonic as ul #library ultrasonic
import pyrebase #library firebase
import RPi.GPIO as GPIO #buat GPIO
from RPLCD.i2c import CharLCD #library LCD
from datetime import datetime, timedelta #library format tanggal
import time #library timer
import socket #library socket buat cek koneksi internet
import subprocess # buat jalanin terminal via python (sudo reboot)

#ultrasonic y401 (distance + temperature)
temperature = None
mm_distance = None


# Fungsi untuk memeriksa koneksi internet, dns google 8.8.8.8
def check_internet_connection():
    result = subprocess.call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result == 0

# Konfigurasi Firebase (bisa dicek disetting firebase)
firebaseConfig = {
  "apiKey": "AIzaSyCE6p2s075BcH52X3NJaWESCXKDJ0zGFXA",
  "authDomain": "shanti-raspi-project.firebaseapp.com",
  "databaseURL": "https://shanti-raspi-project-default-rtdb.firebaseio.com",
  "projectId": "shanti-raspi-project",
  "storageBucket": "shanti-raspi-project.appspot.com",
  "messagingSenderId": "278526881604",
}

#buat buffer untuk lcd 16x2
buffer1 = [
    [' '] * 16, #row 1, 16 character
    [' '] * 16 #row 2, 16 character
]

firebase = pyrebase.initialize_app(firebaseConfig) #init firebase
db = firebase.database()  #variable db untuk mencatata database firebase struct
trash_weight = 0.00 #dibikin global biar bisa diakses dimanapun
row_1 = ""
row_2 = ""

# Inisialisasi GPIO awal
GPIO.setmode(GPIO.BCM)

#setup relay awal
# Atur pin GPIO untuk relay
relay_pin = 17
GPIO.setup(relay_pin, GPIO.OUT)

# setup servo awal
servo_pin = 18
# Inisialisasi PWM (Pulse Width Modulation)
GPIO.setup(servo_pin, GPIO.OUT)
pwm = GPIO.PWM(servo_pin, 50)  # 50Hz (sudut standar servo motor)

#setup relay
def setup_relay():
    relay_pin = 17
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(relay_pin, GPIO.OUT)

#setup servo
def setup_pwm():
    servo_pin = 18
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(servo_pin, GPIO.OUT)

def set_angle(angle):
    duty = angle / 18 + 2  # Mengubah sudut menjadi duty cycle
    GPIO.output(servo_pin, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(4)  # Waktu untuk motor mencapai sudut yang diinginkan
    GPIO.output(servo_pin, False)
    pwm.ChangeDutyCycle(0)

# Setup GPIO button
ON = 1
OFF = 0

def setup_gpio():
    GPIO.setmode(GPIO.BCM)  # Gunakan penomoran BCM

    # Pin button yang digunakan
    button_pin_1 = 21
    button_pin_2 = 20
    button_pin_3 = 7

    # Setup pin sebagai input dengan pull-up resistor
    GPIO.setup(button_pin_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(button_pin_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(button_pin_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    return button_pin_1, button_pin_2, button_pin_3

def lcd_clear():
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
    #reset lcd
    lcd.clear()

def lcd_display(row_1, row_2):
    #buat variable array untuk
    buffer1[0][:len(row_1)] = row_1  # Mengisi baris pertama
    buffer1[1][:len(row_2)] = row_2  # Mengisi baris kedua

    # Mengonversi array menjadi string dan menggabungkannya
    combined_string = ''.join(buffer1[0]) + ''.join(buffer1[1])
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)

    #reset lcd
    lcd.clear()

    #clear buffer
    buffer1[0][:16] = "                "  # clear isi buffer row 1
    buffer1[1][:16] = "                "  # clear isi buffer row 2

    #tampilkan buffer terbaru
    lcd.write_string(combined_string)

def servo_top(mode): #fungsi buka tutup sampah
    setup_pwm() #init ulang servo pwm
    if mode == "open":
        pwm.start(0)  # Mulai PWM dengan duty cycle 0 (posisi awal)
        # Gerakkan servo motor ke 90 derajat
        set_angle(90)
        #time.sleep(2) #delay lima detik
    elif mode == "close":
        # Kembalikan servo motor ke posisi awal (0 derajat)
        set_angle(0)
        #time.sleep(2) #delay lima detik

def stepper_bellow(mode):
    #setup awal driver motor
    # Setup GPIO mode
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Define GPIO pins
    CW_PIN = 12  # GPIO12 for clockwise rotation
    CCW_PIN = 13  # GPIO13 for counterclockwise rotation
    # Setup GPIO pins as output
    GPIO.setup(CW_PIN, GPIO.OUT)
    GPIO.setup(CCW_PIN, GPIO.OUT)
    # Setup PWM on the pins with a frequency of 1000Hz
    pwm_cw = GPIO.PWM(CW_PIN, 1000)
    pwm_ccw = GPIO.PWM(CCW_PIN, 1000)
    # Start PWM with a duty cycle of 0 (motor off)
    pwm_cw.start(0)
    pwm_ccw.start(0)
    if mode == "open":
        print("buka penutup samping (pembuangan)")
        lcd_display("Open Trashchute", "Opening ...")
        pwm_ccw.ChangeDutyCycle(0)  # Ensure CCW PWM is off
        pwm_cw.ChangeDutyCycle(100)  # Set CW PWM duty cycle
        time.sleep(8) #delay 8 detik
        pwm_cw.ChangeDutyCycle(0)  # Ensure CW PWM is off
        pwm_ccw.ChangeDutyCycle(0)  # Ensure CCW PWM is off
        time.sleep(2)
    elif mode == "close":
        print("tutup penutup samping (pembuangan)")
        lcd_display("Close Trashchute", "Closing ...")
        pwm_cw.ChangeDutyCycle(0)  # Ensure CW PWM is off
        pwm_ccw.ChangeDutyCycle(100)  # Set CCW PWM duty cycle
        time.sleep(24) #delay 24 detik
        pwm_cw.ChangeDutyCycle(0)  # Ensure CW PWM is off
        pwm_ccw.ChangeDutyCycle(0)  # Ensure CCW PWM is off
        time.sleep(2)

#fungsi proses pengiriman ke firebase
def send_to_firebase(clean_time_ms, process_time_ms, trash_weight_kg, weight_catergory_str, temperature):
    #catat waktu sekarang
    current_date_time = datetime.now() #catat waktu sekarang untuk firebase
    formatted_time = current_date_time.strftime("%Y-%m-%d %H:%M:%S") #setting ke format yang kita mau 

    # Konversi clean_time ke detik
    process_time_sec = process_time_ms / 1000
    clean_time_sec = clean_time_ms / 1000

    data = {
        "start_time": formatted_time,
        "end_time": None, #kosongkan dulu, nanti diupdate di bawah
        "clean_time (ms)": str(clean_time_ms), #waktu pembersihan sampah dari mesin
        "process_time (ms)": str(process_time_ms), #waktu penggilingan
        "weight_category": str(weight_catergory_str), #kategori berat
        "trash_weight (kg)": str(trash_weight_kg) #berat
        #"temperature (°C)": str(temperature) #suhu
    }

    lcd_display("Mode: Destroy", "Processing ..")
    print("Proses dimulai ..")
    last_time = time.time() #catat waktu sekarang untuk counting time
    while True:  #hold dulu selama process_time_sec second
        setup_relay() #init ulang gpio relay
        current_time = time.time()
        if current_time - last_time <= process_time_sec:
            #aktifkan relay di sini
            print("time process: " + str(int(time.time()-last_time)) + " second")
            GPIO.output(relay_pin, GPIO.HIGH)
            time.sleep(0) #do nothing
        else:
            GPIO.output(relay_pin, GPIO.LOW)
            break #break while supaya program berlanjut

    #catat data terakhir
    end_date_time = datetime.now()  #update end_time
    formatted_end_time = end_date_time.strftime("%Y-%m-%d %H:%M:%S") #setting ke format yang kita mau
    data["end_time"] = formatted_end_time #set dengan format = yyyy:MM:dd HH:mm:ss
    lcd_display("Mode: Destroy", "Process Done !!")
    print("Proses selesai")
    time.sleep(2) #delay dua detik
    stepper_bellow("open")  #buka tutup pembuangan
    lcd_display("Mode: Clean", "Processing ..")
    print("Proses Clean dimulai ..")
    last_time = time.time() #catat waktu sekarang untuk counting time
    while True: #hold dulu selama proses clean time second 
        current_time = time.time()
        if current_time - last_time <= clean_time_sec:
            #aktifkan relay di sini
            print("time Cleaning: " + str(int(time.time()-last_time)) + " second")
            GPIO.output(relay_pin, GPIO.HIGH)
            time.sleep(0) #do nothing
        else:
            GPIO.output(relay_pin, GPIO.LOW)
            break

    stepper_bellow("close") #tutup
    lcd_display("Mode: Clean", "Process Done !!")
    print("Proses Clean Selesai")

    #cek internet dulu sebelum mulai proses
    if check_internet_connection():
        db.child("history").child(formatted_time).set(data) #kirim struct data = {} ke firebase
    else:
        lcd_display("No Internet !!", "Cannot Send !!")
        time.sleep(10) #tahan notifikasi selama 10 detik
    print("Data berhasil dikirim ke Firebase")

    #klasifiksi lama waktu penggilingan dengan clean time (lama waktu pembuangan)
def fuzzy_classtering(trash_weight_kg): #fungsi klasifikasi
    clean_time_ms = 0 #kondisi idle
    process_time_ms = 0 #kondisi idle
    config_values = rc.read_config("config.csv") 
    actual_value, raw_value, time_constant = rc.convert_to_float(config_values)
    mass_to_time = trash_weight_kg * time_constant
    weight_categories = {1: 'Ringan', 2: 'Sedang', 3: 'Berat'} #weight_categories[1] = ringan, weight_categories[2] = sedang, weight_categories[3] = berat
    if trash_weight_kg <= 0.0: #jika berat di bawah sama dengan 0 kg
        process_time_ms = 0 #interval waktu penggilingan 0
        clean_time_ms = 0 #interval waktu pembuangan 0
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': 'Tidak ada sampah'}
    elif trash_weight_kg > 0.0 and trash_weight_kg <= 2.0: #jika diatas 0 kg dan dibawah sama dengan 2 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[1]}
    elif trash_weight_kg > 2.0 and trash_weight_kg <= 3.0: #jika diatas 2 kg dan dibawah sama dengan 3 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[1]}
    elif trash_weight_kg > 3.0 and trash_weight_kg <= 3.5: #jika diatas 3.0 kg dan dibawah sama dengan 3.5 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[1]}
    elif trash_weight_kg > 3.5 and trash_weight_kg <= 4.0: #jika diatas 3.5 kg dan dibawah sama dengan 4 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[2]}
    elif trash_weight_kg > 4.5 and trash_weight_kg <= 5.0: #jika diatas 4.5 kg dan dibawah sama dengan 5.0 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[2]}
    elif trash_weight_kg > 5.0 and trash_weight_kg <= 5.5: #jika diatas 5.0 kg dan dibawah sama dengan 5.5 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[2]}
    elif trash_weight_kg > 5.5 and trash_weight_kg <= 6.0: #jika diatas 5.5 kg dan dibawah sama dengan 6 kg 
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[2]}
    elif trash_weight_kg > 6.0 and trash_weight_kg <= 6.5: #jika diatas 6 kg dan dibawah sama dengan 6.5 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    elif trash_weight_kg > 6.5 and trash_weight_kg <= 7.0: #jika diatas 6.5 kg dan dibawah sama dengan 7 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    elif trash_weight_kg > 7.0 and trash_weight_kg <= 7.5: #jika diatas 7 kg dan dibawah sama dengan 7.5 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    elif trash_weight_kg > 7.5 and trash_weight_kg <= 8.0: #jika diatas 7.5 kg dan dibawah sama dengan 8 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    elif trash_weight_kg > 8.0 and trash_weight_kg <= 8.5: #jika diatas 8 kg dan dibawah sama dengan 8.5 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    elif trash_weight_kg > 8.5 and trash_weight_kg <= 9.0: #jika diatas 8.5 kg dan dibawah sama dengan 9 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    elif trash_weight_kg > 9.0 and trash_weight_kg <= 9.5: #jika diatas 9 kg dan dibawah sama dengan 9.5 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    elif trash_weight_kg > 9.5 and trash_weight_kg <= 10.0: #jika diatas 9.5 kg dan dibawah sama dengan 10 kg
        process_time_ms = int(mass_to_time)
        clean_time_ms = int(process_time_ms / 2)
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': weight_categories[3]}
    else:
        process_time_ms = 0
        clean_time_ms = 0
        #output dari fungsi rekrusif fuzzy_classtering adalah struct berisi variable weight_categories (string array), process_time_ms, dan clean_time_ms
        #syntax mengeluarkan output adalah return (sama dengan bahasa c/cpp)
        return {'clean_time_ms': clean_time_ms, 'process_time_ms': process_time_ms, 'trash_weight_kg': trash_weight_kg, 'weight_category_str': 'di luar range'}

def read_raw():
    time.sleep(1)
    result = 0
    sum_trash_raw = 0
    raw_value, minor_value = lc.read_hx711(window_size=10, threshold=500)
    print("coba membaca, ", len(minor_value))
    result = raw_value
    while len(minor_value) != 0:
        raw_value, minor_value = lc.read_hx711(window_size=10, threshold=500)
        result = raw_value
        time.sleep(1)
        print("masih membaca, ", len(minor_value))
    print("result = ", result)
    return result

def read_trash(delay_time, status):
    sum_trash_weight = 0
    config_values = rc.read_config("config.csv")
    actual_value, raw_value, time_constant = rc.convert_to_float(config_values)
    print("current zero: ", zeroing)
    for i in range(delay_time):
        raw_kg_read = round((read_raw()-zeroing) * lc.constant(actual_value, raw_value), 2)  # trash weight dalam kg
        if raw_kg_read < 0.00:
            raw_kg_read = 0.00

        sum_trash_weight += raw_kg_read
        trash_weight = round(sum_trash_weight / (i+1), 2)
        if status == "process": 
            lcd_display("Start Counting..", ("Mass : " + str(trash_weight) + " kg"))
        elif status == "ready":
            lcd_display("Mode: Ready", ("Mass : " + str(trash_weight) + " kg"))
        elif status == "normal":
            lcd_display("Mode: Normal", ("Mass : " + str(trash_weight) + " kg"))
        #print(trash_weight)
        time.sleep(0.5) #delay 0.5 detik
    return trash_weight

def process():
    servo_top("open") #fungsi servo buka
    lcd_display("Please Insert", "The Trash !!")
    time.sleep(10) #tahan dua detik
    servo_top("close") #fungsi servo tutup 
    trash_weight = read_trash(5, "process") #True itu kalo proses sedang dimulai 
    result = fuzzy_classtering(trash_weight) #panggil fungsi rekrusif fuzzy_classtering, lalu tampung di struct bernama result
    clean_time = result['clean_time_ms'] #panggil variable secara spesifik
    process_time = result['process_time_ms']  #panggil variable secara spesifik
    weight_category_str = result['weight_category_str']  #panggil variable secara spesifik    
    send_to_firebase(clean_time, process_time, trash_weight, weight_category_str, temperature) #kirim melalui fungsi send_to_firebase

#main program
if __name__ == "__main__":
    print("123")
    lcd_clear()#bersikan sisa text di layar
    counter_rezero = 0
    zeroing = read_raw()
    status_start = False
    show_normal_value = False
    show_raw_value = False
    print("first zero: ", zeroing)
    stepper_bellow("close") #tutup
    lcd_display("Current Zero:", str(zeroing)) #Tampilkan Zero
    while True:
        # Init ulang Pin yang digunakan
        button_pin_1, button_pin_2, button_pin_3 = setup_gpio()
        print("rezero: ", counter_rezero)
        while True: #loop terus sampe dapat nilai 
            print("masih membaca sensor")
            temperature, mm_distance = ul.read_distance_and_temperature()
            print("temp ", temperature)
            print("distance ", mm_distance)
            if temperature is not None and mm_distance is not None:
                print("berhasil membaca")
                break
        
        if show_normal_value == False and GPIO.input(button_pin_1) == GPIO.LOW and GPIO.input(button_pin_2) == GPIO.LOW and GPIO.input(button_pin_3) == GPIO.HIGH:
            lcd_display("Button Pressed!!", "Button: Blue") #Tampilkan Raw
            show_normal_value = True
            time.sleep(3)
            
        if show_normal_value == True or show_raw_value == True:
            counter_rezero = 0 #reset counter zeroing saat mode show_normal_value atau show_raw_value
            
        #Jika mode show value aktif
        if show_normal_value == True:
            trash_weight = read_trash(1, "normal") #false itu cuman baca biasa, tanpa proses 
            button_pin_1, button_pin_2, button_pin_3 = setup_gpio()
            if GPIO.input(button_pin_1) == GPIO.LOW and GPIO.input(button_pin_2) == GPIO.LOW and GPIO.input(button_pin_3) == GPIO.HIGH:
                show_normal_value = False
                show_raw_value = True
                lcd_display("Button Pressed!!", "Button: Blue") #Tampilkan Raw
                time.sleep(3) #delay biar ngga kepencet blue 2x (debounce)          
        #Jika mode kalibrasi aktif
        elif show_raw_value == True:
            raw_value = round((read_raw()-zeroing),1)
            lcd_display("Raw Value:", str(raw_value)) #Tampilkan Raw
            button_pin_1, button_pin_2, button_pin_3 = setup_gpio()
            if GPIO.input(button_pin_1) == GPIO.LOW and GPIO.input(button_pin_2) == GPIO.LOW and GPIO.input(button_pin_3) == GPIO.HIGH:
                show_raw_value = False
                lcd_display("Button Pressed!!", "Button: Blue") #Close Menu
                time.sleep(3) #delay biar ngga kepencet blue 2x (debounce)            
        else: #jika bukan mode kalibrasi
            if GPIO.input(button_pin_1) == GPIO.HIGH and GPIO.input(button_pin_2) == GPIO.LOW and GPIO.input(button_pin_3) == GPIO.LOW and status_start == False:
                status_start = True
                lcd_display("Button Pressed!!", "Button: Red") #Tampilkan Raw
                time.sleep(3) #delay biar ngga kepencet ready
            elif GPIO.input(button_pin_1) == GPIO.HIGH and GPIO.input(button_pin_2) == GPIO.LOW and GPIO.input(button_pin_3) == GPIO.LOW and status_start == True:
                status_start = False
                lcd_display("Button Pressed!!", "Button: Red") #Tampilkan Raw
                time.sleep(3) #delay biar ngga kepencet ready
            
            #jika button_2 (tengah) ditekan atau ultrasonic nilainya 5cm (50mm) di mode ready, maka proses akan dimulai 
            if ((GPIO.input(button_pin_1) == GPIO.LOW and GPIO.input(button_pin_2) == GPIO.HIGH and GPIO.input(button_pin_3) == GPIO.LOW) or mm_distance <= 200) and status_start == True:         
                if GPIO.input(button_pin_2) == GPIO.HIGH:
                    lcd_display("Button Pressed!!", "Button: Yellow") #Tampilkan Raw
                    time.sleep(1)
                else:
                    lcd_display("Object Detected!", "Ultrasonic") #Tampilkan Raw
                print("start process ..")
                process() #proses aktuator dan firebase
                #init ulang button, karena remapping gpio dari loadcell
                button_pin_1, button_pin_2, button_pin_3 = setup_gpio()
            elif status_start == True:
                counter_rezero += 1
                if counter_rezero >= 10:
                    zeroing = read_raw() #update nilai zero setiap loop mode idle
                    lcd_display("Mode: Zeroing", "Done Rezero !!")
                    counter_rezero = 0
                    time.sleep(1)
                
                lcd_display("Mode: Ready", "Detecting Object")
                #init ulang button, karena remapping gpio dari loadcell
                button_pin_1, button_pin_2, button_pin_3 = setup_gpio()
            else:
                print("idle")
                counter_rezero += 1
                if counter_rezero >= 10:
                    zeroing = read_raw() #update nilai zero setiap loop mode idle
                    lcd_display("Mode: Zeroing", "Done Rezero !!")
                    counter_rezero = 0
                    time.sleep(1)
                
                lcd_display("Click Button Red", "To Start Process")
                #init ulang button, karena remapping gpio dari loadcell
                button_pin_1, button_pin_2, button_pin_3 = setup_gpio()
pwm_cw.stop()
pwm_ccw.stop()
pwm.stop()
GPIO.cleanup()
