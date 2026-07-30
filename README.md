# TankWaves Version 7 — Shopping & Seller Tools

Built directly from the user's working Version 6 package.

## Version 7 additions

- Price-range filtering
- Seller/store-name filtering
- Aquarium seller directory
- Clickable multi-photo gallery
- Sellers can remove individual listing photos
- Similar listings from other sellers
- Listing view counts
- Watcher/favorite counts
- Inquiry counts
- Seller dashboard analytics per listing
- Store watchlist button
- Improved mobile layouts
- `/version` now reports `7.0`

## Preserved from the working Version 6

- Existing PostgreSQL database and user accounts
- Existing stores and listings
- Cloudinary configuration and image upload code
- All-seller marketplace search
- Reviews, inquiries, favorites, and admin controls
- Render deployment configuration

## Deployment check

After committing the extracted files to GitHub and waiting for Render to show Live, visit:

`https://tankwaves.com/version`

Expected result:

`{"name":"TankWaves","version":"7.0"}`

This update uses `db.create_all()` only to add new tables. It does not delete or reset existing data.
