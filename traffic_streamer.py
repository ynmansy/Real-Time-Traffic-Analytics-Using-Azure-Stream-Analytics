import json
import random
import time
import datetime
from azure.eventhub import EventHubProducerClient, EventData
from faker import Faker

# -----------------------------
# 1️⃣ Azure Configuration
# -----------------------------
# PASTE YOUR AZURE CONNECTION STRING BELOW
CONNECTION_STRING = "XXXXXXXXXX"
EVENT_HUB_NAME = "traffic-data-stream"

fake = Faker("ar_EG")  # Keep the Egyptian localization

# -----------------------------
# 2️⃣ Data Generation Helpers (Your Logic)
# -----------------------------

used_plates = set()

def generate_vehicle():
    """Generates a random vehicle object."""
    while True:
        plate_number = f"EGY-{random.randint(1000, 9999)}-{random.randint(10,99)}"
        # Simple collision check (reset if set gets too big for memory in long run)
        if len(used_plates) > 10000: used_plates.clear()
        if plate_number not in used_plates:
            used_plates.add(plate_number)
            break

    return {
        "vehicle_id": fake.uuid4(),
        "plate_number": plate_number,
        "registration_state": random.choice(["Cairo", "Giza", "Alexandria", "Dakahlia", "Qalyubia", "Assiut", "Port Said"]),
        "vehicle_type": random.choice(["Car", "Truck", "Bus", "Motorcycle"]),
        "model": random.choice(["Toyota", "Hyundai", "Kia", "BMW", "Mercedes", "Nissan", "Chevrolet"]),
        "color": random.choice(["White", "Black", "Silver", "Blue", "Red", "Gray"]),
        "year": random.randint(2005, 2024)
    }

def generate_camera():
    """Generates a random camera location."""
    road_names = ["Ring Road", "October Bridge", "Tahrir Street", "Corniche Road", "Alex Desert Road"]
    return {
        "camera_id": fake.uuid4(),
        "road_name": random.choice(road_names),
        "latitude": round(random.uniform(29.0, 33.0), 6),
        "longitude": round(random.uniform(25.0, 31.0), 6),
        "speed_limit": random.choice([60, 80, 90, 100, 120])
    }

# Pre-generate some assets so the simulation feels consistent (same cars passing by)
print("Initializing simulation assets...")
VEHICLE_POOL = [generate_vehicle() for _ in range(50)]
CAMERA_POOL = [generate_camera() for _ in range(10)]

def generate_traffic_event():
    """
    Simulates a single camera scan event.
    Combines a random vehicle passing a random camera.
    """
    vehicle = random.choice(VEHICLE_POOL)
    camera = random.choice(CAMERA_POOL)
    
    current_time = datetime.datetime.utcnow()
    
    # Calculate Speed logic (Your original logic adapted)
    limit = camera['speed_limit']
    
    # 70% chance legal speed, 30% chance speeding
    if random.random() < 0.7:
        recorded_speed = round(random.uniform(limit * 0.5, limit), 2)
    else:
        recorded_speed = round(random.uniform(limit * 1.01, limit * 1.6), 2)

    # Flags
    sf_flag = 1 if recorded_speed > limit else 0
    sb_flag = 1 if random.random() < 0.10 else 0 # Seatbelt
    ph_flag = 1 if random.random() < 0.15 else 0 # Phone usage

    # Construct the JSON Payload
    event_payload = {
        "event_id": fake.uuid4(),
        "timestamp": current_time.isoformat(),
        "camera_data": camera,
        "vehicle_data": vehicle,
        "telemetry": {
            "speed": recorded_speed,
            "lane": random.randint(1, 4),
            "is_speeding": sf_flag,
            "no_seatbelt": sb_flag,
            "using_phone": ph_flag
        }
    }
    return event_payload

# -----------------------------
# 3️⃣ Azure Event Hub Sender
# -----------------------------
def run_simulation():
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STRING, 
        eventhub_name=EVENT_HUB_NAME
    )

    print(f"🚀 Starting Traffic Stream to Azure Event Hub: {EVENT_HUB_NAME}")
    print("Press Ctrl+C to stop.\n")

    try:
        with producer:
            while True:
                batch = producer.create_batch()
                
                # Send a batch of 3 events at a time
                for _ in range(3):
                    data = generate_traffic_event()
                    json_data = json.dumps(data) # Convert dict to JSON string
                    batch.add(EventData(json_data))
                    
                    # Print snippet to console to verify it's working
                    print(f"[{data['timestamp']}] {data['vehicle_data']['plate_number']} - {data['telemetry']['speed']}km/h (Limit: {data['camera_data']['speed_limit']})")

                producer.send_batch(batch)
                time.sleep(2) # Wait 2 seconds between batches

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_simulation()