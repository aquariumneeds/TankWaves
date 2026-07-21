import os, uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE=Path(__file__).resolve().parent
UPLOAD=BASE/'static'/'uploads'; UPLOAD.mkdir(parents=True,exist_ok=True)
app=Flask(__name__)
app.config['SECRET_KEY']=os.environ.get('SECRET_KEY','change-me')
url=os.environ.get('DATABASE_URL','sqlite:///aquamarket.db')
if url.startswith('postgres://'): url=url.replace('postgres://','postgresql://',1)
app.config['SQLALCHEMY_DATABASE_URI']=url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['MAX_CONTENT_LENGTH']=20*1024*1024
db=SQLAlchemy(app)
login=LoginManager(app); login.login_view='login'
CATS=['Freshwater Fish','Saltwater Fish','Shrimp','Snails','Plants','Coral','Invertebrates','Equipment','Aquariums']

class User(UserMixin,db.Model):
 id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(180),unique=True,nullable=False); password=db.Column(db.String(255),nullable=False); city=db.Column(db.String(100),nullable=False); state=db.Column(db.String(40),nullable=False); created=db.Column(db.DateTime,default=datetime.utcnow)
 listings=db.relationship('Listing',backref='seller',cascade='all, delete-orphan'); store=db.relationship('Store',backref='owner',uselist=False,cascade='all, delete-orphan')
class Store(db.Model):
 id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(140),unique=True,nullable=False); slug=db.Column(db.String(160),unique=True,nullable=False); description=db.Column(db.Text,default=''); shipping_policy=db.Column(db.Text,default=''); live_arrival_policy=db.Column(db.Text,default=''); logo=db.Column(db.String(255)); banner=db.Column(db.String(255)); verified=db.Column(db.Boolean,default=False); owner_id=db.Column(db.Integer,db.ForeignKey('user.id'),unique=True,nullable=False)
class Listing(db.Model):
 id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(150),nullable=False); category=db.Column(db.String(60),nullable=False); species=db.Column(db.String(150),nullable=False); price=db.Column(db.Float,nullable=False); quantity=db.Column(db.Integer,default=1); city=db.Column(db.String(100)); state=db.Column(db.String(40)); shipping=db.Column(db.Boolean,default=False); pickup=db.Column(db.Boolean,default=True); description=db.Column(db.Text,nullable=False); status=db.Column(db.String(20),default='active'); created=db.Column(db.DateTime,default=datetime.utcnow); seller_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
 photos=db.relationship('Photo',backref='listing',cascade='all, delete-orphan',order_by='Photo.position')
class Photo(db.Model):
 id=db.Column(db.Integer,primary_key=True); filename=db.Column(db.String(255),nullable=False); position=db.Column(db.Integer,default=0); listing_id=db.Column(db.Integer,db.ForeignKey('listing.id'),nullable=False)
@login.user_loader
def load(uid): return db.session.get(User,int(uid))
def save(f):
 if not f or not f.filename or '.' not in f.filename: return None
 ext=secure_filename(f.filename).rsplit('.',1)[1].lower()
 if ext not in {'jpg','jpeg','png','webp'}: return None
 name=f'{uuid.uuid4().hex}.{ext}'; f.save(UPLOAD/name); return name
def slugify(v):
 base='-'.join(''.join(c.lower() if c.isalnum() else '-' for c in v).split('-')) or uuid.uuid4().hex[:8]; slug=base; n=2
 while Store.query.filter_by(slug=slug).first(): slug=f'{base}-{n}'; n+=1
 return slug
@app.route('/')
def home():
 q=request.args.get('q','').strip(); listings=Listing.query.filter_by(status='active').order_by(Listing.created.desc())
 if q: listings=listings.filter(Listing.title.ilike(f'%{q}%'))
 return render_template('index.html',listings=listings.all(),stores=Store.query.limit(6).all())
@app.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  if User.query.filter_by(email=request.form['email'].lower()).first(): flash('Email already exists','error')
  else:
   u=User(name=request.form['name'],email=request.form['email'].lower(),password=generate_password_hash(request.form['password']),city=request.form['city'],state=request.form['state']); db.session.add(u); db.session.commit(); login_user(u); return redirect(url_for('dashboard'))
 return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login_user_page():
 if request.method=='POST':
  u=User.query.filter_by(email=request.form['email'].lower()).first()
  if u and check_password_hash(u.password,request.form['password']): login_user(u); return redirect(url_for('dashboard'))
  flash('Incorrect login','error')
 return render_template('login.html')
app.add_url_rule('/login','login',login_user_page,methods=['GET','POST'])
@app.route('/logout')
def logout(): logout_user(); return redirect(url_for('home'))
@app.route('/dashboard')
@login_required
def dashboard(): return render_template('dashboard.html',listings=Listing.query.filter_by(seller_id=current_user.id).all())
@app.route('/store/create',methods=['GET','POST'])
@login_required
def create_store():
 if current_user.store: return redirect(url_for('storefront',slug=current_user.store.slug))
 if request.method=='POST':
  s=Store(name=request.form['name'],slug=slugify(request.form['name']),description=request.form.get('description',''),shipping_policy=request.form.get('shipping_policy',''),live_arrival_policy=request.form.get('live_arrival_policy',''),logo=save(request.files.get('logo')),banner=save(request.files.get('banner')),owner_id=current_user.id); db.session.add(s); db.session.commit(); return redirect(url_for('storefront',slug=s.slug))
 return render_template('store_form.html')
@app.route('/store/<slug>')
def storefront(slug):
 s=Store.query.filter_by(slug=slug).first_or_404(); return render_template('storefront.html',store=s,listings=Listing.query.filter_by(seller_id=s.owner_id,status='active').all())
@app.route('/sell',methods=['GET','POST'])
@login_required
def sell():
 if request.method=='POST':
  l=Listing(title=request.form['title'],category=request.form['category'],species=request.form['species'],price=float(request.form['price']),quantity=int(request.form['quantity']),city=request.form['city'],state=request.form['state'],shipping=bool(request.form.get('shipping')),pickup=bool(request.form.get('pickup')),description=request.form['description'],seller_id=current_user.id); db.session.add(l); db.session.flush()
  for i,f in enumerate(request.files.getlist('photos')[:10]):
   n=save(f)
   if n: db.session.add(Photo(filename=n,position=i,listing_id=l.id))
  db.session.commit(); return redirect(url_for('listing',lid=l.id))
 return render_template('listing_form.html',cats=CATS)
@app.route('/listing/<int:lid>')
def listing(lid): return render_template('listing.html',listing=Listing.query.get_or_404(lid))
with app.app_context(): db.create_all()
if __name__=='__main__': app.run(debug=True)
