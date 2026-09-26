import os, json, uuid
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

BASE = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    'orders': os.path.join(DATA_DIR, 'orders.json'),
    'crops': os.path.join(DATA_DIR, 'crops.json'),
    'suggestions': os.path.join(DATA_DIR, 'suggestions.json'),
    'notifications': os.path.join(DATA_DIR, 'notifications.json'),
}

DEMO_TRANSPORTERS = [
    {'id':'TR001','name':'Transporter','mobile':'9876543210','vehicle_type':'mini-truck','vehicle_number':'AP 07 AB 1234','capacity':'1.5 Ton'},
    {'id':'TR002','name':'Ravi Transport','mobile':'9876543211','vehicle_type':'pickup','vehicle_number':'AP 07 CD 5678','capacity':'3 Ton'},
    {'id':'TR003','name':'Guntur Agri Logistics','mobile':'9876543212','vehicle_type':'truck','vehicle_number':'AP 07 EF 9012','capacity':'10 Ton'},
]

DEFAULT_CROPS = [
    {'id':'CROP001','farmer':'Farmer','farmer_email':'farmer@agridirect.com','crop':'Tomatoes','variety':'Local Red','quantity':120,'price':32,'unit':'kg','location':'Guntur','harvest_date':'2026-09-28','availability':'high','description':'Fresh farm tomatoes directly from the farmer.','emoji':'🍅','created_at':''},
    {'id':'CROP002','farmer':'Farmer','farmer_email':'farmer@agridirect.com','crop':'Chilli','variety':'Guntur Sannam','quantity':80,'price':145,'unit':'kg','location':'Guntur','harvest_date':'2026-10-02','availability':'medium','description':'Quality Guntur chilli for wholesale and retail buyers.','emoji':'🌶️','created_at':''},
    {'id':'CROP003','farmer':'Farmer','farmer_email':'farmer@agridirect.com','crop':'Rice','variety':'Sona Masuri','quantity':500,'price':48,'unit':'kg','location':'Tenali','harvest_date':'2026-10-05','availability':'high','description':'Clean, locally grown rice.','emoji':'🌾','created_at':''},
]
DEFAULT_SUGGESTIONS = [
    {'id':'SUG001','author':'Farmer','category':'rice','title':'Better paddy water management','text':'Use field channels and avoid standing water after the crop reaches the right stage.','likes':4,'created_at':''},
    {'id':'SUG002','author':'Farmer','category':'vegetables','title':'Simple vegetable grading','text':'Separate damaged produce before packing to improve buyer confidence.','likes':7,'created_at':''},
]


def now_iso(): return datetime.now(timezone.utc).isoformat()

def read_json(key, default):
    path = FILES[key]
    if not os.path.exists(path):
        write_json(key, default)
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data=json.load(f)
            return data if isinstance(data, type(default)) else default
    except Exception:
        return default

def write_json(key, data):
    path=FILES[key]; tmp=path+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False)
    os.replace(tmp,path)

def load_orders(): return read_json('orders', [])
def save_orders(v): write_json('orders', v)
def load_crops():
    data=read_json('crops', DEFAULT_CROPS)
    if not data:
        data=[dict(x, created_at=now_iso()) for x in DEFAULT_CROPS]; write_json('crops',data)
    return data

def save_crops(v): write_json('crops', v)
def load_suggestions():
    data=read_json('suggestions', DEFAULT_SUGGESTIONS)
    if not data:
        data=[dict(x, created_at=now_iso()) for x in DEFAULT_SUGGESTIONS]; write_json('suggestions',data)
    return data

def save_suggestions(v): write_json('suggestions',v)
def current_role(*roles): return session.get('role') in roles

def order_for_user(o):
    role=session.get('role')
    if role=='buyer': return o.get('buyer_email')==session.get('email')
    if role=='farmer': return o.get('farmer_email')==session.get('email') or o.get('farmer')==session.get('name')
    if role=='transporter': return o.get('transporter_id')==session.get('transporter_id')
    return False

def ok(data=None, status=200): return jsonify({'ok':True, **(data or {})}), status

def error(message,status=400): return jsonify({'ok':False,'error':message}), status

@app.route('/set-language/<lang>', methods=['POST'])
def set_language(lang):
    if lang not in {'en','te','hi'}: return error('Unsupported language',400)
    session['language']=lang; return ok({'language':lang})

@app.route('/')
def home(): return render_template('index.html')

