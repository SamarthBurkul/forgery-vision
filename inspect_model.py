from keras.models import load_model
model = load_model("ELA_Training/model_ela.h5")
for i, layer in enumerate(model.layers):
    print(f"{i:3d}  {layer.name:40s}  {layer.__class__.__name__}")
print(f"\nTotal layers: {len(model.layers)}")
# Find last Conv2D
for layer in reversed(model.layers):
    if 'conv' in layer.name.lower():
        print(f"\nLast conv layer: {layer.name}")
        print(f"Output shape: {layer.output_shape}")
        break
