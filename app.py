from __future__ import annotations

import os
import re
from datetime import datetime

import cloudinary
import cloudinary.uploader
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "development-only-secret")

database_url = os.environ.get("DATABASE_URL", "sqlite:///tankwaves.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

cloudinary_url = os.environ.get("CLOUDINARY_URL")
if cloudinary_url:
    cloudinary.config(secure=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."

CATEGORIES = [
    "Freshwater Fish", "Saltwater Fish", "Shrimp", "Snails", "Plants",
    "Coral", "Invertebrates", "Equipment", "Aquariums", "Food & Supplies"
]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    listings = db.relationship("Listing", backref="seller", lazy=True, cascade="all, delete-orphan")
    store = db.relationship("Store", backref="owner", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    logo_url = db.Column(db.String(500))
    banner_url = db.Column(db.String(500))
    description = db.Column(db.Text, default="")
    shipping_policy = db.Column(db.Text, default="")
    live_arrival_policy = db.Column(db.Text, default="")
    website = db.Column(db.String(255), default="")
    facebook = db.Column(db.String(255), default="")
    instagram = db.Column(db.String(255), default="")
    phone = db.Column(db.String(40), default="")
    business_hours = db.Column(db.String(255), default="")
    verified = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)


class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    species = db.Column(db.String(150), nullable=False)
    scientific_name = db.Column(db.String(150), default="")
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(40), nullable=False)
    shipping_available = db.Column(db.Boolean, default=False)
    local_pickup = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="active")
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    photos = db.relationship(
        "Photo", backref="listing", lazy=True, cascade="all, delete-orphan",
        order_by="Photo.position"
    )


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500), nullable=False)
    public_id = db.Column(db.String(255))
    position = db.Column(db.Integer, default=0)
    listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "store"
    slug = cleaned
    number = 2
    while Store.query.filter_by(slug=slug).first():
        slug = f"{cleaned}-{number}"
        number += 1
    return slug


