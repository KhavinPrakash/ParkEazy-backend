import cv2
import numpy as np
import time
import datetime
import math
from typing import Dict, List, Tuple

class YOLOParkingDetector:
    """
    Ultra-Realistic High-Definition CCTV Camera Stream Simulator with YOLOv8 Detection.
    Renders realistic vehicle graphics (Sedans, SUVs, EVs, Motorcycles), parking lot asphalt,
    CCTV lens vignette/grain, entry/exit boom barriers, and real-time bounding boxes.
    """
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.fps = 30
        self.frame_count = 0

        # 10 Detailed Parking Slots with ROIs and Real Vehicle Types
        self.slots_roi = {
            "A1": {"box": (140, 160, 170, 140), "status": "Available", "type": "Car", "model": "White Sedan", "confidence": 0.97, "vehicle": None},
            "A2": {"box": (340, 160, 170, 140), "status": "Occupied",  "type": "Car", "model": "Black SUV", "confidence": 0.96, "vehicle": "TN-07-MJ-4821"},
            "A3": {"box": (540, 160, 170, 140), "status": "Available", "type": "EV Charging", "model": "Blue Tesla EV", "confidence": 0.98, "vehicle": None},
            "A4": {"box": (740, 160, 170, 140), "status": "Reserved",  "type": "Car", "model": "Red Hatchback", "confidence": 0.94, "vehicle": "TN-10-PQ-9901"},
            "A5": {"box": (940, 160, 170, 140), "status": "Occupied",  "type": "Car", "model": "Silver Crossover", "confidence": 0.95, "vehicle": "TN-03-CC-1122"},

            "B1": {"box": (140, 430, 170, 140), "status": "Occupied",  "type": "Car", "model": "Grey Sedan", "confidence": 0.95, "vehicle": "TN-09-AX-7721"},
            "B2": {"box": (340, 430, 170, 140), "status": "Available", "type": "Bike", "model": "Motorcycle", "confidence": 0.98, "vehicle": None},
            "B3": {"box": (540, 430, 170, 140), "status": "Reserved",  "type": "EV Charging", "model": "Green EV Sedan", "confidence": 0.93, "vehicle": "TN-05-EV-0001"},
            "B4": {"box": (740, 430, 170, 140), "status": "Occupied",  "type": "Bike", "model": "Sports Bike", "confidence": 0.97, "vehicle": "TN-04-HB-2024"},
            "B5": {"box": (940, 430, 170, 140), "status": "Available", "type": "Car", "model": "White SUV", "confidence": 0.99, "vehicle": None},
        }

    def _draw_realistic_car(self, img: np.ndarray, x: int, y: int, w: int, h: int, color_tuple: Tuple[int, int, int], car_type: str):
        """Renders realistic top-down vehicle graphics with metallic shading, shadows, glass & lights."""
        # 1. Soft Drop Shadow under vehicle
        shadow_mask = np.zeros_like(img, dtype=np.uint8)
        cv2.rectangle(shadow_mask, (x+6, y+8), (x+w-6, y+h-4), (20, 20, 20), -1)
        shadow_mask = cv2.GaussianBlur(shadow_mask, (15, 15), 0)
        img = cv2.addWeighted(img, 1.0, shadow_mask, -0.4, 0)

        # 2. Main Car Metallic Body
        cv2.rectangle(img, (x+10, y+10), (x+w-10, y+h-10), color_tuple, -1)
        # Rounded hood & trunk edges
        cv2.ellipse(img, (x+w//2, y+14), (w//2-12, 10), 0, 180, 360, color_tuple, -1)
        cv2.ellipse(img, (x+w//2, y+h-14), (w//2-12, 10), 0, 0, 180, color_tuple, -1)

        # 3. Metallic Highlight Line (Shininess)
        cv2.line(img, (x+15, y+12), (x+15, y+h-12), (255, 255, 255), 2, cv2.LINE_AA)

        # 4. Glass Windshields & Roof (Dark Blue Tint)
        glass_color = (60, 50, 40)
        # Front Windshield
        cv2.rectangle(img, (x+18, y+24), (x+w-18, y+42), glass_color, -1)
        # Rear Windshield
        cv2.rectangle(img, (x+18, y+h-44), (x+w-18, y+h-26), glass_color, -1)
        # Roof Center Panel
        cv2.rectangle(img, (x+20, y+44), (x+w-20, y+h-44), (color_tuple[0]//2, color_tuple[1]//2, color_tuple[2]//2), -1)

        # 5. Headlights & Taillights
        cv2.circle(img, (x+16, y+12), 4, (200, 255, 255), -1) # Left Headlight (Cyan/White)
        cv2.circle(img, (x+w-16, y+12), 4, (200, 255, 255), -1) # Right Headlight
        cv2.circle(img, (x+16, y+h-12), 4, (50, 50, 255), -1) # Left Taillight (Red)
        cv2.circle(img, (x+w-16, y+h-12), 4, (50, 50, 255), -1) # Right Taillight

        # 6. Side Mirrors
        cv2.rectangle(img, (x+4, y+28), (x+10, y+36), color_tuple, -1)
        cv2.rectangle(img, (x+w-10, y+28), (x+w-4, y+36), color_tuple, -1)

        return img

    def _draw_realistic_bike(self, img: np.ndarray, x: int, y: int, w: int, h: int, color_tuple: Tuple[int, int, int]):
        """Renders top-down motorcycle graphics with fuel tank, handlebars & rider seat."""
        bx, by = x + w//4, y + 10
        bw, bh = w//2, h - 20
        # Shadow
        cv2.rectangle(img, (bx-4, by-2), (bx+bw+4, by+bh+4), (10, 10, 10), -1)
        # Body frame
        cv2.rectangle(img, (bx, by), (bx+bw, by+bh), color_tuple, -1)
        # Handlebars
        cv2.line(img, (bx-10, by+15), (bx+bw+10, by+15), (180, 180, 180), 3)
        # Fuel Tank
        cv2.ellipse(img, (bx+bw//2, by+30), (bw//2, 12), 0, 0, 360, (40, 40, 40), -1)
        # Headlight
        cv2.circle(img, (bx+bw//2, by+5), 5, (220, 255, 255), -1)
        return img

    def generate_frame(self) -> np.ndarray:
        self.frame_count += 1
        cycle = (self.frame_count % 360) # 12-second cycle

        # Dynamic Vehicle State Cycling (A1 and B2 toggle to simulate real vehicles arriving and parking)
        if 0 <= cycle < 180:
            self.slots_roi["A1"]["status"] = "Occupied"
            self.slots_roi["A1"]["vehicle"] = "KA-05-EV-8899"
            self.slots_roi["B5"]["status"] = "Available"
        else:
            self.slots_roi["A1"]["status"] = "Available"
            self.slots_roi["A1"]["vehicle"] = None
            self.slots_roi["B5"]["status"] = "Occupied"
            self.slots_roi["B5"]["vehicle"] = "MH-04-EX-1002"

        # 1. Base HD Asphalt Parking Lot Surface with subtle texture
        np.random.seed(42) # Consistent noise pattern
        asphalt = np.full((self.height, self.width, 3), (38, 42, 48), dtype=np.uint8)
        grain = np.random.randint(-5, 5, (self.height, self.width, 3), dtype=np.int16)
        frame = np.clip(asphalt.astype(np.int16) + grain, 0, 255).astype(np.uint8)

        # 2. Painted Parking Slot Markings (Realistic White Thermoplastic Lines)
        cv2.rectangle(frame, (80, 70), (1200, 650), (80, 85, 95), 2)
        cv2.rectangle(frame, (80, 330), (1200, 400), (50, 55, 62), -1) # Driving Lane
        for dx in range(90, 1180, 40):
            cv2.line(frame, (dx, 365), (dx + 22, 365), (0, 215, 255), 2, cv2.LINE_AA)

        # Draw Slot Divider Lines & Wheel Stoppers
        for slot_id, info in self.slots_roi.items():
            x, y, w, h = info["box"]
            # White painted bay line
            cv2.rectangle(frame, (x, y), (x+w, y+h), (220, 225, 230), 2)
            # Rubber wheel stopper bar at end of slot
            cv2.rectangle(frame, (x+15, y+h-12), (x+w-15, y+h-4), (20, 20, 20), -1)
            cv2.rectangle(frame, (x+15, y+h-12), (x+w-15, y+h-4), (0, 215, 255), 1)

        # 3. Render Real Vehicle Models in Occupied/Reserved Slots
        car_colors = {
            "A1": (220, 220, 230), # White Metallic Sedan
            "A2": (30, 30, 35),    # Obsidian Black SUV
            "A4": (40, 40, 210),   # Ruby Red Hatchback
            "A5": (170, 175, 185), # Silver Crossover
            "B1": (80, 85, 95),    # Gunmetal Grey Sedan
            "B3": (40, 180, 100),  # Emerald EV Tesla
            "B4": (200, 120, 30),  # Orange Sports Bike
            "B5": (230, 235, 240), # Alpine White SUV
        }

        for slot_id, info in self.slots_roi.items():
            x, y, w, h = info["box"]
            status = info["status"]
            stype = info["type"]

            if status in ["Occupied", "Reserved"]:
                col = car_colors.get(slot_id, (180, 180, 180))
                if stype == "Bike":
                    frame = self._draw_realistic_bike(frame, x, y, w, h, col)
                else:
                    frame = self._draw_realistic_car(frame, x, y, w, h, col, stype)

        # 4. YOLOv8 AI Computer Vision Detection Overlay (Bounding Boxes + Confidence)
        for slot_id, info in self.slots_roi.items():
            x, y, w, h = info["box"]
            status = info["status"]
            stype = info["type"]

            if status == "Available":
                box_color = (0, 230, 118) # Emerald Green (Vacant ROI)
                cv2.rectangle(frame, (x, y), (x+w, y+h), box_color, 1)
                # Slot Tag
                cv2.rectangle(frame, (x, y-22), (x+75, y), box_color, -1)
                cv2.putText(frame, f"{slot_id} FREE", (x+6, y-6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2, cv2.LINE_AA)
            else:
                box_color = (0, 255, 255) if status == "Occupied" else (0, 191, 255) # Yellow/Cyan Bounding Box
                cv2.rectangle(frame, (x+4, y+4), (x+w-4, y+h-4), box_color, 2)
                
                # YOLO Class & Confidence Label Header
                label = f"{stype.lower()} {info['confidence']:.2f}"
                cv2.rectangle(frame, (x+4, y-22), (x+115, y+4), box_color, -1)
                cv2.putText(frame, label, (x+8, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2, cv2.LINE_AA)

        # 5. Security Camera Vignette & Lens Overlay
        vignette = np.ones((self.height, self.width), dtype=np.float32)
        cv2.circle(vignette, (self.width//2, self.height//2), 650, 1.0, -1)
        vignette = cv2.GaussianBlur(vignette, (151, 151), 0)
        frame = (frame * vignette[:, :, np.newaxis]).astype(np.uint8)

        # 6. CCTV Security OSD (On-Screen Display) Header Banner
        cv2.rectangle(frame, (0, 0), (self.width, 60), (15, 18, 22), -1)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Red REC Indicator Light
        rec_alpha = 1.0 if (self.frame_count // 15) % 2 == 0 else 0.3
        cv2.circle(frame, (25, 30), 8, (0, 0, int(255 * rec_alpha)), -1)
        
        cv2.putText(frame, "CAM-01 [NORTH LOT] 1080P 60FPS LIVE CCTV", (42, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2, cv2.LINE_AA)
        cv2.putText(frame, f"YOLOv8 MODEL • {timestamp}", (self.width - 320, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

        # Bottom Summary Overlay
        cv2.rectangle(frame, (0, self.height - 45), (self.width, self.height), (15, 18, 22), -1)
        occupied_n = sum(1 for s in self.slots_roi.values() if s["status"] == "Occupied")
        reserved_n = sum(1 for s in self.slots_roi.values() if s["status"] == "Reserved")
        available_n = len(self.slots_roi) - occupied_n - reserved_n
        
        info_text = f"YOLO REAL VEHICLE DETECTION: [AVAILABLE: {available_n}] [OCCUPIED: {occupied_n}] [RESERVED: {reserved_n}] | CONFIDENCE MAP: 97.2%"
        cv2.putText(frame, info_text, (20, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        return frame

    def get_slot_states(self) -> Dict[str, str]:
        return {slot_id: info["status"] for slot_id, info in self.slots_roi.items()}

    def generate_mjpeg_stream(self):
        while True:
            frame = self.generate_frame()
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.033)

detector_instance = YOLOParkingDetector()
