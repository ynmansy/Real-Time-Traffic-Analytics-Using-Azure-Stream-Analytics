import pyodbc
from faker import Faker
import random
from datetime import datetime, timedelta

# -----------------------------
# 1️⃣ Database Connection Setup
# -----------------------------
SERVER = r"HOPA\SQLEXPRESS"
DATABASE = "TrafficAnalysis"

CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

fake = Faker("ar_EG")  # 🇪🇬 Egyptian locale

# -----------------------------
# 2️⃣ Parameters
# -----------------------------
NUM_DRIVERS = 50
NUM_VEHICLES = 100
NUM_ROADS = 15
NUM_CAMERAS = 40
NUM_SPEED_LIMITS = 50
NUM_SCANS = 1000

# -----------------------------
# 3️⃣ Helper Functions
# -----------------------------

def generate_egyptian_national_id():
    """Generate realistic 14-digit Egyptian National ID."""
    year = random.randint(1970, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    gov_code = random.randint(1, 27)
    serial = random.randint(10000, 99999)
    century = 3 if year >= 2000 else 2
    check_digit = random.randint(0, 9)
    national_id = f"{century}{str(year)[-2:]:0>2}{month:02d}{day:02d}{gov_code:02d}{serial}{check_digit}"
    return national_id


def generate_egyptian_phone():
    """Generate Egyptian mobile number (always 11 digits)."""
    prefix = random.choice(["010", "011", "012", "015"])
    number = ''.join(random.choices("0123456789", k=8))
    return prefix + number


def generate_driver():
    """Generate realistic driver data for Egypt."""
    first = fake.first_name()
    last = fake.last_name()
    dob = fake.date_of_birth(minimum_age=22, maximum_age=60)
    issue = fake.date_between(start_date='-10y', end_date='-1y')
    expiry = issue + timedelta(days=random.randint(365, 3650))

    return (
        generate_egyptian_national_id(),
        first,
        last,
        dob,
        fake.address().replace("\n", ", "),
        generate_egyptian_phone(),
        fake.unique.bothify(text="LIC-####-????"),
        issue,
        expiry,
        random.choice(["A", "B", "C"]),
        random.choice(["Private", "Professional", "Taxi", "Truck"]),
        random.randint(0, 10),
    )


used_plates = set()

def generate_vehicle(driver_id):
    """Generate unique Egyptian-style vehicle plate linked to a driver."""
    while True:
        plate_number = f"EGY-{random.randint(1000, 9999)}-{random.randint(10,99)}"
        if plate_number not in used_plates:
            used_plates.add(plate_number)
            break

    registration_state = random.choice(["Cairo", "Giza", "Alexandria", "Dakahlia", "Qalyubia", "Assiut", "Port Said"])
    vehicle_type = random.choice(["Car", "Truck", "Bus", "Motorcycle"])
    model = random.choice(["Toyota", "Hyundai", "Kia", "BMW", "Mercedes", "Nissan", "Chevrolet"])
    color = random.choice(["White", "Black", "Silver", "Blue", "Red", "Gray"])
    year = random.randint(2005, 2024)
    
    return (driver_id, plate_number, registration_state, vehicle_type, model, color, year)


def generate_road():
    regions = ["Cairo", "Giza", "Alexandria", "Mansoura", "Tanta", "Assiut", "Port Said", "Minya"]
    road_names = [
        "Ring Road", "October Bridge", "Tahrir Street", "Corniche Road",
        "El Salam Road", "Autostrad Road", "Airport Road", "Alex Desert Road"
    ]
    return (
        random.choice(road_names),
        random.choice(["Highway", "Street", "Bridge"]),
        round(random.uniform(1.0, 200.0), 2),
        random.randint(2, 8),
        random.choice(regions),
        round(random.uniform(29.0, 33.0), 6),
        round(random.uniform(25.0, 31.0), 6),
        round(random.uniform(29.0, 33.0), 6),
        round(random.uniform(25.0, 31.0), 6),
    )


def generate_camera(road_id):
    return (
        road_id,
        round(random.uniform(29.0, 33.0), 6),
        round(random.uniform(25.0, 31.0), 6),
        random.choice(["Intersection", "Tunnel", "Bridge", "Highway Exit"]),
        random.choice(["1080p", "4K"]),
        random.choice(["Active", "Maintenance", "Offline"]),
        fake.date_between(start_date='-5y', end_date='today'),
        random.choice(["Speed", "ANPR", "Traffic Flow"])
    )


def generate_speed_limit(road_id):
    return (
        road_id,
        random.choice(["Car", "SUV", "Truck", "Bus", "Motorcycle"]),
        round(random.uniform(60, 120), 2),
    )


def generate_scan(vehicle_id, camera_id, road_id, vehicle_type, max_speed):
    max_speed = float(max_speed)
    scan_time = datetime.now() - timedelta(days=random.randint(0, 30),
                                           hours=random.randint(0, 23),
                                           minutes=random.randint(0, 59))
    lane = random.randint(1, 4)
    gps_long = round(random.uniform(29.0, 33.0), 6)
    gps_lat = round(random.uniform(25.0, 31.0), 6)
    recorded_speed = round(random.uniform(max_speed * 0.7, max_speed * 1.4), 2)

    legal_flag = 1 if recorded_speed <= max_speed else 0
    sf_flag = 1 if recorded_speed > max_speed * 1.2 else 0
    sb_flag = 1 if recorded_speed > max_speed * 1.4 else 0

    return (
        vehicle_id, camera_id, scan_time, lane,
        gps_long, gps_lat, recorded_speed, legal_flag, sf_flag, sb_flag
    )


# -----------------------------
# 4️⃣ Insert Data into Database
# -----------------------------
def insert_data():
    cnxn = pyodbc.connect(CONNECTION_STRING)
    cursor = cnxn.cursor()

    # Optional: Clear tables before inserting (for re-runs)
    print("🧹 Clearing old data...")
    cursor.execute("DELETE FROM SCAN")
    cursor.execute("DELETE FROM SPEED_LIMIT")
    cursor.execute("DELETE FROM CAMERA")
    cursor.execute("DELETE FROM ROAD")
    cursor.execute("DELETE FROM VEHICLE")
    cursor.execute("DELETE FROM DRIVER")
    cnxn.commit()

    # DRIVER
    print("🚗 Inserting drivers...")
    fake.unique.clear()
    drivers = [generate_driver() for _ in range(NUM_DRIVERS)]
    cursor.executemany("""
        INSERT INTO DRIVER (National_ID, First_Name, Last_Name, Date_of_Birth,
        Address, Phone_Number, License_Number, License_Issue_Date,
        License_Expiry_Date, License_Class, Attribute_Data, Points_on_License)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, drivers)
    cnxn.commit()

    cursor.execute("SELECT Driver_ID FROM DRIVER")
    driver_ids = [r[0] for r in cursor.fetchall()]

    # VEHICLE
    print("🚙 Inserting vehicles...")
    vehicles = [generate_vehicle(random.choice(driver_ids)) for _ in range(NUM_VEHICLES)]
    cursor.executemany("""
        INSERT INTO VEHICLE (Driver_ID, Plate_Number, Registration_State,
        Vehicle_Type, Model, Color, Year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, vehicles)
    cnxn.commit()

    cursor.execute("SELECT Vehicle_ID, Vehicle_Type FROM VEHICLE")
    vehicle_data = cursor.fetchall()

    # ROAD
    print("🛣️ Inserting roads...")
    roads = [generate_road() for _ in range(NUM_ROADS)]
    cursor.executemany("""
        INSERT INTO ROAD (Road_Name, Road_Type, Length, Lanes, Region,
        Start_Long, Start_Lat, End_Long, End_Lat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, roads)
    cnxn.commit()

    cursor.execute("SELECT Road_ID FROM ROAD")
    road_ids = [r[0] for r in cursor.fetchall()]

    # CAMERA
    print("📷 Inserting cameras...")
    cameras = [generate_camera(random.choice(road_ids)) for _ in range(NUM_CAMERAS)]
    cursor.executemany("""
        INSERT INTO CAMERA (Road_ID, Latitude, Longitude, Location_Description,
        Resolution, Status, Installation_Date, Camera_Type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, cameras)
    cnxn.commit()

    cursor.execute("SELECT Camera_ID, Road_ID FROM CAMERA")
    camera_data = cursor.fetchall()

    # SPEED LIMIT
    print("🚦 Inserting speed limits...")
    speed_limits = [generate_speed_limit(random.choice(road_ids)) for _ in range(NUM_SPEED_LIMITS)]
    cursor.executemany("""
        INSERT INTO SPEED_LIMIT (Road_ID, Vehicle_Type, Max_Speed)
        VALUES (?, ?, ?)
    """, speed_limits)
    cnxn.commit()

    cursor.execute("SELECT Road_ID, Vehicle_Type, Max_Speed FROM SPEED_LIMIT")
    speed_lookup = {(r[0], r[1]): r[2] for r in cursor.fetchall()}

    # SCAN
    print("📸 Generating scans...")
    scans = []
    for _ in range(NUM_SCANS):
        vehicle_id, v_type = random.choice(vehicle_data)
        camera_id, road_id = random.choice(camera_data)
        max_speed = speed_lookup.get((road_id, v_type), random.randint(80, 120))
        scans.append(generate_scan(vehicle_id, camera_id, road_id, v_type, max_speed))

    cursor.executemany("""
        INSERT INTO SCAN (Vehicle_ID, Camera_ID, Scan_DateTime, Lane_Number,
        GPS_Longitude, GPS_Latitude, Speed_Recorded, Legal_Flag, SF_Flag, SB_Flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, scans)
    cnxn.commit()

    cnxn.close()
    print("✅ All data inserted successfully and consistently!")


# -----------------------------
# 5️⃣ Run
# -----------------------------
if __name__ == "__main__":
    insert_data()