def upload_image(file, folder: str):
    if not file or not file.filename:
        return None
    if not os.environ.get("CLOUDINARY_URL"):
        raise RuntimeError("CLOUDINARY_URL is not configured.")
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="image",
        transformation=[
            {"width": 1800, "height": 1800, "crop": "limit"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )
    return {"url": result["secure_url"], "public_id": result.get("public_id")}


def delete_cloudinary(public_id):
    if public_id and os.environ.get("CLOUDINARY_URL"):
        try:
            cloudinary.uploader.destroy(public_id)
        except Exception:
            pass


@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    state = request.args.get("state", "").strip()

    query = Listing.query.filter_by(status="active").order_by(
        Listing.featured.desc(), Listing.created_at.desc()
    )
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(
            Listing.title.ilike(pattern),
            Listing.species.ilike(pattern),
            Listing.scientific_name.ilike(pattern),
            Listing.description.ilike(pattern),
        ))
    if category:
        query = query.filter_by(category=category)
    if state:
        query = query.filter(Listing.state.ilike(f"%{state}%"))

    stores = Store.query.order_by(Store.featured.desc(), Store.created_at.desc()).limit(8).all()
    return render_template(
        "index.html",
        listings=query.limit(60).all(),
        stores=stores,
        categories=CATEGORIES,
        q=q,
        category=category,
        state=state,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()

        if not all([name, email, password, city, state]):
            flash("Please complete every field.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account already exists with that email.", "error")
        else:
            user = User(name=name, email=email, city=city, state=state)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to TankWaves!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    listings = Listing.query.filter_by(seller_id=current_user.id).order_by(
        Listing.created_at.desc()
    ).all()
    active_count = sum(1 for listing in listings if listing.status == "active")
    sold_count = sum(1 for listing in listings if listing.status == "sold")
    return render_template(
        "dashboard.html",
        listings=listings,
        active_count=active_count,
        sold_count=sold_count,
    )


@app.route("/store/create", methods=["GET", "POST"])
@login_required
def create_store():
    if current_user.store:
        return redirect(url_for("edit_store"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Store name is required.", "error")
        elif Store.query.filter_by(name=name).first():
            flash("That store name is already taken.", "error")
        else:
            try:
                logo = upload_image(request.files.get("logo"), "tankwaves/store-logos")
                banner = upload_image(request.files.get("banner"), "tankwaves/store-banners")
                store = Store(
                    name=name,
                    slug=slugify(name),
                    description=request.form.get("description", "").strip(),
                    shipping_policy=request.form.get("shipping_policy", "").strip(),
                    live_arrival_policy=request.form.get("live_arrival_policy", "").strip(),
                    website=request.form.get("website", "").strip(),
                    facebook=request.form.get("facebook", "").strip(),
                    instagram=request.form.get("instagram", "").strip(),
                    phone=request.form.get("phone", "").strip(),
                    business_hours=request.form.get("business_hours", "").strip(),
                    logo_url=logo["url"] if logo else None,
                    banner_url=banner["url"] if banner else None,
                    owner_id=current_user.id,
                )
                db.session.add(store)
                db.session.commit()
                flash("Your TankWaves store is live.", "success")
                return redirect(url_for("storefront", slug=store.slug))
            except Exception as exc:
                db.session.rollback()
                flash(f"Store could not be created: {exc}", "error")
    return render_template("store_form.html", store=None)


@app.route("/store/edit", methods=["GET", "POST"])
@login_required
def edit_store():
    store = current_user.store
    if not store:
        return redirect(url_for("create_store"))

    if request.method == "POST":
        try:
            store.name = request.form.get("name", "").strip()
            store.description = request.form.get("description", "").strip()
            store.shipping_policy = request.form.get("shipping_policy", "").strip()
            store.live_arrival_policy = request.form.get("live_arrival_policy", "").strip()
            store.website = request.form.get("website", "").strip()
            store.facebook = request.form.get("facebook", "").strip()
            store.instagram = request.form.get("instagram", "").strip()
            store.phone = request.form.get("phone", "").strip()
            store.business_hours = request.form.get("business_hours", "").strip()

            logo = upload_image(request.files.get("logo"), "tankwaves/store-logos")
            banner = upload_image(request.files.get("banner"), "tankwaves/store-banners")
            if logo:
                store.logo_url = logo["url"]
            if banner:
                store.banner_url = banner["url"]

            db.session.commit()
            flash("Store updated.", "success")
            return redirect(url_for("storefront", slug=store.slug))
        except Exception as exc:
            db.session.rollback()
            flash(f"Store could not be updated: {exc}", "error")

    return render_template("store_form.html", store=store)


@app.route("/store/<slug>")
def storefront(slug):
    store = Store.query.filter_by(slug=slug).first_or_404()
    listings = Listing.query.filter_by(
        seller_id=store.owner_id, status="active"
    ).order_by(Listing.created_at.desc()).all()
    return render_template("storefront.html", store=store, listings=listings)


def populate_listing_from_form(listing):
    listing.title = request.form.get("title", "").strip()
    listing.category = request.form.get("category", "").strip()
    listing.species = request.form.get("species", "").strip()
    listing.scientific_name = request.form.get("scientific_name", "").strip()
    listing.price = float(request.form.get("price", 0))
    listing.quantity = int(request.form.get("quantity", 0))
    listing.city = request.form.get("city", "").strip()
    listing.state = request.form.get("state", "").strip()
    listing.shipping_available = bool(request.form.get("shipping_available"))
    listing.local_pickup = bool(request.form.get("local_pickup"))
    listing.description = request.form.get("description", "").strip()

    if not all([
        listing.title, listing.category, listing.species, listing.city,
        listing.state, listing.description
    ]):
        raise ValueError("Please complete all required fields.")
    if listing.price <= 0 or listing.quantity <= 0:
        raise ValueError("Price and quantity must be greater than zero.")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def create_listing():
    if request.method == "POST":
        listing = Listing(seller_id=current_user.id)
        try:
            populate_listing_from_form(listing)
            db.session.add(listing)
            db.session.flush()

            files = [f for f in request.files.getlist("photos") if f and f.filename][:10]
            for position, file in enumerate(files):
                uploaded = upload_image(file, "tankwaves/listings")
                db.session.add(Photo(
                    image_url=uploaded["url"],
                    public_id=uploaded["public_id"],
                    position=position,
                    listing_id=listing.id,
                ))

            db.session.commit()
            flash("Listing published.", "success")
            return redirect(url_for("listing_detail", listing_id=listing.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Listing could not be published: {exc}", "error")

    return render_template("listing_form.html", listing=None, categories=CATEGORIES)


@app.route("/listing/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit_listing(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.seller_id != current_user.id:
        abort(403)

    if request.method == "POST":
        try:
            populate_listing_from_form(listing)
            new_files = [f for f in request.files.getlist("photos") if f and f.filename]
            available_slots = max(0, 10 - len(listing.photos))
            for position, file in enumerate(new_files[:available_slots], start=len(listing.photos)):
                uploaded = upload_image(file, "tankwaves/listings")
                db.session.add(Photo(
                    image_url=uploaded["url"],
                    public_id=uploaded["public_id"],
                    position=position,
                    listing_id=listing.id,
                ))
            db.session.commit()
            flash("Listing updated.", "success")
            return redirect(url_for("listing_detail", listing_id=listing.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Listing could not be updated: {exc}", "error")

    return render_template("listing_form.html", listing=listing, categories=CATEGORIES)


@app.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    return render_template("listing.html", listing=listing)


@app.route("/listing/<int:listing_id>/status", methods=["POST"])
@login_required
def listing_status(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.seller_id != current_user.id:
        abort(403)
    requested_status = request.form.get("status")
    if requested_status not in {"active", "sold", "paused"}:
        abort(400)
    listing.status = requested_status
    db.session.commit()
    flash("Listing status updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/listing/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.seller_id != current_user.id:
        abort(403)
    for photo in listing.photos:
        delete_cloudinary(photo.public_id)
    db.session.delete(listing)
    db.session.commit()
    flash("Listing deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/health")
def health():
    return {"status": "ok", "database": "connected"}


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
