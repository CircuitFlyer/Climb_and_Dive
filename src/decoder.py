import struct
import csv
import os

def decode_bin_to_csv(bin_filename="flight_log.bin", csv_filename="flight_log.csv"):
    record_format = "<fffffff"
    record_size = struct.calcsize(record_format)

    if not os.path.exists(bin_filename):
        print(f"File {bin_filename} not found!")
        return

    print(f"Start converting {bin_filename}...")

    with open(bin_filename, "rb") as f_in, open(csv_filename, "w", newline="") as f_out:
        writer = csv.writer(f_out)
        
        writer.writerow(["timestamp", "rpm", "wing_accel", "vert_accel", "climb_boost", "overhead_boost", "corner_boost"])

        records_processed = 0
        while True:            
            chunk = f_in.read(record_size)
            
            if len(chunk) < record_size:
                break
            
            data = struct.unpack(record_format, chunk)
            
            # Check for NaN divider
            if any(str(x).lower() == 'nan' for x in data):
                writer.writerow(["---", "---", "---", "---", "---", "---", "---"])
                continue

            formatted_data = [
                f"{data[0]:.5f}",  # timestamp
                f"{data[1]:.0f}",  # rpm
                f"{data[2]:.5f}",  # wing_accel
                f"{data[3]:.5f}",  # vert_accel
                f"{data[4]:.0f}",  # climb_boost
                f"{data[5]:.0f}",  # overhead_boost
                f"{data[6]:.0f}"   # corner_boost
            ]
            writer.writerow(formatted_data)
            records_processed += 1

    print(f"Done. Saved result into {csv_filename}.")

if __name__ == "__main__":
    decode_bin_to_csv()