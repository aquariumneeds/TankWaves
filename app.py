from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///marketplace.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    species = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    location = db.Column(db.String(120), nullable=False)
    shipping = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(500))
    description = db.Column(db.Text, nullable=False)
    seller_name = db.Column(db.String(120), nullable=False)
    seller_email = db.Column(db.String(180), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False)
    buyer_name = db.Column(db.String(120), nullable=False)
    buyer_email = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    listing = db.relationship("Listing", backref="inquiries")

@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = Listing.query.order_by(Listing.created_at.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Listing.title.ilike(like), Listing.species.ilike(like), Listing.description.ilike(like)))
    if category:
        query = query.filter_by(category=category)
    return render_template("index.html", listings=query.all(), q=q, category=category)

@app.route("/listing/<int:listing_id>", methods=["GET", "POST"])
def listing_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if request.method == "POST":
        name = request.form.get("buyer_name", "").strip()
        email = request.form.get("buyer_email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please complete every field.", "error")
        else:
            db.session.add(Inquiry(listing_id=listing.id, buyer_name=name, buyer_email=email, message=message))
            db.session.commit()
            flash("Inquiry sent.", "success")
            return redirect(url_for("listing_detail", listing_id=listing.id))
    return render_template("listing.html", listing=listing)

@app.route("/sell", methods=["GET", "POST"])
def sell():
    if request.method == "POST":
        try:
            listing = Listing(
                title=request.form["title"].strip(),
                species=request.form["species"].strip(),
                category=request.form["category"].strip(),
                price=float(request.form["price"]),
                quantity=int(request.form["quantity"]),
                location=request.form["location"].strip(),
                shipping=request.form["shipping"].strip(),
                image_url=request.form.get("image_url", "").strip(),
                description=request.form["description"].strip(),
                seller_name=request.form["seller_name"].strip(),
                seller_email=request.form["seller_email"].strip(),
            )
            if listing.price <= 0 or listing.quantity <= 0:
                raise ValueError
            db.session.add(listing)
            db.session.commit()
            flash("Listing published.", "success")
            return redirect(url_for("listing_detail", listing_id=listing.id))
        except Exception:
            db.session.rollback()
            flash("Please check every field.", "error")
    return render_template("sell.html")

@app.route("/admin/inquiries")
def admin_inquiries():
    if request.args.get("token") != os.environ.get("ADMIN_TOKEN", "demo-admin"):
        return "Unauthorized", 401
    return render_template("admin.html", inquiries=Inquiry.query.order_by(Inquiry.created_at.desc()).all())

@app.cli.command("seed")
def seed():
    if Listing.query.count() == 0:
        db.session.add_all([
            Listing(title="Blue Dream Shrimp Colony", species="Neocaridina davidi", category="Shrimp", price=39.99, quantity=10, location="Raleigh, NC", shipping="Overnight available", image_url="", description="Healthy home-bred shrimp, mixed juveniles and young adults.", seller_name="Triangle Aquatics", seller_email="seller@example.com"),
            Listing(title="Lemon Oscar Juvenile", species="Astronotus ocellatus", category="Freshwater Fish", price=29.99, quantity=4, location="Durham, NC", shipping="Local pickup", image_url="", description="Active juvenile Oscars eating pellets and frozen foods.", seller_name="Bull City Fish", seller_email="seller2@example.com"),
        ])
        db.session.commit()
        print("Sample listings added.")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
