import os
from io import BytesIO
from typing import Any

import requests
from dotenv import load_dotenv
from mastodon import Mastodon

load_dotenv()


def get_client() -> Mastodon:
    return Mastodon(
        access_token=os.getenv("MASTODON_ACCESS_TOKEN"),
        api_base_url=os.getenv("MASTODON_API_BASE_URL"),
    )


def post_to_mastodon(
    message: str,
    image_url: str | None = None,
    taxon_image_url: str | None = None,
    in_reply_to_id: str | None = None,
    image_alt_text: str | None = None,  # Add alt-text parameter
    taxon_image_alt_text: str | None = None,  # Add alt-text for taxon image
) -> Any:
    client = get_client()
    media_ids = []

    def upload_image_from_url(url: str, alt_text: str | None) -> Any:
        headers = {"User-Agent": "DailyLotusBot/0.1 (https://earthmetabolome.org/; contact@earthmetabolome.org)"}

        response = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        response.raise_for_status()

        if url.endswith(".svg") or response.headers.get("Content-Type") == "image/svg+xml":
            from cairosvg import svg2png

            png = BytesIO()
            svg2png(bytestring=response.content, write_to=png)
            png.seek(0)
            return client.media_post(png, mime_type="image/png", description=alt_text)  # Add alt-text here
        else:
            img = BytesIO(response.content)
            mime_type = response.headers.get("Content-Type", "image/jpeg")  # fallback
            return client.media_post(img, mime_type=mime_type, description=alt_text)  # Add alt-text here

    if image_url:
        media_ids.append(upload_image_from_url(image_url, alt_text=image_alt_text))

    if taxon_image_url:
        media_ids.append(upload_image_from_url(taxon_image_url, alt_text=taxon_image_alt_text))

    return client.status_post(
        message,
        media_ids=media_ids if media_ids else None,
        in_reply_to_id=in_reply_to_id,
    )