@app.route('/farmer-login', methods=['GET','POST'])
def farmer_login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        if email=='farmer@agridirect.com' and password=='farmer123':
            lang=session.get('language','en'); session.clear(); session.update(language=lang,role='farmer',name='Farmer',email=email); return redirect(url_for('farmer_dashboard'))
        flash('Invalid farmer login details.','error')
    return render_template('farmer-login.html')

@app.route('/farmer-dashboard')
def farmer_dashboard():
    if not current_role('farmer'): flash('Please login as a farmer first.','error'); return redirect(url_for('farmer_login'))
    return render_template('farmer-dashboard.html', farmer_name=session.get('name','Farmer'))

@app.route('/pesticides')
def pesticides():
    if not current_role('farmer'): flash('Please login as a farmer to access pesticides.','error'); return redirect(url_for('farmer_login'))
    return render_template('pesticides.html')

@app.route('/buyer-login', methods=['GET','POST'])
def buyer_login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        if email=='buyer@agridirect.com' and password=='buyer123':
            lang=session.get('language','en'); session.clear(); session.update(language=lang,role='buyer',name='Buyer',email=email); return redirect(url_for('buyer_dashboard'))
        flash('Invalid buyer login details.','error')
    return render_template('buyer-login.html')

@app.route('/buyer-dashboard')
def buyer_dashboard():
    if not current_role('buyer'): flash('Please login as a buyer first.','error'); return redirect(url_for('buyer_login'))
    return render_template('buyer-dashboard.html', buyer_name=session.get('name','Buyer'))

@app.route('/transporter_login', methods=['GET','POST'])
def transporter_login():
    if request.method=='POST':
        mobile=request.form.get('mobile','').strip(); password=request.form.get('password','').strip(); vehicle_type=request.form.get('vehicleType','').strip()
        t=next((x for x in DEMO_TRANSPORTERS if x['mobile']==mobile),None)
        if not mobile.isdigit() or len(mobile)!=10: flash('Please enter a valid 10-digit mobile number.','error')
        elif t and password=='transporter123':
            lang=session.get('language','en'); session.clear(); session.update(language=lang,role='transporter',name=t['name'],mobile=t['mobile'],vehicle_type=vehicle_type or t['vehicle_type'],transporter_id=t['id'],vehicle_number=t['vehicle_number'],capacity=t['capacity']); return redirect(url_for('transporter_dashboard'))
        else: flash('Invalid transporter login. Demo: 9876543210 / transporter123','error')
    return render_template('transporter_login.html')

@app.route('/transporter_dashboard')
def transporter_dashboard():
    if not current_role('transporter'): flash('Please login as a transporter first.','error'); return redirect(url_for('transporter_login'))
    return render_template('transporter_dashboard.html', transporter_name=session.get('name','Transporter'),mobile=session.get('mobile',''),vehicle_type=session.get('vehicle_type','Vehicle'),vehicle_number=session.get('vehicle_number',''),capacity=session.get('capacity','Not set'))

# ---------- dashboard APIs ----------
@app.route('/api/dashboard-summary')
def dashboard_summary():
    role=session.get('role')
    if not role: return error('Login required',401)
    orders=[o for o in load_orders() if order_for_user(o)]
    crops=load_crops()
    if role=='farmer': crops=[c for c in crops if c.get('farmer_email')==session.get('email') or c.get('farmer')==session.get('name')]
    elif role=='buyer': crops=[c for c in crops if float(c.get('quantity',0))>0]
    elif role=='transporter': crops=[]
    delivered=[o for o in orders if o.get('status')=='Delivered']
    return ok({'role':role,'orders':len(orders),'crops':len(crops),'active':len([o for o in orders if o.get('status') not in {'Delivered','Cancelled'}]),'delivered':len(delivered),'earnings':round(sum(float(o.get('price',0))*float(o.get('quantity',0)) for o in delivered),2)})

