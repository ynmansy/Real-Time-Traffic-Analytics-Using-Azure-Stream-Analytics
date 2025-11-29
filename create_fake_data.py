import pyodbc
from faker import Faker
import random
from datetime import datetime, timedelta
from itertools import islice

# -----------------------------
# 1️⃣ Database Connection Setup
# -----------------------------
SERVER = r"HOPA\SQLEXPRESS"  # ضع اسم السيرفر هنا
DATABASE = "TrafficAnalysis"

CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

fake = Faker("ar_EG")  # 🇪🇬 Egyptian locale

# -----------------------------
# 2️⃣ Parameters (Requested: Option 1)
# -----------------------------
NUM_DRIVERS = 10_000
NUM_VEHICLES = 10_000
NUM_ROADS = 100           # زيادة طفيفة لتوزيع الكاميرات والسرعات
NUM_CAMERAS = 400        # توزيع أفضل للكاميرات
NUM_SPEED_LIMITS = 500
NUM_SCANS = 50_000

# Batch sizes (تعديل حسب أداء السيرفر)
BATCH_SIZE_DRIVERS = 1000
BATCH_SIZE_VEHICLES = 1000
BATCH_SIZE_ROADS = 200
BATCH_SIZE_CAMERAS = 500
BATCH_SIZE_SPEED = 500
BATCH_SIZE_SCANS = 5000
BATCH_SIZE_CITATIONS = 2000

# -----------------------------
# 3️⃣ Uniqueness trackers
# -----------------------------
used_plates = set()
used_national_ids = set()
used_license_numbers = set()

