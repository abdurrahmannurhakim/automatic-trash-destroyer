# Nama file: read_config.py

def read_config(filename):
    config_values = {}
    with open(filename, 'r') as file:
        for line in file:
            # Menghilangkan karakter spasi dan newline
            line = line.strip()
            if '=' in line:
                key, value = line.split('=')
                key = key.strip()
                value = value.strip()
                config_values[key] = value
    return config_values

def convert_to_float(config_values):
    try:
        actual_value = float(config_values['actual_value'])
    except KeyError:
        print("Error: 'mass' tidak ditemukan di file config.")
        actual_value = None
    except ValueError:
        print("Error: 'mass' tidak dapat dikonversi ke float.")
        actual_value = None

    try:
        raw_value = float(config_values['raw_value'])
    except KeyError:
        print("Error: 'raw_value' tidak ditemukan di file config.")
        raw_value = None
    except ValueError:
        print("Error: 'raw_value' tidak dapat dikonversi ke float.")
        raw_value = None
        
    try:
        time_constant = int(config_values['time_constant'])
    except KeyError:
        print("Error: 'raw_value' tidak ditemukan di file config.")
        time_constant = None
    except ValueError:
        print("Error: 'raw_value' tidak dapat dikonversi ke float.")
        time_constant = None

    return actual_value, raw_value, time_constant


