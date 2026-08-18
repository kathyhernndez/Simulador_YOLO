import cv2
import time
from src.local_yolo import LocalYOLOModel
from src.mock_detector import MockTrafficScenarioGenerator

def run():
    print("Testing YOLO Model...")
    model = LocalYOLOModel('best.pt')
    print('Model loaded:', model.is_loaded)
    print('Classes:', model.classes)

    img = MockTrafficScenarioGenerator.generate_synthetic_road_image('normal')

    if img is not None:
        print('Testing inference on frame of size', img.shape)
        # Primer run (calentamiento)
        dets, lat, _ = model.infer(img, conf=0.1)
        print('Warmup Latency:', lat, 'ms')
        
        # Segundo run
        dets, lat, _ = model.infer(img, conf=0.1)
        print('Real Latency:', lat, 'ms')
        print('Detections:', len(dets))
        for d in dets:
            print(d)
    else:
        print('No image found to test.')

if __name__ == "__main__":
    run()