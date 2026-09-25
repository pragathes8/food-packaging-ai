from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

r = client.get("/health")
assert r.status_code == 200, r.text

r = client.get("/metadata")
assert r.status_code == 200, r.text
meta = r.json()
assert meta["foods"] == 109
assert meta["packaging_materials"] == 40
assert meta["candidate_pairs"] == 4360

r = client.get("/foods")
assert r.status_code == 200, r.text
assert r.json()["count"] == 109

r = client.get("/packaging")
assert r.status_code == 200, r.text
assert r.json()["count"] == 40

r = client.post("/recommend", json={
    "food_name": "Tomato",
    "top_n": 3,
    "storage_type": "Refrigerated",
    "shelf_life_days": 10,
    "humidity": "High",
    "transport": "Cold chain",
    "map_required": False,
})
assert r.status_code == 200, r.text
result = r.json()
assert result.get("status") == "Recommendations_Available", result
assert len(result.get("recommendations", [])) == 3, result

r = client.post("/recommend", json={"food_name": "__UNKNOWN_FOOD__", "top_n": 3})
assert r.status_code == 404, r.text

r = client.post("/recommend", json={"food_name": "Tomato", "top_n": 0})
assert r.status_code == 422, r.text

print("API TESTS PASSED")
print("Tomato top recommendation:", result["recommendations"][0])
