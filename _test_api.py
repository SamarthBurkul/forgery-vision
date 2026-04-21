import requests

def test(img_path, label):
    with open(img_path, 'rb') as f:
        r = requests.post('http://localhost:5000/analyze/full', files={'image': f})
    d = r.json()
    print(f"--- {label} ---")
    print(f"  Verdict       : {d['verdict']}")
    print(f"  ELA prob      : {d['ela_confidence']:.4f}")
    print(f"  Noise score   : {d['noise_score']:.4f}")
    print(f"  Edge score    : {d['edge_score']:.4f}")
    print(f"  Unified score : {d['unified_score']}")
    bbox = d['annotated_image_base64']
    print(f"  BBox drawn    : {bbox is not None}")
    print(f"  ELA b64 len   : {len(d['ela_image_base64'])} chars")
    print()

test('rsc/real.jpg',     'AUTHENTIC (rsc/real.jpg)')
test('rsc/fake.jpg',     'TAMPERED  (rsc/fake.jpg)')
test('rsc/fake_img.jpg', 'TAMPERED  (rsc/fake_img.jpg)')
print("All tests complete.")
