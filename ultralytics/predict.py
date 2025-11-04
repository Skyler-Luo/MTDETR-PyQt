from ultralytics import MTDETR


model = MTDETR("../best.pt")

model.predict(source='./dataset', imgsz=(640,640), device='cpu', mask_threshold=[0.45,0.9], show_labels=True, save=True, project="runs", name="predict")

# Run inference with the RT-DETR-l model on the 'bus.jpg' image
# results = model("path/to/bus.jpg")