@app.route('/api/crops', methods=['GET','POST'])
def crops_api():
    if not session.get('role'): return error('Login required',401)
    crops=load_crops()
    if request.method=='GET':
        q=request.args.get('q','').strip().lower(); loc=request.args.get('location','').strip().lower(); availability=request.args.get('availability','').strip().lower()
        out=[c for c in crops if (not q or q in str(c.get('crop','')).lower() or q in str(c.get('variety','')).lower() or q in str(c.get('location','')).lower()) and (not loc or str(c.get('location','')).lower()==loc) and (not availability or str(c.get('availability','')).lower()==availability) and (session.get('role')!='farmer' or c.get('farmer_email')==session.get('email') or c.get('farmer')==session.get('name'))]
        return ok({'crops':out})
    if session.get('role')!='farmer': return error('Farmer login required',403)
    d=request.get_json(silent=True) or {}
    required=['crop','quantity','price','location']
    missing=[x for x in required if not str(d.get(x,'')).strip()]
    if missing: return error('Missing: '+', '.join(missing),400)
    try: quantity=float(d['quantity']); price=float(d['price'])
    except: return error('Quantity and price must be numbers',400)
    if quantity<=0 or price<0: return error('Enter valid quantity and price',400)
    item={'id':'CROP-'+uuid.uuid4().hex[:8].upper(),'farmer':session.get('name','Farmer'),'farmer_email':session.get('email',''),'crop':str(d['crop']).strip(),'variety':str(d.get('variety','')).strip(),'quantity':quantity,'price':price,'unit':str(d.get('unit','kg')),'location':str(d['location']).strip(),'harvest_date':str(d.get('harvest_date','')),'availability':str(d.get('availability','high')),'description':str(d.get('description','')).strip(),'emoji':str(d.get('emoji','🌾')),'created_at':now_iso()}
    crops.append(item); save_crops(crops); return ok({'crop':item},201)

@app.route('/api/crops/<crop_id>', methods=['PUT','DELETE'])
def crop_item(crop_id):
    if session.get('role')!='farmer': return error('Farmer login required',403)
    crops=load_crops(); item=next((c for c in crops if c.get('id')==crop_id),None)
    if not item: return error('Crop not found',404)
    if item.get('farmer_email')!=session.get('email'): return error('Not your crop',403)
    if request.method=='DELETE': crops.remove(item); save_crops(crops); return ok({'message':'Crop removed'})
    d=request.get_json(silent=True) or {}
    for k in ['crop','variety','location','harvest_date','availability','description','unit','emoji']:
        if k in d: item[k]=str(d[k])
    for k in ['quantity','price']:
        if k in d:
            try: item[k]=float(d[k])
            except: pass
    save_crops(crops); return ok({'crop':item})

@app.route('/api/suggestions', methods=['GET','POST'])
def suggestions_api():
    if not session.get('role'): return error('Login required',401)
    data=load_suggestions()
    if request.method=='GET': return ok({'suggestions':sorted(data,key=lambda x:x.get('created_at',''),reverse=True)})
    d=request.get_json(silent=True) or {}
    title=str(d.get('title','')).strip(); text=str(d.get('text','')).strip()
    if not title or not text: return error('Title and suggestion are required',400)
    item={'id':'SUG-'+uuid.uuid4().hex[:8].upper(),'author':session.get('name','User'),'category':str(d.get('category','general')),'title':title,'text':text,'likes':0,'created_at':now_iso()}
    data.append(item); save_suggestions(data); return ok({'suggestion':item},201)

@app.route('/api/suggestions/<suggestion_id>/like', methods=['POST'])
def like_suggestion(suggestion_id):
    data=load_suggestions(); item=next((x for x in data if x.get('id')==suggestion_id),None)
    if not item: return error('Suggestion not found',404)
    item['likes']=int(item.get('likes',0))+1; save_suggestions(data); return ok({'suggestion':item})

@app.route('/api/notifications')
def notifications():
    if not session.get('role'): return error('Login required',401)
    orders=[o for o in load_orders() if order_for_user(o)]
    items=[{'id':o['id'],'title':f"Order {o['id']} — {o.get('status','Requested')}",'text':o.get('last_event','Order updated'),'time':o.get('updated_at') or o.get('created_at')} for o in orders[:10]]
    return ok({'notifications':items})

@app.route('/api/profile', methods=['GET','PUT'])
def profile():
    if not session.get('role'): return error('Login required',401)
    if request.method=='GET': return ok({'profile':{'name':session.get('name',''),'email':session.get('email',''),'mobile':session.get('mobile',''),'role':session.get('role',''),'vehicle_type':session.get('vehicle_type',''),'vehicle_number':session.get('vehicle_number',''),'capacity':session.get('capacity','')}})
    d=request.get_json(silent=True) or {}
    if str(d.get('name','')).strip(): session['name']=str(d['name']).strip()
    if session.get('role')=='transporter':
        for k in ('mobile','vehicle_type','vehicle_number','capacity'):
            if k in d: session[k]=str(d[k]).strip()
    return ok({'profile':{'name':session.get('name',''),'email':session.get('email',''),'mobile':session.get('mobile',''),'role':session.get('role',''),'vehicle_type':session.get('vehicle_type',''),'vehicle_number':session.get('vehicle_number',''),'capacity':session.get('capacity','')}})

