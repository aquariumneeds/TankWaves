# TankWaves Version 4 — Branding Update

This upgrade adds:

- PostgreSQL support for permanent user, store, and listing data
- Cloudinary support for permanent photos
- Business storefront logos and banners
- Website, Facebook, Instagram, phone, and business hours
- Listing editing
- Active, paused, and sold listing statuses
- Seller dashboard statistics
- Improved marketplace and mobile design

## Important setup

### 1. Render PostgreSQL
The included `render.yaml` can create a PostgreSQL database when deploying as a Blueprint.

For an existing Render web service, create a PostgreSQL database in Render and add its Internal Database URL as:

`DATABASE_URL`

### 2. Cloudinary
Create a free Cloudinary account. In the Cloudinary dashboard, copy the API Environment Variable beginning with:

`cloudinary://`

Add it to Render as:

`CLOUDINARY_URL`

### 3. Render commands

Build command:

`pip install -r requirements.txt`

Start command:

`gunicorn app:app`

## Warning about upgrading an existing SQLite deployment

Your old SQLite account and store data do not automatically move into PostgreSQL. Keep the old deployment available until the new database is configured and tested.
