# TankWaves Version 6 — All-Seller Marketplace Search

Version 6 makes the public shopping experience work more like eBay:

- One search combines matching listings from every seller
- Prominent customer-facing marketplace homepage
- Left-sidebar filters for category, state, delivery, and sorting
- List-style comparison results with price, seller, rating, location, and delivery badges
- Species pages showing all sellers offering the same fish or item
- Watchlist support
- Seller storefronts remain separate, but marketplace search is not limited to one store
- Visible “Version 6” marker and `/version` endpoint for deployment verification
- Login accepts either the registered email or account name
- No destructive database reset or table deletion

## Verify the deployment

After Render deploys, visit:

```text
https://tankwaves.com/version
```

It should display:

```json
{"name":"TankWaves","version":"6.0"}
```

The public homepage should say:

```text
Search once. Compare every seller.
```

## Existing Render service

Keep your current web service, database, domain, and environment variables.

Build:

```text
pip install -r requirements.txt
```

Start:

```text
gunicorn app:app
```

Required environment variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `CLOUDINARY_URL`

Optional:

- `ADMIN_EMAILS`
