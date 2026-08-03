from datetime import datetime, timedelta

def test_create_shorturl(client, auth_header):
    payload = {
        "original_url": "https://www.google.com",
        "expires_at": (datetime.now() + timedelta(days=5)).isoformat()
    }

    response = client.post("/urls/shorten", json=payload, headers=auth_header)

    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://www.google.com/"
    assert "short_code" in data
    assert "user_id" in data


def test_get_all_urls(client, auth_header):
    # Creating url
    client.post("/urls/shorten", json={"original_url": "https://www.github.com"}, headers=auth_header)

    # Fetch all URLs
    response = client.get("/urls/me", headers=auth_header)

    assert response.status_code == 200
    data = response.json()
    assert type(data) == list
    assert len(data) >= 1
    assert data[0]["original_url"] == "https://www.github.com/"


def test_redirect_and_get_stats(client, auth_header):
    # Create a URL
    setup_res = client.post("/urls/shorten", json={"original_url": "https://www.python.org"}, headers=auth_header)
    short_code = setup_res.json()["short_code"]

    # Visit the short link (follow_redirects=False so we can check the 307 status)
    redirect_res = client.get(f"/urls/{short_code}", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == "https://www.python.org/"

    # Check the stats (assuming this is the first URL created, its ID is 1)
    stats_res = client.get("/urls/1/stats", headers=auth_header)
    assert stats_res.status_code == 200

    # Stats should show at least 1 click from our visit above
    stats_data = stats_res.json()
    assert len(stats_data) >= 1


def test_delete_url(client, auth_header):
    # Create a URL
    client.post("/urls/shorten", json={"original_url": "https://www.python.org"}, headers=auth_header)

    # Delete it (Assuming ID 1)
    delete_res = client.delete("/urls/1", headers=auth_header)
    assert delete_res.status_code == 204

    # Verify we can't find its stats anymore
    stats_res = client.get("/urls/1/stats", headers=auth_header)
    assert stats_res.status_code == 404


def test_redirect_expired_url(client, auth_header):
    # Create a URL that expired yesterday
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    setup_res = client.post(
        "/urls/shorten",
        json={"original_url": "https://www.example.com", "expires_at": yesterday},
        headers=auth_header
    )
    short_code = setup_res.json()["short_code"]

    # Try to visit it
    response = client.get(f"/urls/{short_code}", follow_redirects=False)

    # Assert it returns 410 GONE
    assert response.status_code == 410
    assert response.json()["detail"] == "This short link has expired"
