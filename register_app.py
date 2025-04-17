from mastodon import Mastodon

# Your Mastodon instance, e.g. 'https://mastodon.social'
MASTODON_API_BASE_URL = "mastodon.social"

# Your bot's login credentials
USERNAME = ""
PASSWORD = ""

# Step 1: Register the app (will generate clientcred.secret)
Mastodon.create_app("daily-lotus", api_base_url=MASTODON_API_BASE_URL, to_file="clientcred.secret")

# Step 2: Log in and get access token
mastodon = Mastodon(client_id="clientcred.secret", api_base_url=MASTODON_API_BASE_URL)

mastodon.log_in(USERNAME, PASSWORD, to_file="usercred.secret")

# Step 3: Print the access token (you'll paste this into .env)
with open("usercred.secret") as f:
    access_token = f.read().strip()
    print(f"✅ Your access token:\n{access_token}")