# -----------------------------
# 4️⃣ Helper functions
# -----------------------------
def chunked(iterable, size):
    """Yield successive chunks from iterable of length size."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk

def generate_egyptian_national_id():
    """Generate realistic 14-digit Egyptian National ID and ensure uniqueness locally."""
    while True:
        year = random.randint(1970, 2005)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        gov_code = random.randint(1, 27)
        serial = random.randint(10000, 99999)
        century = 3 if year >= 2000 else 2
        check_digit = random.randint(0, 9)
        national_id = f"{century}{str(year)[-2:]:0>2}{month:02d}{day:02d}{gov_code:02d}{serial}{check_digit}"
        if national_id not in used_national_ids:
            used_national_ids.add(national_id)
            return national_id

def generate_egyptian_phone():
    prefix = random.choice(["010", "011", "012", "015"])
    number = ''.join(random.choices("0123456789", k=8))
    return prefix + number

def generate_license_number():
    """Generate pseudo-unique license numbers (tracked locally)."""
    while True:
        lic = f"LIC-{random.randint(1000, 9999)}-{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(10,99)}"
        if lic not in used_license_numbers:
            used_license_numbers.add(lic)
            return lic

def generate_driver():
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
        generate_license_number(),
        issue,
        expiry,
        random.choice(["A", "B", "C"]),
        random.choice(["Private", "Professional", "Taxi", "Truck"]),
        random.randint(0, 10),
    )

def generate_vehicle(driver_id):
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
        "El Salam Road", "Autostrad Road", "Airport Road", "Alex Desert Road",
        "Salah Salem", "El Nozha", "Al Gamaa"
    ]
    return (
        random.choice(road_names) + f" #{random.randint(1,500)}",
        random.choice(["Highway", "Street", "Bridge"]),
        round(random.uniform(0.5, 200.0), 2),
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
    
    # Speed flag
    if random.random() < 0.7:
        recorded_speed = round(random.uniform(max_speed * 0.5, max_speed), 2)
        sf_flag = 0
    else:
        recorded_speed = round(random.uniform(max_speed * 1.01, max_speed * 1.6), 2)
        sf_flag = 1

    sb_flag = 1 if random.random() < 0.10 else 0
    ph_flag = 1 if random.random() < 0.15 else 0
    legal_flag = 0 if sf_flag == 1 or sb_flag == 1 or ph_flag == 1 else 1

    return (
        vehicle_id, camera_id, scan_time, lane,
        gps_long, gps_lat, recorded_speed, legal_flag, sf_flag, sb_flag, ph_flag
    )

# -----------------------------
# 5️⃣ Main insertion routine (optimized, NO DELETE)
# -----------------------------
def insert_data():
    cnxn = pyodbc.connect(CONNECTION_STRING)
    cursor = cnxn.cursor()

    print("🚀 Starting large data insertion WITHOUT deleting old records...")
    print(f"Drivers: {NUM_DRIVERS}, Vehicles: {NUM_VEHICLES}, Scans: {NUM_SCANS}")

    # ---------- 1. Insert DRIVERS in batches ----------
    print("🚗 Inserting drivers (batches)...")
    def gen_drivers():
        for _ in range(NUM_DRIVERS):
            yield generate_driver()

    for i, batch in enumerate(chunked(gen_drivers(), BATCH_SIZE_DRIVERS), start=1):
        try:
            cursor.executemany("""
                INSERT INTO DRIVER (National_ID, First_Name, Last_Name, Date_of_Birth,
                Address, Phone_Number, License_Number, License_Issue_Date,
                License_Expiry_Date, License_Class, Attribute_Data, Points_on_License)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            cnxn.commit()
        except Exception as e:
            print(f"⚠️ Error inserting driver batch {i}: {e}")
            cnxn.rollback()

        if i % 5 == 0:
            print(f"  • Inserted {i * BATCH_SIZE_DRIVERS} drivers so far...")

    # Refresh driver ids
    cursor.execute("SELECT Driver_ID FROM DRIVER")
    driver_ids = [r[0] for r in cursor.fetchall()]
    if not driver_ids:
        raise RuntimeError("No drivers found after insert — check DB or constraints.")
    print(f"  → Total drivers in DB now: {len(driver_ids)}")

    # ---------- 2. Insert VEHICLES in batches ----------
    print("🚙 Inserting vehicles (batches)...")
    def gen_vehicles():
        for _ in range(NUM_VEHICLES):
            yield generate_vehicle(random.choice(driver_ids))

    for i, batch in enumerate(chunked(gen_vehicles(), BATCH_SIZE_VEHICLES), start=1):
        try:
            cursor.executemany("""
                INSERT INTO VEHICLE (Driver_ID, Plate_Number, Registration_State,
                Vehicle_Type, Model, Color, Year)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, batch)
            cnxn.commit()
        except Exception as e:
            print(f"⚠️ Error inserting vehicle batch {i}: {e}")
            cnxn.rollback()

        if i % 5 == 0:
            print(f"  • Inserted {i * BATCH_SIZE_VEHICLES} vehicles so far...")

    cursor.execute("SELECT Vehicle_ID, Vehicle_Type FROM VEHICLE")
    vehicle_data = cursor.fetchall()
    if not vehicle_data:
        raise RuntimeError("No vehicles found after insert — check DB or constraints.")
    print(f"  → Total vehicles in DB now: {len(vehicle_data)}")

    # ---------- 3. Insert ROADS ----------
    print("🛣️ Inserting roads...")
    roads = [generate_road() for _ in range(NUM_ROADS)]
    for i, batch in enumerate(chunked(roads, BATCH_SIZE_ROADS), start=1):
        try:
            cursor.executemany("""
                INSERT INTO ROAD (Road_Name, Road_Type, Length, Lanes, Region,
                Start_Long, Start_Lat, End_Long, End_Lat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            cnxn.commit()
        except Exception as e:
            print(f"⚠️ Error inserting road batch {i}: {e}")
            cnxn.rollback()

    cursor.execute("SELECT Road_ID FROM ROAD")
    road_ids = [r[0] for r in cursor.fetchall()]
    print(f"  → Total roads in DB now: {len(road_ids)}")

    # ---------- 4. Insert CAMERAS ----------
    print("📷 Inserting cameras...")
    cameras = [generate_camera(random.choice(road_ids)) for _ in range(NUM_CAMERAS)]
    for i, batch in enumerate(chunked(cameras, BATCH_SIZE_CAMERAS), start=1):
        try:
            cursor.executemany("""
                INSERT INTO CAMERA (Road_ID, Latitude, Longitude, Location_Description,
                Resolution, Status, Installation_Date, Camera_Type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            cnxn.commit()
        except Exception as e:
            print(f"⚠️ Error inserting camera batch {i}: {e}")
            cnxn.rollback()

    cursor.execute("SELECT Camera_ID, Road_ID FROM CAMERA")
    camera_data = cursor.fetchall()
    print(f"  → Total cameras in DB now: {len(camera_data)}")

    # ---------- 5. Insert SPEED_LIMITS ----------
    print("🚦 Inserting speed limits...")
    speed_limits = [generate_speed_limit(random.choice(road_ids)) for _ in range(NUM_SPEED_LIMITS)]
    for i, batch in enumerate(chunked(speed_limits, BATCH_SIZE_SPEED), start=1):
        try:
            cursor.executemany("""
                INSERT INTO SPEED_LIMIT (Road_ID, Vehicle_Type, Max_Speed)
                VALUES (?, ?, ?)
            """, batch)
            cnxn.commit()
        except Exception as e:
            print(f"⚠️ Error inserting speed limit batch {i}: {e}")
            cnxn.rollback()

    cursor.execute("SELECT Road_ID, Vehicle_Type, Max_Speed FROM SPEED_LIMIT")
    speed_lookup = {(r[0], r[1]): r[2] for r in cursor.fetchall()}
    print(f"  → Speed limits mapping loaded: {len(speed_lookup)} entries")

    # ---------- 6. Generate & Insert SCANS (large) ----------
    print("📸 Generating and inserting scans (batches)...")
    def gen_scans():
        for _ in range(NUM_SCANS):
            vehicle_id, v_type = random.choice(vehicle_data)
            camera_id, road_id = random.choice(camera_data)
            max_speed = speed_lookup.get((road_id, v_type), random.randint(80, 120))
            yield generate_scan(vehicle_id, camera_id, road_id, v_type, max_speed)

    total_scans_inserted = 0
    for i, batch in enumerate(chunked(gen_scans(), BATCH_SIZE_SCANS), start=1):
        try:
            cursor.executemany("""
                INSERT INTO SCAN (Vehicle_ID, Camera_ID, Scan_DateTime, Lane_Number,
                GPS_Longitude, GPS_Latitude, Speed_Recorded, Legal_Flag, SF_Flag, SB_Flag, PH_Flag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            cnxn.commit()
            total_scans_inserted += len(batch)
        except Exception as e:
            print(f"⚠️ Error inserting scan batch {i}: {e}")
            cnxn.rollback()

        print(f"  • Inserted {total_scans_inserted}/{NUM_SCANS} scans so far...")

    # ---------- 7. Ensure VIOLATION types exist ----------
    print("📜 Ensuring violation types exist...")
    violation_types = [
        ("SPD01", "Speeding (Low)", "Exceeding limit by < 20%", 0, 150.00, 1, "Active"),
        ("SPD02", "Speeding (High)", "Exceeding limit by > 20%", 3, 300.00, 1, "Active"),
        ("SBT01", "No Seatbelt", "Driver failed to wear seatbelt", 1, 100.00, 1, "Active"),
        ("PHN01", "Phone Usage", "Using handheld mobile device", 3, 500.00, 1, "Active")
    ]
    for v in violation_types:
        cursor.execute("SELECT 1 FROM VIOLATION WHERE Violation_Code = ?", v[0])
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO VIOLATION (Violation_Code, Violation_Type, Description, Points, Base_Fine, Active_Flag, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, v)
            cnxn.commit()

    cursor.execute("SELECT Violation_ID, Violation_Code, Base_Fine FROM VIOLATION")
    viol_map = {row.Violation_Code: (row.Violation_ID, float(row.Base_Fine)) for row in cursor.fetchall()}

    # ---------- 8. Generate CITATIONS from illegal scans ----------
    print("📝 Generating citations from illegal scans (this may take a while)...")
    sql_query = """
        SELECT 
            S.Scan_ID, S.Scan_DateTime, S.SF_Flag, S.SB_Flag, S.PH_Flag, S.Speed_Recorded, 
            V.Vehicle_Type, C.Road_ID
        FROM SCAN S
        JOIN VEHICLE V ON S.Vehicle_ID = V.Vehicle_ID
        JOIN CAMERA C ON S.Camera_ID = C.Camera_ID
        WHERE S.Legal_Flag = 0
    """
    cursor.execute(sql_query)
    illegal_scans = cursor.fetchall()
    print(f"  → Found {len(illegal_scans)} illegal scans to process for citations.")

    citations = []
    for row in illegal_scans:
        scan_id, scan_dt, sf_flag, sb_flag, ph_flag, recorded_speed, v_type, road_id = row
        violations_to_issue = []

        if sf_flag:
            limit = float(speed_lookup.get((road_id, v_type), 90.0))
            speed_val = float(recorded_speed)
            violations_to_issue.append("SPD02" if speed_val > limit * 1.2 else "SPD01")
        if sb_flag:
            violations_to_issue.append("SBT01")
        if ph_flag:
            violations_to_issue.append("PHN01")

        for v_code in violations_to_issue:
            viol_id, fine_amount = viol_map[v_code]
            citation_date = scan_dt.date()
            citation_time = scan_dt.time()
            due_date = citation_date + timedelta(days=14)

            rand_pay = random.random()
            late_fee = 0.0
            payment_date = None

            if rand_pay < 0.60:
                payment_date = citation_date + timedelta(days=random.randint(0, 13))
            elif rand_pay < 0.80:
                payment_date = due_date + timedelta(days=random.randint(1, 20))
                late_fee = 100.00
            else:
                if datetime.now().date() > due_date:
                    late_fee = 100.00

            total_amount = fine_amount + late_fee

            citations.append((
                scan_id, viol_id, citation_date, citation_time,
                fine_amount, late_fee, total_amount, due_date, payment_date
            ))

    # Insert citations in batches
    total_citations = 0
    for i, batch in enumerate(chunked(citations, BATCH_SIZE_CITATIONS), start=1):
        try:
            cursor.executemany("""
                INSERT INTO CITATION (Scan_ID, Violation_ID, Citation_Date, Citation_Time,
                Fine_Amount, Late_Fee, Total_Amount, Payment_Due_Date, Payment_Date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            cnxn.commit()
            total_citations += len(batch)
        except Exception as e:
            print(f"⚠️ Error inserting citation batch {i}: {e}")
            cnxn.rollback()

        print(f"  • Inserted {total_citations}/{len(citations)} citations so far...")

    cnxn.close()
    print("✅ Large data insertion finished. Check DB for results.")

# -----------------------------
# 6️⃣ Run
# -----------------------------
if __name__ == "__main__":
    insert_data()
