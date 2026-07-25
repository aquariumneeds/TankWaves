# TankWaves Version 7 — Shopping Experience Upgrade

Version 7 keeps the working PostgreSQL and Cloudinary foundation from Version 6 and improves the buyer and seller experience.

## New in Version 7

- Homepage powered by real marketplace listings and real storefronts
- Stronger all-seller search and category browsing
- Price range, state, delivery, category, and sorting filters
- Multi-photo listing gallery with clickable thumbnails
- Similar listings shown on product pages
- Store name, seller rating, location, shipping, and pickup details
- Better watchlist controls
- Seller dashboard totals for favorites and inquiries
- Cleaner mobile layout
- `/version` now returns `7.0`

## Existing services stay connected

Keep the existing Render environment variables:

- `DATABASE_URL`
- `CLOUDINARY_URL`
- `PYTHON_VERSION`
- `SECRET_KEY` if configured

No database reset is performed. Existing users, stores, listings, photos, favorites, reviews, and inquiries remain intact.