# ---------- order/tracking APIs ----------
@app.route('/api/transporters')
def api_transporters(): return ok({'transporters':DEMO_TRANSPORTERS})

@app.route('/api/orders', methods=['GET','POST'])
def orders_api():
    if not session.get('role'): return error('Login required',401)
    if request.method=='GET':
        orders=[o for o in load_orders() if order_for_user(o)]; orders.sort(key=lambda x:x.get('created_at',''),reverse=True); return ok({'orders':orders})
    if session.get('role')!='buyer': return error('Buyer login required',403)
    d=request.get_json(silent=True) or {}
    for k in ['crop','quantity','price','farmer']:
        if not str(d.get(k,'')).strip(): return error('Missing: '+k,400)
    try: quantity=float(d['quantity']); price=float(d['price'])
    except: return error('Quantity and price must be numbers',400)
    crops=load_crops(); crop=next((c for c in crops if c.get('id')==d.get('crop_id')),None)
    if crop and quantity>float(crop.get('quantity',0)): return error('Requested quantity is greater than available crop quantity',400)
    transporter_id=d.get('transporter_id') or 'TR001'; t=next((x for x in DEMO_TRANSPORTERS if x['id']==transporter_id),DEMO_TRANSPORTERS[0])
    order_id='AG-'+uuid.uuid4().hex[:8].upper()
    order={'id':order_id,'crop':str(d['crop']),'variety':str(d.get('variety','')),'quantity':quantity,'price':price,'farmer':str(d['farmer']),'farmer_email':str(d.get('farmer_email','')),'pickup':str(d.get('pickup') or d.get('location') or 'Guntur'),'delivery':str(d.get('delivery') or 'Buyer Location'),'buyer_name':session.get('name','Buyer'),'buyer_email':session.get('email',''),'transporter_id':t['id'],'transporter_name':t['name'],'transporter_mobile':t['mobile'],'vehicle_type':t['vehicle_type'],'vehicle_number':t['vehicle_number'],'status':'Requested','created_at':now_iso(),'updated_at':now_iso(),'location':{'lat':None,'lng':None,'accuracy':None,'timestamp':None},'eta_minutes':None,'last_event':'Order created. Waiting for transporter acceptance.'}
    orders=load_orders(); orders.append(order); save_orders(orders)
    if crop:
        crop['quantity']=max(0,float(crop.get('quantity',0))-quantity)
        if crop['quantity']<=0: crop['availability']='low'
        save_crops(crops)
    return ok({'order':order},201)

@app.route('/api/orders/<order_id>')
def get_order(order_id):
    if not session.get('role'): return error('Login required',401)
    order=next((o for o in load_orders() if o.get('id')==order_id and order_for_user(o)),None)
    if not order: return error('Order not found',404)
    return ok({'order':order})

@app.route('/api/orders/<order_id>/status', methods=['POST'])
def update_order_status(order_id):
    if session.get('role')!='transporter': return error('Transporter login required',403)
    d=request.get_json(silent=True) or {}; status=str(d.get('status','')).strip(); allowed={'Accepted','Picked Up','In Transit','Delivered','Cancelled'}
    if status not in allowed: return error('Invalid status',400)
    orders=load_orders()
    for o in orders:
        if o.get('id')==order_id:
            if o.get('transporter_id')!=session.get('transporter_id'): return error('Not your order',403)
            o['status']=status; o['updated_at']=now_iso(); o['last_event']={'Accepted':'Transporter accepted the order.','Picked Up':'Crop has been picked up from the farmer.','In Transit':'Vehicle is now moving to the delivery location.','Delivered':'Order delivered successfully.','Cancelled':'Transporter cancelled the order.'}[status]; save_orders(orders); return ok({'order':o})
    return error('Order not found',404)

@app.route('/api/orders/<order_id>/location', methods=['POST'])
def update_location(order_id):
    if session.get('role')!='transporter': return error('Transporter login required',403)
    d=request.get_json(silent=True) or {}
    try: lat=float(d['lat']); lng=float(d['lng']); accuracy=float(d.get('accuracy',0))
    except: return error('Invalid GPS coordinates',400)
    if not (-90<=lat<=90 and -180<=lng<=180): return error('GPS coordinates out of range',400)
    orders=load_orders()
    for o in orders:
        if o.get('id')==order_id:
            if o.get('transporter_id')!=session.get('transporter_id'): return error('Not your order',403)
            o['location']={'lat':lat,'lng':lng,'accuracy':accuracy,'timestamp':now_iso()}; o['updated_at']=now_iso()
            if o.get('status') in {'Accepted','Picked Up'}: o['status']='In Transit'; o['last_event']='Live GPS tracking started.'
            save_orders(orders); return ok({'location':o['location'],'order':o})
    return error('Order not found',404)

@app.route('/order-tracking/<order_id>')
def order_tracking(order_id):
    if not session.get('role'): flash('Please login to track an order.','error'); return redirect(url_for('home'))
    order=next((o for o in load_orders() if o.get('id')==order_id),None)
    if not order: flash('Order not found.','error'); return redirect(url_for('tracking_back'))
    if not order_for_user(order): return '<h3>Unauthorized</h3><p>You are not allowed to track this order.</p>',403
    return render_template('order_tracking.html',order=order,order_id=order_id)

@app.route('/track-order/<order_id>')
def track_order(order_id): return redirect(url_for('order_tracking',order_id=order_id))

@app.route('/api/order/<order_id>/location')
def legacy_order_location(order_id):
    if not session.get('role'): return jsonify(success=False,message='Login required'),401
    o=next((x for x in load_orders() if x.get('id')==order_id),None)
    if not o: return jsonify(success=False,message='Order not found'),404
    if not order_for_user(o): return jsonify(success=False,message='Unauthorized'),403
    loc=o.get('location') or {}
    return jsonify(success=True,order_id=o['id'],status=o.get('status','Requested'),crop=o.get('crop',''),quantity=o.get('quantity',0),driver={'name':o.get('transporter_name','Transporter'),'lat':loc.get('lat'),'lng':loc.get('lng')},farmer=None,buyer=None,last_update=loc.get('timestamp') or o.get('updated_at'))

@app.route('/api/update-location',methods=['POST'])
def legacy_update_location():
    if session.get('role')!='transporter': return jsonify(success=False,message='Transporter login required'),403
    d=request.get_json(silent=True) or {}; order_id=str(d.get('order_id','')).strip()
    if not order_id: return jsonify(success=False,message='Order ID is required'),400
    try: lat=float(d['lat']); lng=float(d['lng']); accuracy=float(d.get('accuracy',0))
    except: return jsonify(success=False,message='Invalid GPS coordinates'),400
    # use same implementation semantics
    orders=load_orders()
    for o in orders:
        if o.get('id')==order_id:
            if o.get('transporter_id')!=session.get('transporter_id'): return jsonify(success=False,message='Not your order'),403
            o['location']={'lat':lat,'lng':lng,'accuracy':accuracy,'timestamp':now_iso()}; o['updated_at']=now_iso()
            if o.get('status') in {'Accepted','Picked Up'}: o['status']='In Transit'; o['last_event']='Live GPS tracking started.'
            save_orders(orders); return jsonify(success=True,message='GPS location updated successfully.',order_id=order_id,lat=lat,lng=lng,status=o.get('status'),last_update=o['location']['timestamp'])
    return jsonify(success=False,message='Order not found'),404

@app.route('/api/order/<order_id>/status',methods=['POST'])
def legacy_update_status(order_id):
    if session.get('role')!='transporter': return jsonify(success=False,message='Transporter login required'),403
    d=request.get_json(silent=True) or {}; status=str(d.get('status','')).strip(); allowed={'Accepted','Picked Up','In Transit','Delivered','Cancelled'}
    if status not in allowed: return jsonify(success=False,message='Invalid order status'),400
    orders=load_orders()
    for o in orders:
        if o.get('id')==order_id:
            if o.get('transporter_id')!=session.get('transporter_id'): return jsonify(success=False,message='Not your order'),403
            o['status']=status; o['updated_at']=now_iso(); o['last_event']=status; save_orders(orders); return jsonify(success=True,order_id=order_id,status=status)
    return jsonify(success=False,message='Order not found'),404

@app.route('/tracking-back')
def tracking_back():
    return redirect(url_for({'farmer':'farmer_dashboard','buyer':'buyer_dashboard','transporter':'transporter_dashboard'}.get(session.get('role'),'home')))

@app.route('/logout')
def logout(): session.clear(); flash('You have been logged out successfully.','success'); return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(error): return '<h1>404 - Page Not Found</h1><p>The requested page does not exist.</p><a href="/">Go back to AgriDirect</a>',404

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=os.environ.get('FLASK_DEBUG')=='1')
